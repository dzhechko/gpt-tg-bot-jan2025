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
    log_handler_call,
    create_menu_keyboard,
    check_user_access_decorator,
    check_user_access
)

settings_manager = SettingsManager()
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Базовые команды
@check_user_access_decorator
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start."""
    user = update.effective_user
    welcome_text = (
        f"👋 Привет, {user.first_name}!\n\n"
        "Я - GPT бот, который может помочь тебе с текстом и изображениями.\n"
        "Используй следующие команды:\n"
        "/help - показать справку\n"
        "/settings - настройки бота\n"
        "/current_settings - показать текущие настройки\n"
        "/clear - очистить историю сообщений\n"
        "/myid - показать ваш Telegram ID"
    )
    await update.message.reply_text(welcome_text)

@check_user_access_decorator
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /help."""
    user_id = update.effective_user.id
    has_access = check_user_access(user_id)
    
    base_help_text = (
        "🤖 Основные команды:\n\n"
        "📝 Работа с текстом:\n"
        "- Просто отправьте мне текстовое сообщение\n"
        "- Я отвечу вам, используя выбранную модель\n\n"
        "🎨 Работа с изображениями:\n"
        "- Используйте команду /image или /img с описанием для генерации\n"
        "  Пример: /image нарисуй красивый закат на море\n"
        "- Или отправьте существующее изображение с описанием изменений\n"
        "  для его редактирования\n\n"
    )
    
    if has_access:
        # Полная справка для пользователей с доступом
        help_text = base_help_text + (
            "⚙️ Настройки и команды:\n"
            "/settings - открыть меню настроек\n"
            "/current_settings - показать текущие настройки\n"
            "/clear - очистить историю сообщений\n"
            "/myid - показать ваш Telegram ID\n\n"
            "❓ Дополнительно:\n"
            "- Поддерживаю работу в группах\n"
            "- Можно настроить параметры моделей\n"
            "- Историю можно экспортировать/импортировать\n"
            "- Доступ к боту ограничен списком разрешенных пользователей"
        )
    else:
        # Базовая справка для пользователей без доступа
        help_text = (
            "ℹ️ Информация о боте:\n\n"
            "Это GPT бот с поддержкой обработки текста и генерации изображений.\n"
            "Для использования бота требуется доступ.\n\n"
            "📝 Доступные команды:\n"
            "/help - показать эту справку\n"
            "/myid - показать ваш Telegram ID\n\n"
            "🔐 Как получить доступ:\n"
            "1. Используйте команду /myid чтобы узнать свой Telegram ID\n"
            "2. Свяжитесь с администратором бота для получения доступа\n"
            "3. После получения доступа станут доступны все функции бота"
        )
    
    await update.message.reply_text(help_text)

@check_user_access_decorator
async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /settings."""
    keyboard = create_settings_keyboard()
    await update.message.reply_text(
        "⚙️ Настройки бота\nВыберите категорию:",
        reply_markup=keyboard
    )

@check_user_access_decorator
async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /clear."""
    await send_confirmation_dialog(
        update,
        context,
        "очистить историю сообщений",
        "clear_history"
    )

