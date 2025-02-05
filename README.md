# 🤖 GPT Telegram Bot

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=for-the-badge&logo=python)](https://www.python.org/)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-blue?style=for-the-badge&logo=telegram)](https://core.telegram.org/bots)
[![OpenAI](https://img.shields.io/badge/OpenAI-API-412991?style=for-the-badge&logo=openai)](https://openai.com/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Author](https://img.shields.io/badge/Author-@djdim-blue?style=for-the-badge&logo=telegram)](https://t.me/djdim)

Многофункциональный Telegram бот с поддержкой GPT моделей для обработки текста и генерации изображений.

[Основные возможности](#основные-возможности) •
[Установка](#установка) •
[Настройка](#настройка-доступа-к-боту) •
[Команды](#команды-бота) •
[Документация](#административные-функции)

</div>

## 📋 Основные возможности

<details open>
<summary>Список возможностей</summary>

- 💬 Текстовый чат с использованием GPT моделей (gpt-4o-mini, gpt-4o, gpt-4, claude-3-sonnet)
- 🎨 Генерация изображений с помощью DALL-E 3
- ⚙️ Настраиваемые параметры для каждой модели
- 📊 Управление контекстом и историей диалога
- 🔐 Система разрешений пользователей
- 👥 Поддержка работы в группах
- 👑 Административные функции для управления ботом

</details>

## 🚀 Установка

<details>
<summary>Пошаговая инструкция</summary>

1. Клонируйте репозиторий:
```bash
git clone https://github.com/yourusername/gpt-telegram-bot.git
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

4. Настройте переменные окружения в файле `.env`:
- `TELEGRAM_TOKEN` - токен вашего Telegram бота
- `OPENAI_API_KEY` - ключ API OpenAI
- `ALLOWED_USERS` - список разрешенных Telegram ID через запятую
- `ALLOWED_GROUPS` - список разрешенных ID групп через запятую (опционально)
- Другие опциональные настройки

</details>

## 🔒 Настройка доступа к боту

<details>
<summary>Индивидуальный доступ</summary>

Бот поддерживает обязательную систему контроля доступа на основе Telegram ID пользователей. Для работы бота необходимо указать список разрешенных пользователей.

### 🆔 Как получить Telegram ID

1. **Через команду бота**:
   - Отправьте команду `/myid` боту
   - Бот покажет ваш ID, username и имя

2. **Через других ботов**:
   - @userinfobot - отправьте любое сообщение
   - @RawDataBot - показывает подробную информацию
   - @getmyid_bot - специализированный бот для получения ID

3. **Через веб-версию Telegram**:
   - Откройте web.telegram.org
   - Войдите в аккаунт
   - ID можно увидеть в URL при открытии любого чата

</details>

<details>
<summary>Работа в группах</summary>

Бот может работать как в личных чатах, так и в группах. Для использования в группах:

1. **Добавление бота в группу**:
   - Добавьте бота как администратора группы
   - Убедитесь, что у бота есть необходимые права (чтение сообщений, отправка сообщений)

2. **Настройка доступа для групп**:
   - По умолчанию бот работает во всех группах
   - Для ограничения доступа используйте переменную `ALLOWED_GROUPS`
   - ID группы всегда начинается с -100 (например: -100123456789)
   - Получить ID группы можно:
     * Через команду `/myid` в группе
     * Через @getgroupid_bot
     * В URL веб-версии Telegram

3. **Использование бота в группе**:
   - Для работы с текстовой моделью есть два способа:
     * Использовать команду `/gpt ваш_запрос`
     * Упомянуть бота: `@имя_бота ваш_запрос`
   - Для генерации изображений используйте команды `/image` или `/img`
   - Все остальные команды работают как обычно: `/help`, `/myid` и т.д.
   - Бот отвечает только на сообщения с явным обращением к нему

4. **Права пользователей в группах**:
   - Каждый пользователь в группе должен иметь индивидуальный доступ
   - Пользователи без доступа не смогут использовать команды бота
   - Публичные команды (`/start`, `/help`, `/myid`) доступны всем

5. **Пример настройки в .env**:
```
ALLOWED_USERS=123456789,987654321
ALLOWED_GROUPS=-100123456789,-100987654321
```

</details>

## 🛠️ Настройка разрешенных пользователей

<details>
<summary>Пошаговая настройка</summary>

1. В файле `.env` ОБЯЗАТЕЛЬНО добавьте переменную `ALLOWED_USERS` со списком разрешенных ID:
```
ALLOWED_USERS=123456789,987654321,456789123
```

2. Если используете Railway.app:
   - Обязательно добавьте переменную `ALLOWED_USERS` в настройках проекта
   - Укажите список разрешенных ID через запятую

3. Особенности работы:
   - ⚠️ Бот не будет работать, пока не задан список разрешенных пользователей
   - Доступ разрешен ТОЛЬКО пользователям из списка
   - Остальные получат сообщение об отказе в доступе
   - При некорректном формате списка доступ будет запрещен всем

4. Проверка доступа:
   - Проверяется каждый запрос к боту
   - Ведется логирование попыток несанкционированного доступа
   - При отсутствии или некорректности настройки `ALLOWED_USERS` в логах будут предупреждения

</details>

## 📝 Команды бота

<details>
<summary>Список доступных команд</summary>

| Команда | Описание |
|---------|----------|
| `/start` | Начать работу с ботом |
| `/help` | Показать справку по командам |
| `/settings` | Настройки моделей и параметров |
| `/current_settings` | Показать текущие настройки |
| `/clear` | Очистить историю диалога |
| `/myid` | Показать ваш Telegram ID |
| `/gpt` | Отправить запрос к GPT (для групп) |
| `/image` или `/img` | Генерация изображений |

💡 **Примечание**: В личных чатах можно просто отправлять сообщения без команды `/gpt`. В группах используйте `/gpt` или упоминание `@имя_бота` перед сообщением.

</details>

## 🎨 Работа с изображениями

<details>
<summary>Подробная информация</summary>

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

</details>

## ⚙️ Настройка моделей

<details>
<summary>Доступные модели и параметры</summary>

### 🤖 Текстовые модели

| Модель | Описание |
|--------|----------|
| `gpt-4o-mini` | Базовая модель (по умолчанию) |
| `gpt-4o` | Улучшенная модель |
| `gpt-4` | Продвинутая модель |
| `Custom Model` | Пользовательская модель |

### ⚙️ Параметры текстовых моделей

| Параметр | Значение | Описание |
|----------|----------|-----------|
| Temperature | 0.0 - 2.0 | Креативность ответов (0 - наиболее предсказуемые, 2 - наиболее креативные) |
| Max Tokens | 100 - 4000 | Максимальная длина ответа |

### 🎨 Модели изображений

| Модель | Возможности |
|--------|-------------|
| `dall-e-3` | • Высокое качество<br>• Размеры: 1024x1024, 1024x1792, 1792x1024<br>• Поддержка HDR<br>• Стили: natural, vivid |
| `dall-e-2` | • Стандартное качество<br>• Размеры: 256x256, 512x512, 1024x1024 |

</details>

## 🚂 Развертывание

<details>
<summary>Информация о развертывании</summary>

Бот готов к развертыванию на платформе Railway.app. Все необходимые файлы конфигурации включены в репозиторий.

</details>

## 🔐 Безопасность

<details>
<summary>Меры безопасности</summary>

- Поддержка списка разрешенных пользователей через `ALLOWED_USERS`
- Поддержка списка разрешенных групп через `ALLOWED_GROUPS`
- Ограничение максимального количества токенов
- Безопасное хранение API ключей через переменные окружения

</details>

## 📊 Логирование

<details>
<summary>Настройка логирования</summary>

Расширенное логирование может быть включено установкой `DEBUG=true` в файле `.env`

</details>

## 📄 Лицензия

Этот проект распространяется под лицензией MIT. Подробности смотрите в файле [LICENSE](LICENSE).

## 👤 Автор

**Telegram**: [@djdim](https://t.me/djdim)

---

<div align="center">
Made with ❤️ by <a href="https://t.me/djdim">@djdim</a>
</div>

## ⚙️ Настройки по умолчанию

<div align="center">

| 🤖 Текстовая модель | 🎨 Модель изображений |
|:------------------:|:--------------------:|
| `gpt-4o-mini` | `dall-e-3` |

</div>

## Административные функции

### Настройка администраторов

Для использования административных функций необходимо добавить ID администраторов в переменную `ADMIN_USER_IDS` в файле `.env`:
```
ADMIN_USER_IDS=123456789,987654321
```

### Доступные административные команды

#### Управление пользователями
- `/adduser ID` - добавить пользователя в список разрешенных
- `/removeuser ID` - удалить пользователя из списка разрешенных
- `/listusers` - показать список разрешенных пользователей

Особенности работы с пользователями:
1. Список разрешенных пользователей хранится в файле `allowed_users.json`
2. При добавлении/удалении пользователей изменения сохраняются автоматически
3. Команда `/listusers` показывает все ID пользователей, которым разрешен доступ к боту
4. ID пользователя должен быть числом (можно получить через команду `/myid`)

Примеры использования:
```bash
# Добавить пользователя
/adduser 123456789

# Удалить пользователя
/removeuser 123456789

# Посмотреть список пользователей
/listusers
```

Важно: После добавления пользователя убедитесь, что:
- Пользователь существует в Telegram
- ID указан корректно
- Пользователь может отправлять сообщения боту

#### Управление группами
- `/addgroup -100123456789` - добавить группу в список разрешенных
- `/removegroup -100123456789` - удалить группу из списка разрешенных
- `/listgroups` - показать список разрешенных групп

Особенности работы с группами:
1. Список разрешенных групп хранится в файле `allowed_groups.json`
2. ID группы всегда должен начинаться с `-100`
3. Если список групп пуст, бот работает во всех группах
4. При добавлении/удалении групп изменения сохраняются автоматически
5. Команда `/listgroups` показывает все группы, в которых разрешена работа бота

Примеры использования:
```bash
# Добавить группу
/addgroup -100123456789

# Удалить группу
/removegroup -100123456789

# Посмотреть список групп
/listgroups
```

Важно: После добавления группы убедитесь, что:
- Бот добавлен в группу как администратор
- У бота есть необходимые права (чтение и отправка сообщений)
- Пользователи в группе имеют индивидуальный доступ к боту

#### Мониторинг и управление
- `/stats` - показать статистику использования бота
- `/logs` - просмотр последних логов бота
- `/broadcast [сообщение]` - отправить сообщение всем пользователям
- `/restart` - перезапустить бота
- `/maintenance on/off` - включить/выключить режим обслуживания

### Режим обслуживания

Режим обслуживания позволяет временно ограничить доступ к боту для всех пользователей, кроме администраторов. Это полезно при:
- Обновлении бота
- Технических работах
- Устранении неполадок

#### Использование режима обслуживания:
1. Включение: `/maintenance on`
   - Все пользователи получат уведомление о переходе в режим обслуживания
   - Только администраторы смогут использовать бота
   
2. Выключение: `/maintenance off`
   - Все пользователи получат уведомление о возобновлении работы
   - Доступ к боту будет восстановлен для всех разрешенных пользователей

### Мониторинг бота

#### Статистика использования
Команда `/stats` показывает:
- Общее количество пользователей
- Общее количество сообщений
- Время работы бота

#### Просмотр логов
Команда `/logs` позволяет:
- Просматривать последние 50 строк логов
- Получать лог-файл целиком, если логи слишком большие
- Отслеживать ошибки и проблемы в работе бота

#### Массовые уведомления
Команда `/broadcast` позволяет:
- Отправлять важные сообщения всем пользователям
- Информировать о планируемых работах
- Оповещать об обновлениях и изменениях

### Безопасность

- Все административные команды доступны только пользователям из списка `ADMIN_USER_IDS`
- При попытке использования административных команд обычными пользователями они получат сообщение об отказе в доступе
- Все действия администраторов логируются для аудита
- Режим обслуживания защищает бота во время технических работ

### Рекомендации по использованию

1. **Управление пользователями**:
   - Регулярно проверяйте список разрешенных пользователей
   - Удаляйте неактивных пользователей
   - Ведите учет кому и когда был предоставлен доступ

2. **Управление группами**:
   - Проверяйте ID групп перед добавлением (должны начинаться с -100)
   - Убедитесь, что бот имеет необходимые права в группе
   - Регулярно проверяйте активность в группах

3. **Мониторинг**:
   - Регулярно проверяйте статистику использования
   - Следите за логами на предмет ошибок
   - Своевременно реагируйте на проблемы

4. **Режим обслуживания**:
   - Включайте перед началом технических работ
   - Предупреждайте пользователей заранее через `/broadcast`
   - Не забывайте выключать после завершения работ 