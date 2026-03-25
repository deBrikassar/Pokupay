import os
from dataclasses import dataclass
from typing import Set


@dataclass(frozen=True)
class Config:
    bot_token: str
    allowed_user_ids: Set[int]
    db_path: str = "shopping_bot.db"


def _parse_allowed_user_ids(raw: str) -> Set[int]:
    ids: Set[int] = set()
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        ids.add(int(part))
    return ids


def load_config() -> Config:
    bot_token = os.getenv("BOT_TOKEN", "").strip()
    allowed_raw = os.getenv("ALLOWED_USER_IDS", "").strip()
    db_path = os.getenv("DB_PATH", "shopping_bot.db").strip()

    if not bot_token:
        raise ValueError("BOT_TOKEN is required")
    if not allowed_raw:
        raise ValueError("ALLOWED_USER_IDS is required")

    allowed_user_ids = _parse_allowed_user_ids(allowed_raw)
    if not allowed_user_ids:
        raise ValueError("ALLOWED_USER_IDS must contain at least one Telegram user id")

    return Config(bot_token=bot_token, allowed_user_ids=allowed_user_ids, db_path=db_path)
