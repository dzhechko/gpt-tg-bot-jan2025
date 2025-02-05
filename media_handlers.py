import os
from telegram import Update
from telegram.ext import CallbackContext
from logger import log_user_action, log_error
import speech_recognition as sr
import pyttsx3
from utils import download_file, ensure_directory, create_combined_image

class MediaHandler:
    def __init__(self):
        """Инициализация обработчика медиа."""
        self.temp_dir = "temp"
        ensure_directory(self.temp_dir)
        
        # Инициализация распознавания речи
        self.recognizer = sr.Recognizer()
        
        # Инициализация синтеза речи
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)
        self.engine.setProperty('voice', 'russian')

    async def handle_voice(self, update: Update, context: CallbackContext) -> None:
        """
        Обработка голосовых сообщений.
        Конвертирует голос в текст и отправляет ответ.
        """
        try:
            # Получаем файл голосового сообщения
            voice = update.message.voice
            voice_file = await context.bot.get_file(voice.file_id)
            
            # Создаем временный файл
            voice_path = os.path.join(self.temp_dir, f"voice_{update.effective_user.id}.ogg")
            await voice_file.download_to_drive(voice_path)
            
            # Конвертируем в текст
            text = self._convert_voice_to_text(voice_path)
            
            if text:
                # Обрабатываем текст как обычное сообщение
                update.message.text = text  # Подменяем текст для обработки
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"Распознанный текст: {text}"
                )
                # Передаем управление обработчику текстовых сообщений
                from handlers import handle_message
                await handle_message(update, context)
            else:
                await update.message.reply_text(
                    "Извините, не удалось распознать речь. Пожалуйста, попробуйте еще раз."
                )
                
        except Exception as e:
            log_error('voice_handler', str(e))
            await update.message.reply_text(
                "Произошла ошибка при обработке голосового сообщения."
            )
        finally:
            # Очищаем временные файлы
            if os.path.exists(voice_path):
                os.remove(voice_path)

    async def handle_image(self, update: Update, context: CallbackContext) -> None:
        """
        Обработка изображений.
        Сохраняет изображение и ждет текстового описания для генерации нового изображения.
        """
        try:
            # Получаем файл изображения
            photo = update.message.photo[-1]  # Берем последнее (самое качественное) изображение
            photo_file = await context.bot.get_file(photo.file_id)
            
            # Создаем временный файл
            image_path = os.path.join(self.temp_dir, f"image_{update.effective_user.id}.jpg")
            await photo_file.download_to_drive(image_path)
            
            # Сохраняем путь к файлу в контексте пользователя
            if not context.user_data.get('image_processing'):
                context.user_data['image_processing'] = {}
            context.user_data['image_processing']['last_image'] = image_path
            
            await update.message.reply_text(
                "Изображение получено. Пожалуйста, отправьте текстовое описание для генерации нового изображения."
            )
            
        except Exception as e:
            log_error('image_handler', str(e))
            await update.message.reply_text(
                "Произошла ошибка при обработке изображения."
            )

    async def handle_image_with_text(self, update: Update, context: CallbackContext) -> None:
        """
        Обработка текстового описания для изображения.
        Генерирует новое изображение на основе существующего и текстового описания.
        """
        try:
            if not context.user_data.get('image_processing', {}).get('last_image'):
                await update.message.reply_text(
                    "Пожалуйста, сначала отправьте изображение."
                )
                return
                
            image_path = context.user_data['image_processing']['last_image']
            text_prompt = update.message.text
            
            # Получаем настройки из бота
            bot = context.bot._bot
            settings = bot.image_settings
            
            # Генерируем новое изображение
            result = create_combined_image(
                text_prompt=text_prompt,
                image_url=image_path,
                style=settings.style,
                size=settings.size,
                quality=settings.quality,
                hdr=settings.hdr
            )
            
            if result and result.get('url'):
                # Скачиваем и отправляем новое изображение
                new_image_path = os.path.join(self.temp_dir, f"new_image_{update.effective_user.id}.jpg")
                if download_file(result['url'], new_image_path):
                    await context.bot.send_photo(
                        chat_id=update.effective_chat.id,
                        photo=open(new_image_path, 'rb'),
                        caption="Сгенерированное изображение на основе вашего запроса"
                    )
                    os.remove(new_image_path)
                else:
                    await update.message.reply_text(
                        "Не удалось загрузить сгенерированное изображение."
                    )
            else:
                await update.message.reply_text(
                    "Не удалось сгенерировать новое изображение."
                )
                
        except Exception as e:
            log_error('image_with_text_handler', str(e))
            await update.message.reply_text(
                "Произошла ошибка при генерации изображения."
            )
        finally:
            # Очищаем данные
            if context.user_data.get('image_processing'):
                if os.path.exists(context.user_data['image_processing']['last_image']):
                    os.remove(context.user_data['image_processing']['last_image'])
                del context.user_data['image_processing']

    def _convert_voice_to_text(self, voice_path: str) -> str:
        """
        Конвертация голосового файла в текст.
        
        Args:
            voice_path (str): Путь к голосовому файлу
            
        Returns:
            str: Распознанный текст или пустая строка при ошибке
        """
        try:
            with sr.AudioFile(voice_path) as source:
                audio = self.recognizer.record(source)
                return self.recognizer.recognize_google(audio, language='ru-RU')
        except Exception as e:
            log_error('voice_to_text', str(e))
            return ""

    async def text_to_voice(self, text: str, chat_id: int, context: CallbackContext) -> None:
        """
        Конвертация текста в голосовое сообщение.
        
        Args:
            text (str): Текст для конвертации
            chat_id (int): ID чата
            context (CallbackContext): Контекст бота
        """
        try:
            voice_path = os.path.join(self.temp_dir, f"voice_response_{chat_id}.mp3")
            self.engine.save_to_file(text, voice_path)
            self.engine.runAndWait()
            
            await context.bot.send_voice(
                chat_id=chat_id,
                voice=open(voice_path, 'rb')
            )
            
            os.remove(voice_path)
            
        except Exception as e:
            log_error('text_to_voice', str(e))
            await context.bot.send_message(
                chat_id=chat_id,
                text="Не удалось создать голосовое сообщение."
            ) 