@check_user_access_decorator
async def show_current_settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /current_settings."""
    user_id = update.effective_user.id
    settings = settings_manager.get_user_settings(user_id)
    
    text = "📊 Текущие настройки:\n\n"
    text += "📝 Текстовая модель:\n"
    text += f"- Модель: {settings.text_settings.model}\n"
    text += f"- Температура: {settings.text_settings.temperature}\n"
    text += f"- Макс. токенов: {settings.text_settings.max_tokens}\n\n"
    text += "🎨 Модель изображений:\n"
    text += f"- Модель: {settings.image_settings.model}\n"
    text += f"- Размер: {settings.image_settings.size}\n"
    text += f"- Качество: {settings.image_settings.quality}\n"
    text += f"- Стиль: {settings.image_settings.style}\n"
    text += f"- HDR: {'Вкл' if settings.image_settings.hdr else 'Выкл'}"
    
    await update.message.reply_text(text)

# Обработчики текста и изображений
@check_user_access_decorator
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
        
        # Получаем экземпляр GPTBot из контекста
        gpt_bot = context.application.bot_data['gpt_bot']
        
        # Отправляем запрос к модели с использованием streaming
        await gpt_bot.stream_chat_completion(
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

@check_user_access_decorator
async def handle_image_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команд /image и /img."""
    user_id = update.effective_user.id
    settings = settings_manager.get_user_settings(user_id)
    
    # Получаем текст после команды
    command_parts = update.message.text.split(maxsplit=1)
    if len(command_parts) < 2:
        await update.message.reply_text(
            "Пожалуйста, добавьте описание желаемого изображения после команды.\n"
            "Например: /image нарисуй красивый закат на море"
        )
        return
    
    prompt = command_parts[1]
    
    try:
        # Отправляем начальное сообщение
        initial_message = await update.message.reply_text(
            "🎨 Генерирую изображение..."
        )
        
        # Получаем экземпляр GPTBot из контекста
        gpt_bot = context.application.bot_data['gpt_bot']
        
        # Генерируем изображение
        image_url = await gpt_bot.create_image(
            prompt=prompt,
            model=settings.image_settings.model,
            size=settings.image_settings.size,
            quality=settings.image_settings.quality,
            style=settings.image_settings.style,
            hdr=settings.image_settings.hdr
        )
        
        # Отправляем изображение
        await context.bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=initial_message.message_id
        )
        await update.message.reply_photo(
            photo=image_url,
            caption=f"🎨 Сгенерировано по запросу: {prompt}"
        )
        
    except Exception as e:
        logger.error(f"Ошибка при генерации изображения: {e}")
        await update.message.reply_text(
            "Произошла ошибка при генерации изображения. Пожалуйста, попробуйте позже."
        )

