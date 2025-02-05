# GPT Telegram Bot

Многофункциональный Telegram бот с поддержкой GPT моделей для обработки текста и генерации изображений.

## Основные возможности

- 💬 Текстовый чат с использованием GPT моделей (gpt-4o-mini, gpt-4o, gpt-4, claude-3-sonnet)
- 🎨 Генерация изображений с помощью DALL-E 3
- ⚙️ Настраиваемые параметры для каждой модели
- 📊 Управление контекстом и историей диалога
- 🔐 Система разрешений пользователей

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/yourusername/gpt-telegram-bot.git
cd gpt-telegram-bot
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Создайте файл `.env` на основе `.env.example` и заполните необходимые переменные окружения:
```bash
cp .env.example .env
```

4. Настройте переменные окружения в файле `.env`:
- `TELEGRAM_TOKEN` - токен вашего Telegram бота
- `OPENAI_API_KEY` - ключ API OpenAI
- Другие опциональные настройки

## Запуск

```bash
python main.py
```

## Команды бота

- `/start` - Начать работу с ботом
- `/help` - Показать справку по командам
- `/settings` - Настройки моделей и параметров
- `/current_settings` - Показать текущие настройки
- `/clear` - Очистить историю диалога

## Работа с изображениями

### Генерация новых изображений
Чтобы создать новое изображение, просто отправьте боту текстовое сообщение, начинающееся с `/image` или `/img`, за которым следует описание желаемого изображения. Например:
```
/image нарисуй красивый закат на море с пальмами
```

### Редактирование существующих изображений
Чтобы изменить существующее изображение:
1. Отправьте боту изображение
2. Добавьте к нему описание желаемых изменений в подписи к изображению
3. Бот создаст новое изображение на основе вашего с учетом указанных изменений

Например, отправьте фотографию пляжа с подписью "добавь на этот пляж пальмы и закат".

## Настройка моделей

### Текстовые модели
- gpt-4o-mini (по умолчанию)
- gpt-4o
- gpt-4
- claude-3-sonnet

### Параметры
- Temperature: 0.0 - 2.0
- Max Tokens: 100 - 4000

## Развертывание

Бот готов к развертыванию на платформе Railway.app. Все необходимые файлы конфигурации включены в репозиторий.

## Безопасность

- Поддержка списка разрешенных пользователей
- Ограничение максимального количества токенов
- Безопасное хранение API ключей через переменные окружения

## Логирование

Расширенное логирование может быть включено установкой `DEBUG=true` в файле `.env`

## Лицензия

MIT

## Автор

Ваше имя 

# Model Settings
DEFAULT_TEXT_MODEL=gpt-4o-mini
DEFAULT_IMAGE_MODEL=dall-e-3 