from typing import Optional, Tuple, Any
from loguru import logger
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import os

DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

def check_user_access(user_id: int) -> bool:
    """
    Проверяет, имеет ли пользователь доступ к боту.
    
    Args:
        user_id: ID пользователя Telegram
    
    Returns:
        bool: True если пользователь имеет доступ, False в противном случае
    """
    allowed_users = os.getenv('ALLOWED_USERS')
    
    # Если переменная ALLOWED_USERS не задана или пустая, запрещаем доступ
    if not allowed_users:
        logger.warning(f"Переменная ALLOWED_USERS не задана. Доступ запрещен для пользователя {user_id}")
        return False
    
    try:
        # Преобразуем строку с ID в список чисел
        allowed_ids = [int(uid.strip()) for uid in allowed_users.split(',') if uid.strip().isdigit()]
        
        # Если список пустой после обработки, запрещаем доступ
        if not allowed_ids:
            logger.warning("Список ALLOWED_USERS пуст или содержит некорректные значения")
            return False
        
        # Проверяем наличие ID пользователя в списке разрешенных
        has_access = user_id in allowed_ids
        if not has_access:
            logger.warning(f"Попытка доступа от неразрешенного пользователя {user_id}")
        return has_access
        
    except Exception as e:
        logger.error(f"Ошибка при проверке доступа: {e}")
        return False

def load_groups() -> list:
    """Загружает список разрешенных групп из файла."""
    try:
        if os.path.exists('allowed_groups.json'):
            with open('allowed_groups.json', 'r') as f:
                return json.load(f)
        return []
    except Exception as e:
        logger.error(f"Ошибка при загрузке списка групп: {e}")
        return []

def check_group_access(chat_id: int) -> bool:
    """
    Проверяет, имеет ли группа доступ к боту.
    
    Args:
        chat_id: ID группы Telegram
    
    Returns:
        bool: True если группа имеет доступ, False в противном случае
    """
    # Загружаем список разрешенных групп из файла
    allowed_groups = load_groups()
    
    # Если список пустой, разрешаем доступ всем группам
    if not allowed_groups:
        return True
    
    # Проверяем наличие ID группы в списке разрешенных
    has_access = str(chat_id) in allowed_groups
    if not has_access:
        logger.warning(f"Попытка доступа из неразрешенной группы {chat_id}")
    return has_access

def check_user_access_decorator(func):
    """Декоратор для проверки доступа пользователя к командам бота."""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        is_group = update.effective_chat.type in ['group', 'supergroup']
        
        # Список команд, доступных всем пользователям
        public_commands = ['myid_command', 'help_command', 'start_command']
        
        # Если это публичная команда, разрешаем доступ
        if func.__name__ in public_commands:
            return await func(update, context, *args, **kwargs)
        
        # Проверяем доступ в зависимости от типа чата
        if is_group:
            # Для групп проверяем и доступ группы, и доступ пользователя
            if not check_group_access(chat_id):
                logger.warning(f"Попытка использования бота в неразрешенной группе {chat_id}")
                await update.message.reply_text(
                    "⛔️ Этот бот не настроен для использования в данной группе.\n"
                    "Администратор группы может связаться с владельцем бота для получения доступа: @djdim"
                )
                return None
            
            if not check_user_access(user_id):
                logger.warning(f"Попытка несанкционированного доступа от пользователя {user_id} в группе {chat_id}")
                await update.message.reply_text(
                    f"⛔️ У пользователя @{update.effective_user.username} нет доступа к боту.\n\n"
                    "Используйте /help для получения информации или /myid чтобы узнать свой Telegram ID.\n\n"
                    "Для получения доступа свяжитесь с администратором: @djdim"
                )
                return None
        else:
            # Для личных чатов проверяем только доступ пользователя
            if not check_user_access(user_id):
                logger.warning(f"Попытка несанкционированного доступа от пользователя {user_id}")
                await update.message.reply_text(
                    "⛔️ У вас нет доступа к этому боту.\n\n"
                    "Используйте /help для получения информации или /myid чтобы узнать свой Telegram ID.\n\n"
                    "Для получения доступа свяжитесь с администратором: @djdim"
                )
                return None
        
        return await func(update, context, *args, **kwargs)
    return wrapper

def create_menu_keyboard(buttons: list[list[tuple[str, str]]]) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру из списка кнопок.
    
    Args:
        buttons: Список списков кнопок в формате [(текст, callback_data), ...]
    """
    keyboard = []
    for row in buttons:
        keyboard_row = []
        for text, callback_data in row:
            keyboard_row.append(InlineKeyboardButton(text, callback_data=callback_data))
        keyboard.append(keyboard_row)
    return InlineKeyboardMarkup(keyboard)

def create_settings_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру для главного меню настроек."""
    buttons = [
        [("📝 Настройки текста", "text_settings")],
        [("🎨 Настройки изображений", "image_settings")],
        [("🗑 Очистить историю", "clear_history")],
        [("💾 Экспорт настроек", "export_settings"),
         ("📥 Импорт настроек", "import_settings")],
        [("❌ Закрыть", "close_settings")]
    ]
    return create_menu_keyboard(buttons)