@check_user_access_decorator
async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик изображений."""
    user_id = update.effective_user.id
    settings = settings_manager.get_user_settings(user_id)
    
    # Получаем изображение и подпись
    image = update.message.photo[-1]
    caption = update.message.caption or ""
    
    if not caption:
        await update.message.reply_text(
            "Пожалуйста, добавьте описание желаемых изменений в подписи к изображению."
        )
        return
    
    try:
        # Отправляем начальное сообщение
        initial_message = await update.message.reply_text(
            "🎨 Обрабатываю изображение..."
        )
        
        # Получаем экземпляр GPTBot из контекста
        gpt_bot = context.application.bot_data['gpt_bot']
        
        # Получаем файл изображения
        file = await context.bot.get_file(image.file_id)
        
        # Генерируем новое изображение на основе существующего
        image_url = await gpt_bot.create_image(
            prompt=caption,
            model=settings.image_settings.model,
            size=settings.image_settings.size,
            quality=settings.image_settings.quality,
            style=settings.image_settings.style,
            hdr=settings.image_settings.hdr,
            reference_image_url=file.file_path
        )
        
        # Отправляем новое изображение
        await context.bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=initial_message.message_id
        )
        await update.message.reply_photo(
            photo=image_url,
            caption=f"🎨 Изображение изменено согласно описанию: {caption}"
        )
        
    except Exception as e:
        logger.error(f"Ошибка при обработке изображения: {e}")
        await update.message.reply_text(
            "Произошла ошибка при обработке изображения. Пожалуйста, попробуйте позже."
        )

# Обработчики callback'ов
@check_user_access_decorator
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
@check_user_access_decorator
async def handle_text_model_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик изменения настроек текстовой модели."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    settings = settings_manager.get_user_settings(user_id)
    logger.debug(f"Processing text model settings for user {user_id}, data: {query.data}")
    
    if query.data == "change_text_model":
        models = settings.text_settings.available_models
        current_model = settings.text_settings.effective_model
        buttons = [[InlineKeyboardButton(f"{model} {'✓' if model == current_model else ''}", 
                   callback_data=f"set_text_model_{model}")] for model in models]
        buttons.append([InlineKeyboardButton("🔙 Назад", callback_data="text_settings")])
        keyboard = InlineKeyboardMarkup(buttons)
        await query.edit_message_text(
            "Выберите модель:\n\n"
            "gpt-4o-mini - базовая модель (по умолчанию)\n"
            "gpt-4o - улучшенная модель\n"
            "gpt-4 - продвинутая модель\n"
            "Custom Model - указать свою модель",
            reply_markup=keyboard
        )
    
    elif query.data.startswith("set_text_model_"):
        model = query.data.replace("set_text_model_", "")
        if model == "Custom Model":
            # Сохраняем состояние ожидания ввода пользовательской модели
            context.user_data["waiting_for_custom_model"] = True
            await query.edit_message_text(
                "Пожалуйста, введите название модели.\n"
                "Например: gpt-3.5-turbo\n\n"
                "Для отмены введите /cancel"
            )
        else:
            settings_manager.update_text_settings(user_id, model=model)
            keyboard = create_text_settings_keyboard(settings.text_settings.dict())
            await query.edit_message_text(
                "📝 Настройки текстовой модели:",
                reply_markup=keyboard
            )
    
    elif query.data == "change_temperature":
        temp_values = ["0.0", "0.3", "0.5", "0.7", "1.0", "1.5", "2.0"]
        current_temp = str(settings.text_settings.temperature)
        buttons = [[InlineKeyboardButton(f"🌡 {temp} {'✓' if temp == current_temp else ''}", 
                   callback_data=f"set_temp_{temp}")] for temp in temp_values]
        buttons.append([InlineKeyboardButton("🔙 Назад", callback_data="text_settings")])
        keyboard = InlineKeyboardMarkup(buttons)
        await query.edit_message_text(
            "Выберите значение температуры:\n\n"
            "0.0 - наиболее предсказуемые ответы\n"
            "0.3-0.7 - баланс креативности и предсказуемости\n"
            "1.0-2.0 - наиболее креативные ответы",
            reply_markup=keyboard
        )
    
    elif query.data.startswith("set_temp_"):
        temp = float(query.data.replace("set_temp_", ""))
        settings_manager.update_text_settings(user_id, temperature=temp)
        keyboard = create_text_settings_keyboard(settings.text_settings.dict())
        await query.edit_message_text(
            "📝 Настройки текстовой модели:",
            reply_markup=keyboard
        )
    
    elif query.data == "change_max_tokens":
        token_values = ["500", "1000", "2000", "3000", "4000"]
        current_tokens = str(settings.text_settings.max_tokens)
        buttons = [[InlineKeyboardButton(f"📊 {token} {'✓' if token == current_tokens else ''}", 
                   callback_data=f"set_tokens_{token}")] for token in token_values]
        buttons.append([InlineKeyboardButton("🔙 Назад", callback_data="text_settings")])
        keyboard = InlineKeyboardMarkup(buttons)
        await query.edit_message_text(
            "Выберите максимальное количество токенов:\n\n"
            "500 - короткие ответы\n"
            "1000 - средние ответы (рекомендуется)\n"
            "2000-4000 - длинные ответы",
            reply_markup=keyboard
        )
    
    elif query.data.startswith("set_tokens_"):
        tokens = int(query.data.replace("set_tokens_", ""))
        settings_manager.update_text_settings(user_id, max_tokens=tokens)
        keyboard = create_text_settings_keyboard(settings.text_settings.dict())
        await query.edit_message_text(
            "📝 Настройки текстовой модели:",
            reply_markup=keyboard
        )
    
    elif query.data == "change_base_url":
        # Сохраняем состояние ожидания ввода base_url
        context.user_data["waiting_for_base_url"] = True
        await query.edit_message_text(
            "Введите новый Base URL.\n\n"
            "По умолчанию: https://api.openai.com/v1\n\n"
            "Для отмены введите /cancel"
        )

# Добавляем обработчик для пользовательского ввода модели
@check_user_access_decorator
async def handle_custom_model_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик ввода пользовательской модели."""
    if not context.user_data.get("waiting_for_custom_model"):
        return

    user_id = update.effective_user.id
    custom_model = update.message.text

    if custom_model.lower() == '/cancel':
        context.user_data["waiting_for_custom_model"] = False
        keyboard = create_text_settings_keyboard(
            settings_manager.get_user_settings(user_id).text_settings.dict()
        )
        await update.message.reply_text(
            "📝 Настройки текстовой модели:",
            reply_markup=keyboard
        )
        return

    settings_manager.update_text_settings(
        user_id, 
        model="Custom Model",
        custom_model=custom_model
    )
    context.user_data["waiting_for_custom_model"] = False
    
    keyboard = create_text_settings_keyboard(
        settings_manager.get_user_settings(user_id).text_settings.dict()
    )
    await update.message.reply_text(
        f"✅ Установлена пользовательская модель: {custom_model}\n\n"
        "📝 Настройки текстовой модели:",
        reply_markup=keyboard
    )

