import json
import os
from typing import Dict, Any, Tuple
from utils import validate_temperature, validate_max_tokens

class TextModelSettings:
    """Настройки текстовой модели."""
    AVAILABLE_MODELS = [
        "gpt-4",
        "gpt-4-turbo",
        "gpt-3.5-turbo",
        "gpt-3.5-turbo-16k"
    ]

    def __init__(self, base_url="https://api.openai.com/v1", model="gpt-4", temperature=0.7, max_tokens=2000):
        self.base_url = base_url
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def update_settings(self, base_url=None, model=None, temperature=None, max_tokens=None) -> Tuple[bool, str]:
        """
        Обновление настроек с валидацией.
        
        Returns:
            Tuple[bool, str]: (успех, сообщение)
        """
        try:
            if base_url is not None:
                self.base_url = base_url

            if model is not None:
                if model not in self.AVAILABLE_MODELS and not model.startswith("gpt-"):
                    return False, "Неподдерживаемая модель"
                self.model = model

            if temperature is not None:
                success, result = validate_temperature(temperature)
                if not success:
                    return False, result
                self.temperature = result

            if max_tokens is not None:
                success, result = validate_max_tokens(max_tokens)
                if not success:
                    return False, result
                self.max_tokens = result

            return True, "Настройки успешно обновлены"
        except Exception as e:
            return False, f"Ошибка при обновлении настроек: {str(e)}"

class ImageModelSettings:
    """Настройки модели изображений."""
    AVAILABLE_MODELS = [
        "dall-e-3",
        "dall-e-2",
        "stable-diffusion-v2",
        "midjourney-v5"
    ]
    
    AVAILABLE_SIZES = [
        "256x256",
        "512x512",
        "1024x1024",
        "1024x1792",
        "1792x1024"
    ]
    
    AVAILABLE_QUALITIES = ["standard", "high", "ultra"]
    AVAILABLE_STYLES = ["vivid", "natural", "artistic", "photographic"]

    def __init__(self, base_url="https://api.openai.com/v1", model="dall-e-3", 
                 size="1024x1024", quality="high", style="natural", hdr=False):
        self.base_url = base_url
        self.model = model
        self.size = size
        self.quality = quality
        self.style = style
        self.hdr = hdr

    def update_settings(self, **kwargs) -> Tuple[bool, str]:
        """
        Обновление настроек с валидацией.
        
        Returns:
            Tuple[bool, str]: (успех, сообщение)
        """
        try:
            if 'model' in kwargs:
                if kwargs['model'] not in self.AVAILABLE_MODELS:
                    return False, "Неподдерживаемая модель"
                self.model = kwargs['model']

            if 'size' in kwargs:
                if kwargs['size'] not in self.AVAILABLE_SIZES:
                    return False, "Неподдерживаемый размер"
                self.size = kwargs['size']

            if 'quality' in kwargs:
                if kwargs['quality'] not in self.AVAILABLE_QUALITIES:
                    return False, "Неподдерживаемое качество"
                self.quality = kwargs['quality']

            if 'style' in kwargs:
                if kwargs['style'] not in self.AVAILABLE_STYLES:
                    return False, "Неподдерживаемый стиль"
                self.style = kwargs['style']

            if 'hdr' in kwargs:
                self.hdr = bool(kwargs['hdr'])

            if 'base_url' in kwargs:
                self.base_url = kwargs['base_url']

            return True, "Настройки успешно обновлены"
        except Exception as e:
            return False, f"Ошибка при обновлении настроек: {str(e)}"

    def get_image_settings(self) -> Dict[str, Any]:
        """Получение текущих настроек."""
        return {
            "base_url": self.base_url,
            "model": self.model,
            "size": self.size,
            "quality": self.quality,
            "style": self.style,
            "hdr": self.hdr
        }

class VoiceModelSettings:
    """Настройки голосовой модели."""
    AVAILABLE_LANGUAGES = ["ru", "en", "es", "fr", "de"]
    AVAILABLE_ACCENTS = ["default", "neutral", "formal", "casual"]
    
    def __init__(self, language="ru", accent="default", speech_rate=1.0, auto_voice_response=False):
        self.language = language
        self.accent = accent
        self.speech_rate = speech_rate
        self.auto_voice_response = auto_voice_response

    def update_settings(self, language=None, accent=None, speech_rate=None, 
                       auto_voice_response=None) -> Tuple[bool, str]:
        """
        Обновление настроек с валидацией.
        
        Returns:
            Tuple[bool, str]: (успех, сообщение)
        """
        try:
            if language is not None:
                if language not in self.AVAILABLE_LANGUAGES:
                    return False, "Неподдерживаемый язык"
                self.language = language

            if accent is not None:
                if accent not in self.AVAILABLE_ACCENTS:
                    return False, "Неподдерживаемый акцент"
                self.accent = accent

            if speech_rate is not None:
                try:
                    rate = float(speech_rate)
                    if 0.5 <= rate <= 2.0:
                        self.speech_rate = rate
                    else:
                        return False, "Скорость речи должна быть от 0.5 до 2.0"
                except ValueError:
                    return False, "Некорректное значение скорости речи"

            if auto_voice_response is not None:
                self.auto_voice_response = bool(auto_voice_response)

            return True, "Настройки успешно обновлены"
        except Exception as e:
            return False, f"Ошибка при обновлении настроек: {str(e)}"

def export_settings(text_settings: TextModelSettings, 
                   image_settings: ImageModelSettings,
                   voice_settings: VoiceModelSettings,
                   file_path: str = "settings_backup.json") -> Tuple[bool, str]:
    """
    Экспорт настроек в JSON файл.
    
    Args:
        text_settings (TextModelSettings): Настройки текстовой модели
        image_settings (ImageModelSettings): Настройки модели изображений
        voice_settings (VoiceModelSettings): Настройки голосовой модели
        file_path (str): Путь для сохранения файла
        
    Returns:
        Tuple[bool, str]: (успех, сообщение)
    """
    try:
        settings = {
            "text": {
                "base_url": text_settings.base_url,
                "model": text_settings.model,
                "temperature": text_settings.temperature,
                "max_tokens": text_settings.max_tokens
            },
            "image": image_settings.get_image_settings(),
            "voice": {
                "language": voice_settings.language,
                "accent": voice_settings.accent,
                "speech_rate": voice_settings.speech_rate,
                "auto_voice_response": voice_settings.auto_voice_response
            }
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=4)
        return True, f"Настройки успешно экспортированы в {file_path}"
    except Exception as e:
        return False, f"Ошибка при экспорте настроек: {str(e)}"

def import_settings(file_path: str = "settings_backup.json") -> Tuple[bool, str, Dict[str, Any]]:
    """
    Импорт настроек из JSON файла.
    
    Args:
        file_path (str): Путь к файлу с настройками
        
    Returns:
        Tuple[bool, str, Dict]: (успех, сообщение, настройки)
    """
    try:
        if not os.path.exists(file_path):
            return False, "Файл настроек не найден", {}
            
        with open(file_path, 'r', encoding='utf-8') as f:
            settings = json.load(f)
            
        # Валидация структуры настроек
        required_sections = ["text", "image", "voice"]
        if not all(section in settings for section in required_sections):
            return False, "Некорректный формат файла настроек", {}
            
        return True, "Настройки успешно импортированы", settings
    except Exception as e:
        return False, f"Ошибка при импорте настроек: {str(e)}", {} 