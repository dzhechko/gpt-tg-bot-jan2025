from bot import GPTBot
from loguru import logger
import os
import signal
import sys
from dotenv import load_dotenv
import json

# Загрузка переменных окружения
load_dotenv()

# Включение/выключение режима отладки
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

def initialize_allowed_groups():
    """Инициализация списка разрешенных групп из переменной окружения."""
    try:
        # Проверяем существование файла
        if not os.path.exists('allowed_groups.json'):
            # Получаем список групп из переменной окружения
            allowed_groups = os.getenv('ALLOWED_GROUPS', '').split(',')
            # Фильтруем пустые значения и пробелы
            allowed_groups = [group.strip() for group in allowed_groups if group.strip()]
            
            # Сохраняем список в файл
            with open('allowed_groups.json', 'w') as f:
                json.dump(allowed_groups, f)
            
            if allowed_groups:
                logger.info(f"Список разрешенных групп инициализирован из переменной окружения: {allowed_groups}")
            else:
                logger.info("Создан пустой список разрешенных групп")
    except Exception as e:
        logger.error(f"Ошибка при инициализации списка групп: {e}")

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
        
        # Инициализируем список разрешенных групп
        initialize_allowed_groups()
        
        # Инициализация и запуск бота
        bot = GPTBot()
        logger.info("Бот инициализирован успешно")
        bot.run()
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске бота: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 