def create_text_settings_keyboard(current_settings: dict) -> InlineKeyboardMarkup:
    """Создает клавиатуру для настроек текстовой модели."""
    logger.debug(f"Creating text settings keyboard with settings: {current_settings}")
    current_model = current_settings.get('effective_model', current_settings.get('model', 'gpt-4o-mini'))
    current_temp = current_settings.get('temperature', 0.7)
    current_tokens = current_settings.get('max_tokens', 1000)
    current_base_url = current_settings.get('base_url', 'https://api.openai.com/v1')
    
    # Сокращаем base_url для отображения, если он слишком длинный
    display_base_url = current_base_url
    if len(display_base_url) > 30:
        display_base_url = display_base_url[:27] + "..."
    
    buttons = [
        [(f"🔄 Модель: {current_model}", "change_text_model")],
        [(f"🌐 Base URL: {display_base_url}", "change_base_url")],
        [(f"🌡 Температура: {current_temp}", "change_temperature")],
        [(f"📊 Макс. токенов: {current_tokens}", "change_max_tokens")],
        [("🔙 Назад", "back_to_main"), ("❌ Закрыть", "close_settings")]
    ]
    return create_menu_keyboard(buttons)

def create_image_settings_keyboard(current_settings: dict) -> InlineKeyboardMarkup:
    """Создает клавиатуру для настроек модели изображений."""
    # Сокращаем base_url для отображения, если он слишком длинный
    current_base_url = current_settings.get('base_url', 'https://api.openai.com/v1')
    display_base_url = current_base_url
    if len(display_base_url) > 30:
        display_base_url = display_base_url[:27] + "..."
    
    buttons = [
        [(f"🔄 Модель: {current_settings['model']}", "change_image_model")],
        [(f"🌐 Base URL: {display_base_url}", "change_image_base_url")],
        [(f"📏 Размер: {current_settings['size']}", "change_size")]
    ]
    
    # Добавляем кнопку качества только если модель поддерживает разные качества
    if len(current_settings.get('available_qualities', [])) > 1:
        buttons.append([(f"✨ Качество: {current_settings['quality']}", "change_quality")])
    
    # Добавляем кнопку стиля только если модель поддерживает стили
    if current_settings.get('available_styles', []):
        buttons.append([(f"🎨 Стиль: {current_settings['style']}", "change_style")])
    
    # Добавляем кнопку HDR только если модель поддерживает HDR
    if current_settings.get('supports_hdr', False):
        hdr_status = 'Вкл' if current_settings['hdr'] else 'Выкл'
        buttons.append([(f"HDR: {hdr_status}", "toggle_hdr")])
    
    buttons.append([("🔙 Назад", "back_to_main"), ("❌ Закрыть", "close_settings")])
    return create_menu_keyboard(buttons)

async def send_confirmation_dialog(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    action: str,
    callback_data: str
) -> None:
    """
    Отправляет диалог подтверждения действия.
    
    Args:
        update: Объект обновления Telegram
        context: Контекст бота
        action: Описание действия
        callback_data: Данные для callback
    """
    buttons = [
        [("✅ Да", f"confirm_{callback_data}"),
         ("❌ Нет", "cancel_confirmation")]
    ]
    keyboard = create_menu_keyboard(buttons)
    
    await update.callback_query.edit_message_text(
        f"Вы уверены, что хотите {action}?",
        reply_markup=keyboard
    )

def validate_temperature(value: Any) -> Tuple[bool, float]:
    """
    Проверяет значение температуры.
    
    Returns:
        Tuple[bool, float]: (успех, значение/сообщение об ошибке)
    """
    try:
        temp = float(value)
        if 0 <= temp <= 1:
            return True, temp
        return False, "Температура должна быть от 0 до 1"
    except ValueError:
        return False, "Некорректное значение температуры"

def validate_max_tokens(value: Any) -> Tuple[bool, int]:
    """
    Проверяет значение максимального количества токенов.
    
    Returns:
        Tuple[bool, int]: (успех, значение/сообщение об ошибке)
    """
    try:
        tokens = int(value)
        if tokens >= 150:
            return True, tokens
        return False, "Минимальное значение токенов: 150"
    except ValueError:
        return False, "Некорректное значение токенов"

def log_handler_call(func):
    """Декоратор для логирования вызовов обработчиков."""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if DEBUG:
            user = update.effective_user
            logger.debug(
                f"Handler {func.__name__} called by user {user.id} ({user.username})"
            )
        return await func(update, context, *args, **kwargs)
    return wrapper

def format_settings_for_display(settings: dict) -> str:
    """
    Форматирует настройки для отображения пользователю.
    
    Args:
        settings: Словарь с настройками
    
    Returns:
        str: Отформатированный текст настроек
    """
    text = "Текущие настройки:\n\n"
    
    if 'text_settings' in settings:
        text += "📝 Настройки текста:\n"
        text += f"- Модель: {settings['text_settings']['model']}\n"
        text += f"- Температура: {settings['text_settings']['temperature']}\n"
        text += f"- Макс. токенов: {settings['text_settings']['max_tokens']}\n\n"
    
    if 'image_settings' in settings:
        text += "🎨 Настройки изображений:\n"
        text += f"- Модель: {settings['image_settings']['model']}\n"
        text += f"- Размер: {settings['image_settings']['size']}\n"
        text += f"- Качество: {settings['image_settings']['quality']}\n"
        text += f"- Стиль: {settings['image_settings']['style']}\n"
        text += f"- HDR: {'Вкл' if settings['image_settings']['hdr'] else 'Выкл'}\n"
    
    return text 