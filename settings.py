from pydantic import BaseModel
from typing import Optional
import json
from loguru import logger
import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Включение/выключение режима отладки
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Настройка логирования
if DEBUG:
    logger.add("debug.log", rotation="500 MB", level="DEBUG")
else:
    logger.add("production.log", rotation="500 MB", level="INFO")

class TextModelSettings(BaseModel):
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 1000

    @property
    def available_models(self):
        return ["gpt-4o-mini", "gpt-4o", "gpt-4", "claude-3-sonnet"]

class ImageModelSettings(BaseModel):
    base_url: str = "https://api.openai.com/v1"
    model: str = "dall-e-3"
    size: str = "1024x1024"
    quality: str = "standard"
    style: str = "natural"
    hdr: bool = False

    @property
    def available_models(self):
        return ["dall-e-3", "dall-e-2", "stable-diffusion-xl"]

    @property
    def available_sizes(self):
        return ["1024x1024", "1024x1792", "1792x1024"]

    @property
    def available_qualities(self):
        return ["standard", "hd"]

    @property
    def available_styles(self):
        return ["natural", "vivid"]

class UserSettings(BaseModel):
    user_id: int
    text_settings: TextModelSettings = TextModelSettings()
    image_settings: ImageModelSettings = ImageModelSettings()
    message_history: list = []

class SettingsManager:
    def __init__(self, settings_file="user_settings.json"):
        self.settings_file = settings_file
        self.users: dict[int, UserSettings] = {}
        self.load_settings()

    def load_settings(self):
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for user_id, settings in data.items():
                        self.users[int(user_id)] = UserSettings.parse_obj(settings)
                logger.info("Настройки успешно загружены")
        except Exception as e:
            logger.error(f"Ошибка при загрузке настроек: {e}")

    def save_settings(self):
        try:
            data = {str(user_id): settings.dict() for user_id, settings in self.users.items()}
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            logger.info("Настройки успешно сохранены")
        except Exception as e:
            logger.error(f"Ошибка при сохранении настроек: {e}")

    def get_user_settings(self, user_id: int) -> UserSettings:
        if user_id not in self.users:
            self.users[user_id] = UserSettings(user_id=user_id)
        return self.users[user_id]

    def update_text_settings(self, user_id: int, **kwargs):
        settings = self.get_user_settings(user_id)
        for key, value in kwargs.items():
            if hasattr(settings.text_settings, key):
                setattr(settings.text_settings, key, value)
        self.save_settings()
        logger.debug(f"Обновлены текстовые настройки для пользователя {user_id}: {kwargs}")

    def update_image_settings(self, user_id: int, **kwargs):
        settings = self.get_user_settings(user_id)
        for key, value in kwargs.items():
            if hasattr(settings.image_settings, key):
                setattr(settings.image_settings, key, value)
        self.save_settings()
        logger.debug(f"Обновлены настройки изображений для пользователя {user_id}: {kwargs}")

    def clear_message_history(self, user_id: int):
        settings = self.get_user_settings(user_id)
        settings.message_history.clear()
        self.save_settings()
        logger.info(f"Очищена история сообщений для пользователя {user_id}")

    def export_settings(self, user_id: int) -> str:
        settings = self.get_user_settings(user_id)
        return json.dumps(settings.dict(), ensure_ascii=False, indent=4)

    def import_settings(self, user_id: int, settings_json: str):
        try:
            settings_dict = json.loads(settings_json)
            self.users[user_id] = UserSettings.parse_obj(settings_dict)
            self.save_settings()
            logger.info(f"Настройки успешно импортированы для пользователя {user_id}")
        except Exception as e:
            logger.error(f"Ошибка при импорте настроек: {e}")
            raise ValueError("Неверный формат настроек") 