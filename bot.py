import os
from openai import OpenAI
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from settings import TextModelSettings, ImageModelSettings, VoiceModelSettings
from handlers import handle_message, handle_callback, handle_command
from media_handlers import MediaHandler
from logger import logger, log_api_call, log_error
from typing import Optional, Any

class TelegramBot:
    def __init__(self, token: str):
        """
        Инициализация бота с настройками и OpenAI клиентом.
        
        Args:
            token (str): Токен Telegram бота
        """
        # Создаем приложение с базовыми настройками
        self.application = (
            Application.builder()
            .token(token)
            .concurrent_updates(True)
            .build()
        )
        
        # Инициализация OpenAI клиента
        self.openai_client = OpenAI(
            api_key=os.getenv('OPENAI_API_KEY'),
            base_url=os.getenv('OPENAI_API_BASE', 'https://api.openai.com/v1')
        )
        
        # Загрузка настроек
        self.text_settings = TextModelSettings()
        self.image_settings = ImageModelSettings()
        self.voice_settings = VoiceModelSettings()
        
        # Инициализация обработчика медиа
        self.media_handler = MediaHandler()
        
        # Регистрация обработчиков
        self._setup_handlers()

    def _setup_handlers(self):
        """Настройка обработчиков команд и сообщений."""
        # Команды
        self.application.add_handler(CommandHandler("start", self._start_command))
        self.application.add_handler(CommandHandler("settings", self._settings_command))
        self.application.add_handler(CommandHandler("clear_history", self._clear_history_command))
        
        # Callback-запросы
        self.application.add_handler(CallbackQueryHandler(self._button_callback))
        
        # Медиа-сообщения
        self.application.add_handler(MessageHandler(filters.VOICE, self._handle_voice))
        self.application.add_handler(MessageHandler(filters.PHOTO, self._handle_image))
        
        # Текстовые сообщения (должны обрабатываться последними)
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))

    async def _start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start."""
        if update and update.effective_chat:
            await handle_command(update, context, 'start')

    async def _settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /settings."""
        if update and update.effective_chat:
            await handle_command(update, context, 'settings')

    async def _clear_history_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /clear_history."""
        if update and update.effective_chat:
            await handle_command(update, context, 'clear_history')

    async def _button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик нажатий кнопок."""
        if update and update.callback_query:
            await handle_callback(update, context)

    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений."""
        if not update or not update.effective_chat:
            return
            
        # Проверяем, не является ли это описанием для изображения
        if context.user_data.get('image_processing'):
            await self.media_handler.handle_image_with_text(update, context)
        else:
            await handle_message(update, context)

    async def _handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик голосовых сообщений."""
        if update and update.effective_chat:
            await self.media_handler.handle_voice(update, context)

    async def _handle_image(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик изображений."""
        if update and update.effective_chat:
            await self.media_handler.handle_image(update, context)

    async def stream_gpt_response(self, messages: list, chat_id: int, message_id: int, context: Any) -> None:
        """
        Потоковая обработка ответа от GPT.
        
        Args:
            messages (list): История сообщений
            chat_id (int): ID чата
            message_id (int): ID сообщения для обновления
            context (Any): Контекст бота
        """
        try:
            log_api_call('OpenAI', 'stream_completion', model=self.text_settings.model)
            
            current_response = ""
            last_update_length = 0
            update_interval = 3
            chunks_since_update = 0
            
            stream = self.openai_client.chat.completions.create(
                model=self.text_settings.model,
                messages=messages,
                stream=True,
                temperature=self.text_settings.temperature,
                max_tokens=self.text_settings.max_tokens
            )

            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    current_response += content
                    chunks_since_update += 1

                    if chunks_since_update >= update_interval:
                        try:
                            await context.bot.edit_message_text(
                                chat_id=chat_id,
                                message_id=message_id,
                                text=current_response,
                                parse_mode=ParseMode.MARKDOWN
                            )
                            chunks_since_update = 0
                            last_update_length = len(current_response)
                        except Exception as e:
                            log_error('telegram_update', str(e))

            # Финальное обновление сообщения
            if len(current_response) > last_update_length:
                try:
                    await context.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=message_id,
                        text=current_response,
                        parse_mode=ParseMode.MARKDOWN
                    )
                    
                    # Если включена голосовая озвучка, конвертируем ответ в голос
                    if self.voice_settings.auto_voice_response:
                        await self.media_handler.text_to_voice(
                            current_response,
                            chat_id,
                            context
                        )
                        
                except Exception as e:
                    log_error('telegram_final_update', str(e))

        except Exception as e:
            log_error('stream_gpt', str(e))
            error_message = "Произошла ошибка при генерации ответа. Пожалуйста, попробуйте позже."
            try:
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=error_message
                )
            except:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=error_message
                )

    async def get_initial_response_message(self, chat_id: int, context: Any) -> Optional[int]:
        """
        Отправка начального сообщения.
        
        Args:
            chat_id (int): ID чата
            context (Any): Контекст бота
            
        Returns:
            Optional[int]: ID сообщения или None при ошибке
        """
        try:
            message = await context.bot.send_message(
                chat_id=chat_id,
                text="Генерирую ответ..."
            )
            return message.message_id
        except Exception as e:
            log_error('initial_message', str(e))
            return None

    async def run(self):
        """Запуск бота в режиме polling."""
        try:
            if not self.application.running:
                await self.application.initialize()
                await self.application.start()
                logger.info("Бот запущен и ожидает сообщений...")
                await self.application.run_polling(allowed_updates=Update.ALL_TYPES)
        except Exception as e:
            logger.error(f"Ошибка при запуске бота: {str(e)}")
            if self.application.running:
                await self.application.stop()
            await self.application.shutdown()
            raise 