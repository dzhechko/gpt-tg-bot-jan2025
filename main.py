from bot import GPTBot
from loguru import logger
import os
import signal
import sys
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Включение/выключение режима отладки
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

def signal_handler(signum, frame):
    """Обработчик сигналов для корректного завершения."""
    logger.info(f"Получен сигнал {signum}, завершаем работу...")
    sys.exit(0)

def main():
    """
    Основная функция для запуска бота.
    Обрабатывает ошибки и обеспечивает логирование.
    """
    try:
        # Регистрируем обработчики сигналов
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Инициализация и запуск бота
        bot = GPTBot()
        logger.info("Бот инициализирован успешно")
        bot.run()
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске бота: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 