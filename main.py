from bot import GPTBot
from loguru import logger
import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Включение/выключение режима отладки
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

def main():
    """
    Основная функция для запуска бота.
    Обрабатывает ошибки и обеспечивает логирование.
    """
    try:
        # Инициализация и запуск бота
        bot = GPTBot()
        logger.info("Бот инициализирован успешно")
        bot.run()
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске бота: {e}")
        raise

if __name__ == "__main__":
    main() 