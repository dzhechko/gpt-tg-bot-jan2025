from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from loguru import logger
import json
import os
from settings import SettingsManager
from utils import (
    create_settings_keyboard,
    create_text_settings_keyboard,
    create_image_settings_keyboard,
    send_confirmation_dialog,
    validate_temperature,
    validate_max_tokens,
    format_settings_for_display,
    log_handler_call
)

settings_manager = SettingsManager()
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Базовые команды
@log_handler_call
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start."""
    user = update.effective_user
    welcome_text = (
        f"👋 Привет, {user.first_name}!\n\n"
        "Я - GPT бот, который может помочь тебе с текстом и изображениями.\n"
        "Используй следующие команды:\n"
        "/help - показать справку\n"
        "/settings - настройки бота\n"
        "/clear - очистить историю сообщений"
    )
    await update.message.reply_text(welcome_text)

@log_handler_call
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /help."""
    help_text = (
        "🤖 Основные команды:\n\n"
        "📝 Работа с текстом:\n"
        "- Просто отправьте мне текстовое сообщение\n"
        "- Я отвечу вам, используя выбранную модель\n\n"
        "🎨 Работа с изображениями:\n"
        "- Отправьте изображение с описанием\n"
        "- Или просто текст для генерации изображения\n\n"
        "⚙️ Настройки:\n"
        "/settings - открыть меню настроек\n"
        "/clear - очистить историю сообщений\n\n"
        "❓ Дополнительно:\n"
        "- Поддерживаю работу в группах\n"
        "- Можно настроить параметры моделей\n"
        "- Историю можно экспортировать/импортировать"
    )
    await update.message.reply_text(help_text)

@log_handler_call
async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /settings."""
    keyboard = create_settings_keyboard()
    await update.message.reply_text(
        "⚙️ Настройки бота\nВыберите категорию:",
        reply_markup=keyboard
    )

@log_handler_call
async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /clear."""
    await send_confirmation_dialog(
        update,
        context,
        "очистить историю сообщений",
        "clear_history"
    )

# Обработчики текста и изображений
@log_handler_call
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик текстовых сообщений."""
    user_id = update.effective_user.id
    settings = settings_manager.get_user_settings(user_id)
    
    try:
        # Добавляем сообщение пользователя в историю
        settings.message_history.append({
            "role": "user",
            "content": update.message.text
        })
        
        # Отправляем начальное сообщение
        initial_message = await update.message.reply_text(
            "Генерирую ответ..."
        )
        
        # Получаем экземпляр бота для доступа к OpenAI клиенту
        bot = context.application.bot
        
        # Отправляем запрос к модели с использованием streaming
        await bot.stream_chat_completion(
            messages=settings.message_history,
            chat_id=update.effective_chat.id,
            message_id=initial_message.message_id,
            context=context
        )
        
        # Сохраняем обновленную историю
        settings_manager.save_settings()
        
    except Exception as e:
        logger.error(f"Ошибка при обработке текстового сообщения: {e}")
        await update.message.reply_text(
            "Произошла ошибка при обработке сообщения. Пожалуйста, попробуйте позже."
        )

@log_handler_call
async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик изображений."""
    user_id = update.effective_user.id
    settings = settings_manager.get_user_settings(user_id)
    
    # Получаем изображение и подпись
    image = update.message.photo[-1]
    caption = update.message.caption or ""
    
    # TODO: Реализовать обработку изображений
    # Пока просто заглушка
    await update.message.reply_text(
        "Извините, функция обработки изображений временно недоступна."
    )