@check_user_access_decorator
async def handle_image_model_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик изменения настроек модели изображений."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    settings = settings_manager.get_user_settings(user_id)
    
    if query.data == "change_image_model":
        models = settings.image_settings.available_models
        current_model = settings.image_settings.model
        buttons = [[InlineKeyboardButton(f"{model} {'✓' if model == current_model else ''}", 
                   callback_data=f"set_image_model_{model}")] for model in models]
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
    
    elif query.data == "change_image_base_url":
        # Сохраняем состояние ожидания ввода base_url для изображений
        context.user_data["waiting_for_image_base_url"] = True
        await query.edit_message_text(
            "Введите новый Base URL для модели изображений.\n\n"
            "По умолчанию: https://api.openai.com/v1\n\n"
            "Для отмены введите /cancel"
        )
    
    elif query.data == "change_size":
        sizes = settings.image_settings.available_sizes
        current_size = settings.image_settings.size
        buttons = [[InlineKeyboardButton(f"{size} {'✓' if size == current_size else ''}", 
                   callback_data=f"set_size_{size}")] for size in sizes]
        buttons.append([InlineKeyboardButton("🔙 Назад", callback_data="image_settings")])
        keyboard = InlineKeyboardMarkup(buttons)
        await query.edit_message_text(
            "Выберите размер изображения:\n\n"
            "1024x1024 - квадратное изображение\n"
            "1024x1792 - вертикальное изображение\n"
            "1792x1024 - горизонтальное изображение",
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
    
    elif query.data == "change_quality":
        qualities = settings.image_settings.available_qualities
        current_quality = settings.image_settings.quality
        buttons = [[InlineKeyboardButton(f"{quality} {'✓' if quality == current_quality else ''}", 
                   callback_data=f"set_quality_{quality}")] for quality in qualities]
        buttons.append([InlineKeyboardButton("🔙 Назад", callback_data="image_settings")])
        keyboard = InlineKeyboardMarkup(buttons)
        await query.edit_message_text(
            "Выберите качество изображения:\n\n"
            "standard - стандартное качество (быстрее)\n"
            "hd - высокое качество (более детальное)",
            reply_markup=keyboard
        )
    
    elif query.data.startswith("set_quality_"):
        quality = query.data.replace("set_quality_", "")
        settings_manager.update_image_settings(user_id, quality=quality)
        keyboard = create_image_settings_keyboard(settings.image_settings.dict())
        await query.edit_message_text(
            "🎨 Настройки модели изображений:",
            reply_markup=keyboard
        )
    
    elif query.data == "change_style":
        styles = settings.image_settings.available_styles
        current_style = settings.image_settings.style
        buttons = [[InlineKeyboardButton(f"{style} {'✓' if style == current_style else ''}", 
                   callback_data=f"set_style_{style}")] for style in styles]
        buttons.append([InlineKeyboardButton("🔙 Назад", callback_data="image_settings")])
        keyboard = InlineKeyboardMarkup(buttons)
        await query.edit_message_text(
            "Выберите стиль изображения:\n\n"
            "natural - естественный, реалистичный стиль\n"
            "vivid - яркий, выразительный стиль",
            reply_markup=keyboard
        )
    
    elif query.data.startswith("set_style_"):
        style = query.data.replace("set_style_", "")
        settings_manager.update_image_settings(user_id, style=style)
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

# Добавляем обработчик для пользовательского ввода base_url для изображений
@check_user_access_decorator
async def handle_image_base_url_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик ввода base_url для модели изображений."""
    if not context.user_data.get("waiting_for_image_base_url"):
        return

    user_id = update.effective_user.id
    new_base_url = update.message.text

    if new_base_url.lower() == '/cancel':
        context.user_data["waiting_for_image_base_url"] = False
        keyboard = create_image_settings_keyboard(
            settings_manager.get_user_settings(user_id).image_settings.dict()
        )
        await update.message.reply_text(
            "🎨 Настройки модели изображений:",
            reply_markup=keyboard
        )
        return

    # Проверяем формат URL
    if not new_base_url.startswith(('http://', 'https://')):
        await update.message.reply_text(
            "❌ Некорректный формат URL. URL должен начинаться с http:// или https://\n"
            "Попробуйте еще раз или введите /cancel для отмены."
        )
        return

    settings_manager.update_image_settings(user_id, base_url=new_base_url)
    context.user_data["waiting_for_image_base_url"] = False
    
    keyboard = create_image_settings_keyboard(
        settings_manager.get_user_settings(user_id).image_settings.dict()
    )
    await update.message.reply_text(
        f"✅ Установлен новый Base URL для модели изображений: {new_base_url}\n\n"
        "🎨 Настройки модели изображений:",
        reply_markup=keyboard
    )

# Добавляем обработчик для пользовательского ввода base_url
@check_user_access_decorator
async def handle_base_url_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик ввода base_url для текстовой модели."""
    if not context.user_data.get("waiting_for_base_url"):
        return

    user_id = update.effective_user.id
    new_base_url = update.message.text

    if new_base_url.lower() == '/cancel':
        context.user_data["waiting_for_base_url"] = False
        keyboard = create_text_settings_keyboard(
            settings_manager.get_user_settings(user_id).text_settings.dict()
        )
        await update.message.reply_text(
            "📝 Настройки текстовой модели:",
            reply_markup=keyboard
        )
        return

    # Проверяем формат URL
    if not new_base_url.startswith(('http://', 'https://')):
        await update.message.reply_text(
            "❌ Некорректный формат URL. URL должен начинаться с http:// или https://\n"
            "Попробуйте еще раз или введите /cancel для отмены."
        )
        return

    settings_manager.update_text_settings(user_id, base_url=new_base_url)
    context.user_data["waiting_for_base_url"] = False
    
    keyboard = create_text_settings_keyboard(
        settings_manager.get_user_settings(user_id).text_settings.dict()
    )
    await update.message.reply_text(
        f"✅ Установлен новый Base URL для текстовой модели: {new_base_url}\n\n"
        "📝 Настройки текстовой модели:",
        reply_markup=keyboard
    )

# Добавляем обработчик для импорта настроек из JSON файла
@check_user_access_decorator
async def handle_settings_import(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик импорта настроек из JSON файла."""
    if not context.user_data.get("waiting_for_settings"):
        return

    try:
        # Проверяем, что получен документ
        if not update.message.document:
            await update.message.reply_text(
                "❌ Пожалуйста, отправьте файл настроек в формате JSON."
            )
            return

        # Проверяем расширение файла
        if not update.message.document.file_name.endswith('.json'):
            await update.message.reply_text(
                "❌ Файл должен иметь расширение .json"
            )
            return

        # Получаем файл
        file = await context.bot.get_file(update.message.document.file_id)
        
        # Скачиваем содержимое файла
        settings_json = await file.download_as_bytearray()
        settings_str = settings_json.decode('utf-8')

        # Импортируем настройки
        user_id = update.effective_user.id
        settings_manager.import_settings(user_id, settings_str)

        # Отправляем подтверждение
        keyboard = create_settings_keyboard()
        await update.message.reply_text(
            "✅ Настройки успешно импортированы!\n\n"
            "⚙️ Настройки бота\nВыберите категорию:",
            reply_markup=keyboard
        )

    except json.JSONDecodeError:
        await update.message.reply_text(
            "❌ Ошибка при чтении файла. Убедитесь, что файл содержит корректный JSON."
        )
    except ValueError as e:
        await update.message.reply_text(
            f"❌ Ошибка при импорте настроек: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Ошибка при импорте настроек: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при импорте настроек. Пожалуйста, попробуйте позже."
        )
    finally:
        # Сбрасываем состояние ожидания
        context.user_data["waiting_for_settings"] = False 

@check_user_access_decorator
async def myid_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает Telegram ID пользователя."""
    user = update.effective_user
    await update.message.reply_text(
        f"👤 Ваш Telegram ID: `{user.id}`\n"
        f"Username: @{user.username}\n"
        f"Имя: {user.first_name}",
        parse_mode='Markdown'
    ) 