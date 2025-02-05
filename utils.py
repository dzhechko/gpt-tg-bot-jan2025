import openai
import logging
import requests
import os
import json
from typing import Tuple, Optional, Dict, Any
from logger import log_error

DEBUG = True  # Флаг отладки, можно переключать для вывода отладочной информации

def stream_chat_completion(user_message, model="gpt-4o-mini"):
    """
    Функция для реализации streaming chat completion с использованием OpenAI API.
    Отправляем запрос и обрабатываем потоковые ответы.
    """
    try:
        # Отправляем запрос с параметром stream=True
        response = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "user", "content": user_message}],
            stream=True
        )
        # Обрабатываем потоковый ответ по частям
        for chunk in response:
            delta = chunk.get("choices", [{}])[0].get("delta", {})
            content = delta.get("content")
            if content:
                print(content, end="", flush=True)
        print()  # Перевод строки после завершения ответа
    except Exception as e:
        logging.error("Ошибка в stream_chat_completion: %s", str(e))

def validate_temperature(value: Any) -> Tuple[bool, float | str]:
    """
    Валидация значения температуры для модели.
    
    Args:
        value: Значение для проверки
        
    Returns:
        Tuple[bool, Union[float, str]]: (успех, значение/сообщение об ошибке)
    """
    try:
        val = float(value)
        if 0 <= val <= 1:
            return True, val
        else:
            return False, "Значение температуры должно быть от 0 до 1"
    except ValueError:
        return False, "Температура должна быть числом"

def validate_max_tokens(value: Any) -> Tuple[bool, int | str]:
    """
    Валидация максимального количества токенов.
    
    Args:
        value: Значение для проверки
        
    Returns:
        Tuple[bool, Union[int, str]]: (успех, значение/сообщение об ошибке)
    """
    try:
        val = int(value)
        if val >= 150:
            return True, val
        else:
            return False, "Значение должно быть не менее 150 токенов"
    except ValueError:
        return False, "Количество токенов должно быть целым числом"

def create_combined_image(text_prompt, image_url, style="default", size="1024x1024", quality="high", hdr=False):
    """
    Функция для генерации нового изображения на основе текстового и графического ввода.
    Отправляет запрос к API, совместимому с OpenAI, с указанными параметрами.
    """
    api_url = "https://api.example.com/generate-image"  # Замените на реальный URL API
    payload = {
        "text_prompt": text_prompt,
        "image_url": image_url,
        "style": style,
        "size": size,
        "quality": quality,
        "hdr": hdr
    }
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(api_url, json=payload, headers=headers)
        if response.status_code == 200:
            logging.debug("Изображение успешно сгенерировано")
            return response.json()
        else:
            logging.error("Ошибка генерации изображения: %s", response.text)
            return None
    except Exception as e:
        logging.error("Ошибка в create_combined_image: %s", str(e))
        return None

def load_json_file(file_path: str) -> Optional[Dict]:
    """
    Загрузка JSON файла.
    
    Args:
        file_path (str): Путь к файлу
        
    Returns:
        Optional[Dict]: Загруженные данные или None при ошибке
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        log_error('json_load', str(e))
        return None

def save_json_file(data: Dict, file_path: str) -> bool:
    """
    Сохранение данных в JSON файл.
    
    Args:
        data (Dict): Данные для сохранения
        file_path (str): Путь к файлу
        
    Returns:
        bool: True если успешно, False при ошибке
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        log_error('json_save', str(e))
        return False

def ensure_directory(path: str) -> bool:
    """
    Проверка и создание директории, если она не существует.
    
    Args:
        path (str): Путь к директории
        
    Returns:
        bool: True если директория существует или создана, False при ошибке
    """
    try:
        if not os.path.exists(path):
            os.makedirs(path)
        return True
    except Exception as e:
        log_error('directory_create', str(e))
        return False

def download_file(url: str, local_path: str) -> bool:
    """
    Загрузка файла по URL.
    
    Args:
        url (str): URL файла
        local_path (str): Локальный путь для сохранения
        
    Returns:
        bool: True если успешно, False при ошибке
    """
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(local_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
            return True
        return False
    except Exception as e:
        log_error('file_download', str(e))
        return False 