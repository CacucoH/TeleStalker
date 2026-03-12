# 🕵️‍♂️ TeleStalker

[🇷🇺 Русская версия README](./README.md)

## 📌 Description

**TeleStalker** is an automated Telegram OSINT tool. It recursively parses a target channel and its connected chats to:

- Find users;
- Search for all-time comments by specific users;
- Attempt to reveal sensitive data (e.g., **phone numbers**) if possible.

⚠️ This tool is intended **for educational and research purposes only**. The author takes no responsibility for misuse.

## IMPORTANT

If something went wrong with auth process, remove all contents from `session/` directory and re-run programm


## Installation

### Linux
```bash
git clone https://github.com/CacucoH/teleStalker.git
cd teleStalker
poetry install
```

### Windows
`.exe` version coming soon, for now, run from source:
```cmd
git clone https://github.com/CacucoH/teleStalker.git
cd teleStalker
poetry install
```

## ⚙️ Configuration

Before running the program, you must provide your own Telegram API credentials:

1. Go to https://my.telegram.org
2. Log in and create an application
3. Copy the `api_id` and `api_hash`
4. Create or edit the `example.env` file in the `./config/` directory:

```env
API_ID=your_api_id
API_HASH=your_api_hash
name = your_app_name
```

5. And finally rename `example.env` to `.env`

🚨 The program will not work without valid API credentials

## 🛠️ Usage
```bash
poetry run python3 src/telestalker/main.py -c <channel> [options]
```
#### Arguments:

| Argument                  | Description                                                                                 |
| ------------------------- | ------------------------------------------------------------------------------------------- |
| `-c`, `--channel`         | **Required**. Target channel ID or username (without `@`)                                   |
| `-u`, `--users`           | Usernames or IDs to search comments for (space-separated, no `@`)                           |
| `-r`, `--recursion-depth` | In-channel search recursion depth (default: `1`). Recommended: `2-3` to observe subchannels |
| `-e`, `--exclude`         | Usernames to exclude from scan (space-separated, no `@`)                                    |
| `-q`, `--qr`              | Use QR code for login. Use this method if you cannot receive Telegram auth codes            |

## ⛔ Telegram API Limits

Telegram allows **only 200 API requests per day**.
- This tool is **optimized** to send as few requests as possible
- If you see an error like:
```
A wait of 82696 seconds is required (caused by ResolveUsernameRequest)
```
It means the API quota is exhausted. You must **wait the specified time** to continue

>[!important]
>⚠️ Improper use (e.g., running while quota is blocked) **may result in account freeze or ban**. Use at your own risk
