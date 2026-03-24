# Shared Shopping List Telegram Bot (2 users)

Simple MVP Telegram bot for two specific users to share one shopping list.

## Features

- Access limited to two allowed Telegram user IDs
- Add item with stores using format:
  - `item name | store1, store2`
- Stores view shows only stores with active items
- Mark item as bought from store view
- Bought items stay in database with status `bought`
- Views:
  - Stores
  - All active items
  - Bought items

## Tech stack

- Python
- [aiogram](https://docs.aiogram.dev/)
- SQLite

## Project structure

- `bot.py` — app entrypoint
- `config.py` — environment config
- `db.py` — SQLite schema and queries
- `handlers.py` — Telegram handlers and business flow
- `keyboards.py` — reply/inline keyboards
- `requirements.txt`

## Setup

1. Create bot in BotFather and get token.
2. Get Telegram user IDs for the 2 allowed users.
3. Create and activate virtual environment.
4. Install requirements.
5. Set environment variables.
6. Run bot.

### Example

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export BOT_TOKEN="123456:ABCDEF"
export ALLOWED_USER_IDS="111111111,222222222"
# optional:
# export DB_PATH="shopping_bot.db"

python bot.py
```

## BotFather quick instructions

1. Open Telegram and start chat with [@BotFather](https://t.me/BotFather).
2. Run `/newbot`.
3. Choose bot name and username.
4. Copy the HTTP API token and set it as `BOT_TOKEN`.
5. (Optional) Run `/setcommands` and set:

```text
start - Start bot
```

## Notes

- This bot uses only Telegram + local SQLite.
- No external services.
- No extra authentication beyond Telegram user ID allowlist.
