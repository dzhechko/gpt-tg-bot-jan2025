from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)
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
    handle_image_model_settings
)

# Загрузка переменных окружения
load_dotenv()

# Включение/выключение режима отладки
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

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

    async def stream_chat_completion(self, messages, chat_id, message_id, context):
        """
        Отправка потокового ответа от модели GPT.
        
        Args:
            messages: История сообщений
            chat_id: ID чата
            message_id: ID сообщения для обновления
            context: Контекст бота
        """
        try:
            # Создаем потоковый запрос к API
            stream = self.openai_client.chat.completions.create(
                model=os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo'),
                messages=messages,
                stream=True
            )

            # Буфер для накопления частей ответа
            response_buffer = ""
            
            # Обрабатываем поток ответов
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    response_buffer += chunk.choices[0].delta.content
                    
                    # Обновляем сообщение каждые N символов или при специальных символах
                    if len(response_buffer) >= 50 or '\n' in response_buffer:
                        await context.bot.edit_message_text(
                            chat_id=chat_id,
                            message_id=message_id,
                            text=response_buffer
                        )

            # Отправляем оставшуюся часть ответа
            if response_buffer:
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=response_buffer
                )

        except Exception as e:
            logger.error(f"Ошибка при получении ответа от OpenAI: {e}")
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text="Произошла ошибка при получении ответа. Пожалуйста, попробуйте позже."
            )

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
            # Создаем приложение
            application = Application.builder().token(self.token).build()

            # Добавляем обработчики команд
            application.add_handler(CommandHandler('start', start_command))
            application.add_handler(CommandHandler('help', help_command))
            application.add_handler(CommandHandler('settings', settings_command))
            application.add_handler(CommandHandler('clear', clear_command))

            # Добавляем обработчики сообщений
            application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
            application.add_handler(MessageHandler(filters.PHOTO, handle_image))

            # Добавляем обработчики callback'ов
            application.add_handler(CallbackQueryHandler(
                handle_settings_callback,
                pattern='^(text_settings|image_settings|clear_history|export_settings|import_settings|close_settings|back_to_main|confirm_.*|cancel_confirmation)$'
            ))
            application.add_handler(CallbackQueryHandler(
                handle_text_model_settings,
                pattern='^(change_text_model|set_text_model_.*)$'
            ))
            application.add_handler(CallbackQueryHandler(
                handle_image_model_settings,
                pattern='^(change_image_model|set_image_model_.*|change_size|set_size_.*|toggle_hdr)$'
            ))

            # Запускаем бота
            logger.info("Бот запущен")
            application.run_polling()
        except Exception as e:
            logger.error(f"Ошибка при запуске бота: {e}") 