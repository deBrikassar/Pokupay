from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


MAIN_MENU_BUTTONS = ["Add item", "Stores", "All active items", "Bought items"]


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Add item"), KeyboardButton(text="Stores")],
            [KeyboardButton(text="All active items"), KeyboardButton(text="Bought items")],
        ],
        resize_keyboard=True,
    )


def stores_keyboard(stores: list[dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for store in stores:
        builder.row(
            InlineKeyboardButton(
                text=store["name"],
                callback_data=f"store:{store['id']}",
            )
        )
    return builder.as_markup()


def store_items_keyboard(items: list[dict], store_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for item in items:
        builder.row(
            InlineKeyboardButton(
                text=f"✅ Bought: {item['title']}",
                callback_data=f"buy:{item['id']}:{store_id}",
            )
        )
    return builder.as_markup()
