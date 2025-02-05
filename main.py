import os
import asyncio
from dotenv import load_dotenv
from logger import setup_logger
from bot import TelegramBot

# Загрузка переменных окружения
load_dotenv()

# Инициализация логгера
logger = setup_logger()

async def main():
    """
    Основная функция для запуска бота.
    Инициализирует и запускает бота с настройками из переменных окружения.
    """
    # Получаем токен из переменных окружения
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("Не найден токен бота. Убедитесь, что переменная TELEGRAM_BOT_TOKEN установлена.")
        return

    try:
        # Создаем и запускаем бота
        bot = TelegramBot(token)
        logger.info("Бот успешно инициализирован и запущен")
        await bot.application.run_polling()
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {str(e)}")

if __name__ == '__main__':
    asyncio.run(main()) 