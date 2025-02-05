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

# Глобальная переменная для хранения экземпляра бота
bot = None

async def shutdown(signal, loop):
    """Корректное завершение работы бота."""
    logger.info(f"Получен сигнал {signal.name}...")
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]

    for task in tasks:
        task.cancel()

    logger.info(f"Отмена {len(tasks)} задач...")
    await asyncio.gather(*tasks, return_exceptions=True)
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
    global bot
    
    # Получаем токен из переменных окружения
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("Не найден токен бота. Убедитесь, что переменная TELEGRAM_BOT_TOKEN установлена.")
        return

    try:
        # Настройка обработки сигналов
        loop = asyncio.get_running_loop()
        loop.set_exception_handler(handle_exception)
        signals = (signal.SIGTERM, signal.SIGINT)
        for s in signals:
            loop.add_signal_handler(
                s, lambda s=s: asyncio.create_task(shutdown(s, loop))
            )

        # Создаем и запускаем бота
        bot = TelegramBot(token)
        logger.info("Бот успешно инициализирован")
        
        # Запускаем бота и ждем завершения
        await bot.run()
        
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {str(e)}")
        if bot and bot.application:
            try:
                await bot.application.stop()
                await bot.application.shutdown()
            except Exception as shutdown_error:
                logger.error(f"Ошибка при остановке бота: {str(shutdown_error)}")

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