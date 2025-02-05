# GPT Telegram Бот

Многофункциональный Telegram бот с поддержкой обработки текста, изображений и голоса, использующий API OpenAI.

## Возможности

- ✨ Обработка текстовых сообщений с использованием GPT
- 🖼️ Генерация и обработка изображений
- 🎤 Голосовой ввод и вывод
- 📝 Поддержка тредов и истории сообщений
- ⚙️ Настраиваемые параметры моделей
- 🔄 Потоковый режим ответов
- 👥 Работа в группах

## Установка

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd gpt-telegram-bot
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Создайте файл `.env` на основе `.env.example`:
```bash
cp .env.example .env
```

4. Заполните необходимые переменные окружения в файле `.env`:
- `TELEGRAM_BOT_TOKEN` - токен вашего Telegram бота
- `OPENAI_API_KEY` - ключ API OpenAI
- Другие настройки по необходимости

## Запуск

Локально:
```bash
python main.py
```

На Railway.app:
1. Подключите репозиторий к Railway
2. Установите переменные окружения
3. Деплой произойдет автоматически

## Использование

### Основные команды

- `/start` - Начало работы с ботом
- `/settings` - Панель настроек
- `/clear_history` - Очистка истории сообщений

### Настройка параметров

#### Текстовая модель
- URL API
- Выбор модели
- Температура (0-1)
- Максимальное количество токенов

#### Модель изображений
- URL API
- Выбор модели
- Размер изображения
- Качество
- Стиль
- HDR

#### Голосовая модель
- Язык
- Акцент
- Скорость речи

## Разработка

### Структура проекта

```
/gpt-telegram-bot
│
├── main.py          # Точка входа
├── bot.py           # Основная логика бота
├── settings.py      # Управление настройками
├── handlers.py      # Обработчики сообщений
├── utils.py         # Вспомогательные функции
├── logger.py        # Настройки логирования
├── requirements.txt # Зависимости
├── railway.json     # Конфигурация Railway.app
└── Procfile        # Конфигурация запуска
```

### Отладка

Для включения подробного логирования установите `DEBUG=True` в `.env` файле.

Логи сохраняются в директории `logs/` в формате JSON с временными метками.

## Безопасность

- Поддержка списка разрешенных пользователей
- Ограничение доступа к командам администратора
- Безопасное хранение настроек
- Валидация пользовательского ввода

## Развертывание

Бот оптимизирован для развертывания на платформе Railway.app:

1. Подключите GitHub репозиторий к Railway
2. Настройте переменные окружения
3. Railway автоматически развернет приложение

## Поддержка

При возникновении проблем:
1. Проверьте логи в директории `logs/`
2. Убедитесь в правильности настроек в `.env`
3. Проверьте доступность API сервисов

## Лицензия

MIT 