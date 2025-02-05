from telegram import Update, Bot
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)
from telegram.error import RetryAfter, TimedOut, NetworkError, Conflict, BadRequest
from openai import OpenAI
import os
from loguru import logger
from dotenv import load_dotenv
from handlers import (
    start_command,
    help_command,
    settings_command,
    clear_command,
    handle_text,
    handle_image,
    handle_settings_callback,
    handle_text_model_settings,
    handle_image_model_settings,
    show_current_settings_command,
    handle_image_command,
    handle_custom_model_input,
    handle_base_url_input,
    handle_image_base_url_input,
    handle_settings_import,
    myid_command,
    stats_command,
    broadcast_command,
    logs_command,
    manage_users_command,
    manage_groups_command,
    restart_command,
    maintenance_command,
    check_maintenance_mode
)
from settings import SettingsManager
import asyncio

# Загрузка переменных окружения
load_dotenv()

# Включение/выключение режима отладки
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Инициализация менеджера настроек
settings_manager = SettingsManager()

class GPTBot:
    def __init__(self):
        """Инициализация бота."""
        self.token = os.getenv('TELEGRAM_TOKEN')
        if not self.token:
            raise ValueError("Не указан токен Telegram бота")

        # Инициализация OpenAI клиента
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            raise ValueError("Не указан API ключ OpenAI")
        
        self.openai_client = OpenAI(
            api_key=openai_api_key,
            base_url=os.getenv('OPENAI_API_BASE', "https://api.openai.com/v1")
        )

        # Настройка логирования
        if DEBUG:
            logger.add("debug.log", rotation="500 MB", level="DEBUG")
        else:
            logger.add("production.log", rotation="500 MB", level="INFO")

        # Создаем приложение
        self.application = Application.builder().token(self.token).build()
        
        # Регистрируем обработчики
        self._setup_handlers()
        
        # Регистрируем обработчик ошибок
        self.application.add_error_handler(self._error_handler)

    def _setup_handlers(self):
        """Настройка обработчиков команд и сообщений."""
        # Добавляем обработчики команд
        self.application.add_handler(CommandHandler('start', start_command))
        self.application.add_handler(CommandHandler('help', help_command))
        self.application.add_handler(CommandHandler('settings', settings_command))
        self.application.add_handler(CommandHandler('clear', clear_command))
        self.application.add_handler(CommandHandler('current_settings', show_current_settings_command))
        self.application.add_handler(CommandHandler(['image', 'img'], handle_image_command))
        self.application.add_handler(CommandHandler('myid', myid_command))
        self.application.add_handler(CommandHandler('gpt', handle_text))

        # Добавляем административные команды
        self.application.add_handler(CommandHandler('stats', stats_command))
        self.application.add_handler(CommandHandler('broadcast', broadcast_command))
        self.application.add_handler(CommandHandler('logs', logs_command))
        self.application.add_handler(CommandHandler(['adduser', 'removeuser', 'listusers'], manage_users_command))
        
        # Добавляем новые административные команды
        self.application.add_handler(CommandHandler(['addgroup', 'removegroup', 'listgroups'], manage_groups_command))
        self.application.add_handler(CommandHandler('restart', restart_command))
        self.application.add_handler(CommandHandler('maintenance', maintenance_command))

        # Добавляем обработчики сообщений
        self.application.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE,
                handle_custom_model_input
            ),
            group=0
        )
        self.application.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE,
                handle_base_url_input
            ),
            group=1
        )
        self.application.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE,
                handle_image_base_url_input
            ),
            group=2
        )
        self.application.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                handle_text
            ),
            group=3
        )
        self.application.add_handler(MessageHandler(filters.PHOTO, handle_image))
        
        # Добавляем обработчик для импорта настроек
        self.application.add_handler(
            MessageHandler(
                filters.Document.FileExtension("json") & filters.ChatType.PRIVATE,
                handle_settings_import
            ),
            group=0
        )

        # Добавляем обработчики callback'ов
        self.application.add_handler(CallbackQueryHandler(
            handle_settings_callback,
            pattern='^(text_settings|image_settings|clear_history|export_settings|import_settings|close_settings|back_to_main|confirm_.*|cancel_confirmation)$'
        ))
        self.application.add_handler(CallbackQueryHandler(
            handle_text_model_settings,
            pattern='^(change_text_model|set_text_model_.*|change_temperature|set_temp_.*|change_max_tokens|set_tokens_.*|change_base_url)$'
        ))
        self.application.add_handler(CallbackQueryHandler(
            handle_image_model_settings,
            pattern='^(change_image_model|set_image_model_.*|change_size|set_size_.*|change_quality|set_quality_.*|change_style|set_style_.*|toggle_hdr|change_image_base_url)$'
        ))

    async def _error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик ошибок бота."""
        try:
            if update and update.effective_message:
                chat_id = update.effective_chat.id
                error_text = "Произошла ошибка при обработке запроса. Попробуйте позже или обратитесь к администратору."
                
                if isinstance(context.error, BadRequest):
                    if "entity" in str(context.error) or "entities" in str(context.error):
                        error_text = "Ошибка форматирования сообщения. Пожалуйста, попробуйте еще раз."
                        logger.warning(f"Ошибка форматирования: {context.error}")
                    else:
                        error_text = "Некорректный запрос. Проверьте правильность команды."
                        logger.error(f"Ошибка BadRequest: {context.error}")
                else:
                    logger.error(f"Необработанная ошибка: {context.error}")
                
                try:
                    # Пробуем отправить новое сообщение вместо редактирования
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=error_text
                    )
                except Exception as send_error:
                    logger.error(f"Не удалось отправить сообщение об ошибке: {send_error}")
            else:
                logger.error(f"Ошибка без контекста сообщения: {context.error}")
        except Exception as e:
            logger.error(f"Ошибка в обработчике ошибок: {e}")

    async def stream_chat_completion(self, messages, chat_id, message_id, context):
        """
        Отправка потокового ответа от модели GPT.
        
        Args:
            messages: История сообщений
            chat_id: ID чата
            message_id: ID сообщения для обновления
            context: Контекст бота
        """
        max_retries = 3
        retry_delay = 100  # начальная задержка в секундах
        attempt = 0

        while attempt < max_retries:
            try:
                # Получаем настройки пользователя
                settings = settings_manager.get_user_settings(chat_id)
                text_settings = settings.text_settings

                # Создаем потоковый запрос к API с настройками пользователя
                stream = self.openai_client.chat.completions.create(
                    model=text_settings.model,
                    messages=messages,
                    temperature=text_settings.temperature,
                    max_tokens=text_settings.max_tokens,
                    stream=True
                )

                # Буфер для накопления частей ответа
                response_buffer = ""
                last_update = ""  # Сохраняем последнее отправленное сообщение
                update_counter = 0  # Счетчик для обновлений
                
                # Обрабатываем поток ответов
                for chunk in stream:
                    if chunk.choices[0].delta.content is not None:
                        content = chunk.choices[0].delta.content
                        response_buffer += content
                        update_counter += 1
                        
                        # Обновляем сообщение каждые 5 чанков или если есть новая строка
                        if update_counter >= 5 or '\n' in content:
                            try:
                                # Проверяем, изменилось ли сообщение
                                if response_buffer != last_update:
                                    await self.application.bot.edit_message_text(
                                        chat_id=chat_id,
                                        message_id=message_id,
                                        text=response_buffer
                                    )
                                    last_update = response_buffer
                                update_counter = 0
                            except BadRequest as e:
                                if "Message is not modified" not in str(e):
                                    logger.debug(f"Ошибка при обновлении сообщения: {e}")

                # Отправляем финальное обновление
                if response_buffer and response_buffer != last_update:
                    try:
                        await self.application.bot.edit_message_text(
                            chat_id=chat_id,
                            message_id=message_id,
                            text=response_buffer
                        )
                        
                        # Сохраняем ответ в историю
                        settings.message_history.append({
                            "role": "assistant",
                            "content": response_buffer
                        })
                        settings_manager.save_settings()
                    except BadRequest as e:
                        if "Message is not modified" not in str(e):
                            logger.debug(f"Ошибка при финальном обновлении: {e}")
                
                # Если успешно получили ответ, выходим из цикла
                break

            except Exception as e:
                error_message = str(e)
                if "Flood control exceeded" in error_message:
                    attempt += 1
                    if attempt < max_retries:
                        retry_seconds = retry_delay * attempt
                        logger.warning(f"Превышен лимит запросов. Попытка {attempt} из {max_retries}. "
                                     f"Ожидание {retry_seconds} секунд...")
                        
                        await self.application.bot.edit_message_text(
                            chat_id=chat_id,
                            message_id=message_id,
                            text=f"⏳ Превышен лимит запросов. Повторная попытка через {retry_seconds} секунд..."
                        )
                        
                        await asyncio.sleep(retry_seconds)
                        continue
                    else:
                        logger.error(f"Превышен лимит попыток после {max_retries} попыток")
                        await self.application.bot.edit_message_text(
                            chat_id=chat_id,
                            message_id=message_id,
                            text="❌ Превышен лимит запросов. Пожалуйста, попробуйте позже."
                        )
                else:
                    logger.error(f"Ошибка при получении ответа от OpenAI: {e}")
                    await self.application.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=message_id,
                        text="❌ Произошла ошибка при получении ответа. Пожалуйста, попробуйте позже."
                    )
                break

    async def create_image(self, prompt, **kwargs):
        """
        Создание изображения с помощью DALL-E.
        
        Args:
            prompt: Текстовое описание изображения
            **kwargs: Дополнительные параметры (размер, качество и т.д.)
        
        Returns:
            str: URL сгенерированного изображения
        """
        try:
            response = self.openai_client.images.generate(
                model=kwargs.get('model', 'dall-e-3'),
                prompt=prompt,
                size=kwargs.get('size', '1024x1024'),
                quality=kwargs.get('quality', 'standard'),
                n=1
            )
            return response.data[0].url
        except Exception as e:
            logger.error(f"Ошибка при генерации изображения: {e}")
            raise

    def run(self):
        """Запуск бота."""
        try:
            # Добавляем GPTBot как пользовательское свойство контекста
            self.application.bot_data['gpt_bot'] = self
            
            # Запускаем бота
            logger.info("Бот запущен")
            self.application.run_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True,
                close_loop=False
            )
        except Exception as e:
            logger.error(f"Ошибка при запуске бота: {e}")
            raise 