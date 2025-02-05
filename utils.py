from typing import Optional, Tuple, Any
from loguru import logger
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import os

DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

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
    buttons = [
        [("🔄 Изменить модель", "change_text_model")],
        [(f"🌡 Температура: {current_settings.get('temperature', 0.7)}", "change_temperature")],
        [(f"📊 Макс. токенов: {current_settings.get('max_tokens', 1000)}", "change_max_tokens")],
        [("🔙 Назад", "back_to_main"), ("❌ Закрыть", "close_settings")]
    ]
    return create_menu_keyboard(buttons)

def create_image_settings_keyboard(current_settings: dict) -> InlineKeyboardMarkup:
    """Создает клавиатуру для настроек модели изображений."""
    buttons = [
        [("🔄 Изменить модель", "change_image_model")],
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
        buttons.append([(f"HDR: {'Вкл' if current_settings['hdr'] else 'Выкл'}", "toggle_hdr")])
    
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