# Обработчики callback'ов
@log_handler_call
async def handle_settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик callback'ов настроек."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    settings = settings_manager.get_user_settings(user_id)
    
    if query.data == "text_settings":
        keyboard = create_text_settings_keyboard(settings.text_settings.dict())
        await query.edit_message_text(
            "📝 Настройки текстовой модели:",
            reply_markup=keyboard
        )
    
    elif query.data == "image_settings":
        keyboard = create_image_settings_keyboard(settings.image_settings.dict())
        await query.edit_message_text(
            "🎨 Настройки модели изображений:",
            reply_markup=keyboard
        )
    
    elif query.data == "clear_history":
        await send_confirmation_dialog(
            update,
            context,
            "очистить историю сообщений",
            "clear_history"
        )
    
    elif query.data == "export_settings":
        settings_json = settings_manager.export_settings(user_id)
        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=settings_json.encode(),
            filename=f"settings_{user_id}.json",
            caption="📤 Ваши настройки"
        )
    
    elif query.data == "import_settings":
        await query.edit_message_text(
            "📥 Отправьте файл с настройками в формате JSON"
        )
        context.user_data["waiting_for_settings"] = True
    
    elif query.data == "close_settings":
        await query.delete_message()
    
    elif query.data == "back_to_main":
        keyboard = create_settings_keyboard()
        await query.edit_message_text(
            "⚙️ Настройки бота\nВыберите категорию:",
            reply_markup=keyboard
        )
    
    elif query.data.startswith("confirm_"):
        action = query.data.split("_")[1]
        if action == "clear_history":
            settings_manager.clear_message_history(user_id)
            await query.edit_message_text("🗑 История сообщений очищена")
    
    elif query.data == "cancel_confirmation":
        keyboard = create_settings_keyboard()
        await query.edit_message_text(
            "⚙️ Настройки бота\nВыберите категорию:",
            reply_markup=keyboard
        )

# Обработчики изменения настроек
@log_handler_call
async def handle_text_model_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик изменения настроек текстовой модели."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    settings = settings_manager.get_user_settings(user_id)
    
    if query.data == "change_text_model":
        models = settings.text_settings.available_models
        buttons = [[InlineKeyboardButton(model, callback_data=f"set_text_model_{model}")] 
                  for model in models]
        buttons.append([InlineKeyboardButton("🔙 Назад", callback_data="text_settings")])
        keyboard = InlineKeyboardMarkup(buttons)
        await query.edit_message_text(
            "Выберите модель:",
            reply_markup=keyboard
        )
    
    elif query.data.startswith("set_text_model_"):
        model = query.data.replace("set_text_model_", "")
        settings_manager.update_text_settings(user_id, model=model)
        keyboard = create_text_settings_keyboard(settings.text_settings.dict())
        await query.edit_message_text(
            "📝 Настройки текстовой модели:",
            reply_markup=keyboard
        )

@log_handler_call
async def handle_image_model_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик изменения настроек модели изображений."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    settings = settings_manager.get_user_settings(user_id)
    
    if query.data == "change_image_model":
        models = settings.image_settings.available_models
        buttons = [[InlineKeyboardButton(model, callback_data=f"set_image_model_{model}")] 
                  for model in models]
        buttons.append([InlineKeyboardButton("🔙 Назад", callback_data="image_settings")])
        keyboard = InlineKeyboardMarkup(buttons)
        await query.edit_message_text(
            "Выберите модель:",
            reply_markup=keyboard
        )
    
    elif query.data.startswith("set_image_model_"):
        model = query.data.replace("set_image_model_", "")
        settings_manager.update_image_settings(user_id, model=model)
        keyboard = create_image_settings_keyboard(settings.image_settings.dict())
        await query.edit_message_text(
            "🎨 Настройки модели изображений:",
            reply_markup=keyboard
        )
    
    elif query.data == "change_size":
        sizes = settings.image_settings.available_sizes
        buttons = [[InlineKeyboardButton(size, callback_data=f"set_size_{size}")] 
                  for size in sizes]
        buttons.append([InlineKeyboardButton("🔙 Назад", callback_data="image_settings")])
        keyboard = InlineKeyboardMarkup(buttons)
        await query.edit_message_text(
            "Выберите размер изображения:",
            reply_markup=keyboard
        )
    
    elif query.data.startswith("set_size_"):
        size = query.data.replace("set_size_", "")
        settings_manager.update_image_settings(user_id, size=size)
        keyboard = create_image_settings_keyboard(settings.image_settings.dict())
        await query.edit_message_text(
            "🎨 Настройки модели изображений:",
            reply_markup=keyboard
        )
    
    elif query.data == "toggle_hdr":
        current_hdr = settings.image_settings.hdr
        settings_manager.update_image_settings(user_id, hdr=not current_hdr)
        keyboard = create_image_settings_keyboard(settings.image_settings.dict())
        await query.edit_message_text(
            "🎨 Настройки модели изображений:",
            reply_markup=keyboard
        ) 