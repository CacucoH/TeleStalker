# 🕵️‍♂️ TeleStalker

<details open>
<summary><strong>🇷🇺 Русский</strong></summary>
## 📌 Описание

**TeleStalker** — это инструмент автоматического сбора данных  из открытых источников (OSINT) в Telegram. Программа рекурсивно парсит указанный канал и его дочерние чаты (связанные группы/комментарии), чтобы:

- Находить пользователей;
- Искать комментарии заданных юзеров за всё время;
- Раскрывать (если возможно) конфиденциальную информацию, такую как **номер телефона**.

⚠️ Программа предназначена **только для образовательных и исследовательских целей**. Автор не несёт ответственности за её неправомерное использование.

---

## 🚀 Установка

### 🐧 Linux
```bash
git clone https://github.com/CacucoH/teleStalker.git
cd teleStalker
chmod +x install.sh
./install.sh
```

### 🪟 Windows
`.exe` версия в разработке, так что пока можно запускать из исходников:
```cmd
git clone https://github.com/CacucoH/teleStalker.git
cd teleStalker
pip3 install -r requirements.txt
```

## 🛠️ Использование
```bash
python3 main.py -c <канал> [опции]
```

#### Аргументы:

| Аргумент                  | Описание                                                                                        |
| ------------------------- | ----------------------------------------------------------------------------------------------- |
| `-c`, `--channel`         | **Обязательный**. Целевой канал (ID или username без `@`)                                       |
| `-u`, `--users`           | Имена или ID юзеров для поиска комментариев (через пробел)                                      |
| `-r`, `--recursion-depth` | Глубина рекурсии поиска (по умолчанию: `1`). Оптимально: `2-3` для обнаружения дочерних каналов |
| `-e`, `--exclude`         | Исключить юзеров по username (через пробел, без `@`)                                            |

## ⛔ Ограничения Telegram API

Telegram API разрешает **только 200 запросов в сутки**.
- Программа **оптимизирована** для минимального количества запросов.
- Если вы увидите ошибку вида:
```bash
A wait of 82696 seconds is required (caused by ResolveUsernameRequest)
```
— это значит, что достигнут лимит. Нужно **подождать указанное время**, чтобы продолжить.

>[!important]
>⚠️ Попытки обойти это ограничение или запускать скрипт во время блокировки API **могут привести к блокировке вашего аккаунта**. Вы действуете на свой страх и риск.

</details>

<details> <summary><strong>🇬🇧 English</strong></summary>
## 📌 Description

**TeleStalker** is an automated Telegram OSINT tool. It recursively parses a target channel and its connected chats to:

- Find users;
- Search for all-time comments by specific users;
- Attempt to reveal sensitive data (e.g., **phone numbers**) if possible.

⚠️ This tool is intended **for educational and research purposes only**. The author takes no responsibility for misuse.

## 🚀 Installation

### 🐧 Linux
```bash
git clone https://github.com/CacucoH/teleStalker.git
cd teleStalker
chmod +x install.sh
./install.sh
```

### 🪟 Windows
`.exe` version coming soon, for now, run from source::
```cmd
git clone https://github.com/CacucoH/teleStalker.git
cd teleStalker
pip3 install -r requirements.txt
```

## 🛠️ Usage
```bash
python3 teleStalker.py -c <channel> [options]
```
#### Arguments:

| Argument                  | Description                                                                                 |
| ------------------------- | ------------------------------------------------------------------------------------------- |
| `-c`, `--channel`         | **Required**. Target channel ID or username (without `@`)                                   |
| `-u`, `--users`           | Usernames or IDs to search comments for (space-separated, no `@`)                           |
| `-r`, `--recursion-depth` | In-channel search recursion depth (default: `1`). Recommended: `2-3` to observe subchannels |
| `-e`, `--exclude`         | Usernames to exclude from scan (space-separated, no `@`)                                    |

## ⛔ Telegram API Limits

Telegram allows **only 200 API requests per day**.
- This tool is **optimized** to send as few requests as possible.
- If you see an error like:
```
A wait of 82696 seconds is required (caused by ResolveUsernameRequest)
```
It means the API quota is exhausted. You must **wait the specified time** to continue

>[!important]
>⚠️ Improper use (e.g., running while quota is blocked) **may result in account freeze or ban**. Use at your own risk.

</details>