import os
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext
from logger import log_user_action, log_error

# Словарь для хранения истории сообщений пользователей
user_message_history = {}

async def handle_message(update: Update, context: CallbackContext) -> None:
    """
    Обработчик входящих текстовых сообщений.
    """
    try:
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        message_text = update.message.text

        log_user_action(user_id, 'send_message', message=message_text)

        # Проверяем доступ пользователя
        allowed_users = os.getenv('ALLOWED_USERS')
        if allowed_users and str(user_id) not in allowed_users.split(','):
            await update.message.reply_text(
                "Извините, у вас нет доступа к этому боту."
            )
            return

        # Управление историей сообщений
        if user_id not in user_message_history:
            user_message_history[user_id] = []

        user_message_history[user_id].append({
            "role": "user",
            "content": message_text
        })

        # Ограничение истории
        max_history = 10
        if len(user_message_history[user_id]) > max_history * 2:
            user_message_history[user_id] = user_message_history[user_id][-max_history * 2:]

        # Получаем бота из контекста
        bot = context.bot._bot

        # Получаем начальное сообщение
        message_id = await bot.get_initial_response_message(chat_id, context)
        if message_id is None:
            await update.message.reply_text(
                "Произошла ошибка при инициализации ответа. Пожалуйста, попробуйте позже."
            )
            return

        # Запускаем генерацию ответа
        await bot.stream_gpt_response(
            messages=user_message_history[user_id],
            chat_id=chat_id,
            message_id=message_id,
            context=context
        )

    except Exception as e:
        log_error('message_handler', str(e))
        await update.message.reply_text(
            "Произошла ошибка при обработке сообщения. Пожалуйста, попробуйте позже."
        )

async def handle_command(update: Update, context: CallbackContext, command: str) -> None:
    """
    Обработчик команд бота.
    
    Args:
        update (Update): Объект обновления Telegram
        context (CallbackContext): Контекст
        command (str): Имя команды
    """
    try:
        if command == 'start':
            await update.message.reply_text(
                "Привет! Я бот, готов помочь. Используйте команду /settings для изменения параметров."
            )
        elif command == 'settings':
            keyboard = [
                [InlineKeyboardButton("Настройки текстовой модели", callback_data='text_settings')],
                [InlineKeyboardButton("Настройки модели изображений", callback_data='image_settings')],
                [InlineKeyboardButton("Настройки голосовой модели", callback_data='voice_settings')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "Выберите параметры для настройки:",
                reply_markup=reply_markup
            )
        elif command == 'clear_history':
            user_id = update.effective_user.id
            clear_user_history(user_id)
            await update.message.reply_text("История сообщений очищена.")
    except Exception as e:
        log_error('command_handler', str(e))
        await update.message.reply_text(
            "Произошла ошибка при выполнении команды. Пожалуйста, попробуйте позже."
        )

async def handle_callback(update: Update, context: CallbackContext) -> None:
    """
    Обработчик callback-запросов от инлайн-кнопок.
    """
    try:
        query = update.callback_query
        await query.answer()

        data = query.data
        if data == 'text_settings':
            bot = context.bot._bot
            settings = bot.text_settings
            await query.edit_message_text(
                f"Настройки текстовой модели:\n"
                f"1. URL: {settings.base_url}\n"
                f"2. Модель: {settings.model}\n"
                f"3. Температура: {settings.temperature}\n"
                f"4. Max tokens: {settings.max_tokens}"
            )
        elif data == 'image_settings':
            bot = context.bot._bot
            settings = bot.image_settings
            await query.edit_message_text(
                f"Настройки модели изображений:\n"
                f"1. URL: {settings.base_url}\n"
                f"2. Модель: {settings.model}\n"
                f"3. Размер: {settings.size}\n"
                f"4. Качество: {settings.quality}\n"
                f"5. Стиль: {settings.style}"
            )
        elif data == 'voice_settings':
            bot = context.bot._bot
            settings = bot.voice_settings
            await query.edit_message_text(
                f"Настройки голосовой модели:\n"
                f"1. Язык: {settings.language}\n"
                f"2. Акцент: {settings.accent}\n"
                f"3. Скорость речи: {settings.speech_rate}"
            )
        else:
            await query.edit_message_text("Неверный выбор.")
    except Exception as e:
        log_error('callback_handler', str(e))
        await query.edit_message_text(
            "Произошла ошибка при обработке запроса. Пожалуйста, попробуйте позже."
        )

def clear_user_history(user_id: int) -> None:
    """
    Очищает историю сообщений пользователя.
    
    Args:
        user_id (int): ID пользователя
    """
    if user_id in user_message_history:
        user_message_history[user_id] = []
        log_user_action(user_id, 'clear_history') 