import logging
import os
from pythonjsonlogger import jsonlogger
from datetime import datetime

# Глобальная переменная для управления режимом отладки
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

def setup_logger():
    """Настройка логгера с поддержкой JSON формата и различных уровней логирования."""
    logger = logging.getLogger('TelegramBot')
    
    # Если логгер уже настроен, возвращаем его
    if logger.handlers:
        return logger
    
    # Установка уровня логирования
    logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)
    
    # Создание директории для логов, если её нет
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Форматтер для JSON логов
    class CustomJsonFormatter(jsonlogger.JsonFormatter):
        def add_fields(self, log_record, record, message_dict):
            super().add_fields(log_record, record, message_dict)
            if not log_record.get('timestamp'):
                log_record['timestamp'] = datetime.now().isoformat()
            if log_record.get('level'):
                log_record['level'] = log_record['level'].upper()
            else:
                log_record['level'] = record.levelname
            
            # Переименовываем поле message в log_message если оно есть в extra
            if 'message' in message_dict:
                log_record['log_message'] = message_dict['message']
                del log_record['message']
    
    # Создание форматтеров
    json_formatter = CustomJsonFormatter(
        '%(timestamp)s %(name)s %(level)s %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Обработчик для файла с JSON логами
    json_handler = logging.FileHandler(
        os.path.join(log_dir, f'bot_{datetime.now().strftime("%Y%m%d")}.json')
    )
    json_handler.setFormatter(json_formatter)
    json_handler.setLevel(logging.DEBUG if DEBUG else logging.INFO)
    
    # Обработчик для консоли
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.DEBUG if DEBUG else logging.INFO)
    
    # Добавляем обработчики к логгеру
    logger.addHandler(json_handler)
    logger.addHandler(console_handler)
    
    return logger

# Создание экземпляра логгера
logger = setup_logger()

def log_message(level, message, **kwargs):
    """
    Универсальная функция логирования с поддержкой дополнительных полей.
    
    Args:
        level (str): Уровень логирования ('debug', 'info', 'warning', 'error', 'critical')
        message (str): Основное сообщение для логирования
        **kwargs: Дополнительные поля для логирования
    """
    log_data = {
        'log_message': message,
        'timestamp': datetime.now().isoformat(),
        **{k: v for k, v in kwargs.items() if k != 'message'}
    }
    
    level_methods = {
        'debug': logger.debug,
        'info': logger.info,
        'warning': logger.warning,
        'error': logger.error,
        'critical': logger.critical
    }
    
    log_method = level_methods.get(level.lower(), logger.info)
    log_method(message, extra=log_data)

# Вспомогательные функции для различных типов логов
def log_user_action(user_id, action, **kwargs):
    """Логирование действий пользователя."""
    log_message('info', f'User {user_id}: {action}', user_id=user_id, action_type='user_action', **kwargs)

def log_bot_response(user_id, response_type, **kwargs):
    """Логирование ответов бота."""
    log_message('info', f'Bot response to {user_id}', user_id=user_id, response_type=response_type, **kwargs)

def log_error(error_type, error_message, **kwargs):
    """Логирование ошибок."""
    log_message('error', f'Error: {error_type} - {error_message}', error_type=error_type, **kwargs)

def log_api_call(api_name, method, **kwargs):
    """Логирование вызовов API."""
    log_message('debug', f'API Call: {api_name} - {method}', api_name=api_name, method=method, **kwargs) 