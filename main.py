import os
import asyncio
import signal
from dotenv import load_dotenv
from logger import setup_logger
from bot import TelegramBot
import sys

# Загрузка переменных окружения
load_dotenv()

# Инициализация логгера
logger = setup_logger()

async def shutdown(bot=None):
    """Корректное завершение работы бота."""
    logger.info("Начало процедуры завершения работы...")
    
    if bot and bot.application:
        try:
            if bot.application.running:
                await bot.application.stop()
            await bot.application.shutdown()
        except Exception as e:
            logger.error(f"Ошибка при остановке бота: {str(e)}")

    # Отменяем все оставшиеся задачи
    try:
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        if tasks:
            logger.info(f"Отмена {len(tasks)} задач...")
            for task in tasks:
                if not task.done():
                    task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
    except Exception as e:
        logger.error(f"Ошибка при отмене задач: {str(e)}")

    logger.info("Завершение работы...")

def handle_exception(loop, context):
    """Обработка необработанных исключений."""
    msg = context.get("exception", context["message"])
    logger.error(f"Необработанное исключение: {msg}")

async def main():
    """
    Основная функция для запуска бота.
    Инициализирует и запускает бота с настройками из переменных окружения.
    """
    bot = None
    
    try:
        # Получаем токен из переменных окружения
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not token:
            logger.error("Не найден токен бота. Убедитесь, что переменная TELEGRAM_BOT_TOKEN установлена.")
            return

        # Настройка обработки исключений
        loop = asyncio.get_running_loop()
        loop.set_exception_handler(handle_exception)

        # Настройка обработки сигналов
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(
                sig,
                lambda: asyncio.create_task(shutdown(bot))
            )

        # Создаем и запускаем бота
        bot = TelegramBot(token)
        logger.info("Бот успешно инициализирован")
        
        # Запускаем бота и ждем его завершения
        await bot.run()

    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {str(e)}")
        if bot:
            await shutdown(bot)
        return 1
    return 0

if __name__ == '__main__':
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {str(e)}")
        sys.exit(1) 