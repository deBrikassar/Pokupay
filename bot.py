import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

from config import load_config
from db import Database
from handlers import router, setup_handlers


async def main() -> None:
    config = load_config()

    db = Database(config.db_path)
    db.init()

    setup_handlers(db=db, allowed_user_ids=config.allowed_user_ids)

    bot = Bot(token=config.bot_token, parse_mode=ParseMode.HTML)
    dp = Dispatcher()
    dp.include_router(router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
