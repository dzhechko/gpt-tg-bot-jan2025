import os
import asyncio
import signal
from dotenv import load_dotenv
from logger import setup_logger
from bot import TelegramBot

# Загрузка переменных окружения
load_dotenv()

# Инициализация логгера
logger = setup_logger()

async def shutdown(loop, bot=None):
    """Корректное завершение работы бота."""
    logger.info("Начало процедуры завершения работы...")
    
    if bot and bot.application:
        try:
            if bot.application.running:
                await bot.application.stop()
            await bot.application.shutdown()
        except Exception as e:
            logger.error(f"Ошибка при остановке бота: {str(e)}")

    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    if tasks:
        logger.info(f"Отмена {len(tasks)} задач...")
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    logger.info("Завершение работы...")
    loop.stop()

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
    loop = asyncio.get_running_loop()
    
    try:
        # Получаем токен из переменных окружения
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not token:
            logger.error("Не найден токен бота. Убедитесь, что переменная TELEGRAM_BOT_TOKEN установлена.")
            return

        # Настройка обработки исключений
        loop.set_exception_handler(handle_exception)

        # Настройка обработки сигналов
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(
                sig,
                lambda s=sig: asyncio.create_task(shutdown(loop, bot))
            )

        # Создаем и запускаем бота
        bot = TelegramBot(token)
        logger.info("Бот успешно инициализирован")
        await bot.run()

    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {str(e)}")
    finally:
        if loop.is_running():
            await shutdown(loop, bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {str(e)}")
    finally:
        # Ensure all tasks are properly cleaned up
        pending = asyncio.all_tasks()
        for task in pending:
            task.cancel() 