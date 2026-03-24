from __future__ import annotations

from typing import List, Optional, Tuple

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from db import Database
from keyboards import MAIN_MENU_BUTTONS, main_menu_keyboard, store_items_keyboard, stores_keyboard

router = Router()

DB: Optional[Database] = None
ALLOWED_USER_IDS: set[int] = set()


def setup_handlers(db: Database, allowed_user_ids: set[int]) -> None:
    global DB, ALLOWED_USER_IDS
    DB = db
    ALLOWED_USER_IDS = allowed_user_ids


def is_allowed(user_id: Optional[int]) -> bool:
    return bool(user_id and user_id in ALLOWED_USER_IDS)


def parse_item_input(text: str) -> Tuple[str, List[str]]:
    if "|" not in text:
        raise ValueError

    raw_title, raw_stores = text.split("|", maxsplit=1)
    title = raw_title.strip()
    stores = []
    seen = set()

    for store in raw_stores.split(","):
        normalized = " ".join(store.strip().split())
        if not normalized:
            continue
        key = normalized.casefold()
        if key in seen:
            continue
        seen.add(key)
        stores.append(normalized)

    if not title or not stores:
        raise ValueError

    return title, stores


def user_display_name(message: Message) -> str:
    user = message.from_user
    if user is None:
        return "Unknown"
    return user.full_name or user.username or str(user.id)


def bought_display_name(user_id: Optional[int]) -> str:
    return str(user_id) if user_id is not None else "Unknown"


@router.message(F.text == "/start")
async def start(message: Message) -> None:
    if not is_allowed(message.from_user.id if message.from_user else None):
        await message.answer("Sorry, you are not allowed to use this bot.")
        return

    await message.answer(
        "Shared shopping list bot is ready.\n"
        "Send item as: item name | store1, store2",
        reply_markup=main_menu_keyboard(),
    )


@router.message(F.text == "Add item")
async def add_item_help(message: Message) -> None:
    if not is_allowed(message.from_user.id if message.from_user else None):
        return
    await message.answer("Send item in this format:\nitem name | store1, store2")


@router.message(F.text == "Stores")
async def stores(message: Message) -> None:
    if not is_allowed(message.from_user.id if message.from_user else None):
        return

    assert DB is not None
    store_rows = DB.get_stores_with_active_items()
    if not store_rows:
        await message.answer("No stores with active items right now.")
        return

    payload = [{"id": row["id"], "name": row["name"]} for row in store_rows]
    await message.answer("Choose a store:", reply_markup=stores_keyboard(payload))


@router.callback_query(F.data.startswith("store:"))
async def store_view(callback: CallbackQuery) -> None:
    if not is_allowed(callback.from_user.id if callback.from_user else None):
        await callback.answer("Not allowed", show_alert=True)
        return

    assert DB is not None
    store_id = int(callback.data.split(":", maxsplit=1)[1])
    store_name = DB.get_store_name(store_id)
    if not store_name:
        await callback.answer("Store not found", show_alert=True)
        return

    items = DB.get_active_items_for_store(store_id)
    if not items:
        await callback.message.edit_text(f"{store_name}: no active items.")
        await callback.answer()
        return

    lines = [f"🛒 <b>{store_name}</b>"]
    item_payload = []
    for row in items:
        lines.append(f"• {row['title']} (added by {row['created_by_name']})")
        item_payload.append({"id": row["id"], "title": row["title"]})

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=store_items_keyboard(item_payload, store_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("buy:"))
async def mark_bought(callback: CallbackQuery) -> None:
    if not is_allowed(callback.from_user.id if callback.from_user else None):
        await callback.answer("Not allowed", show_alert=True)
        return

    assert DB is not None
    _, item_id_str, store_id_str = callback.data.split(":", maxsplit=2)
    item_id = int(item_id_str)
    store_id = int(store_id_str)

    changed = DB.mark_item_bought(item_id, callback.from_user.id)
    if not changed:
        await callback.answer("Already bought or unavailable", show_alert=False)

    store_name = DB.get_store_name(store_id) or "Store"
    items = DB.get_active_items_for_store(store_id)

    if not items:
        await callback.message.edit_text(f"{store_name}: no active items.")
        await callback.answer("Updated")
        return

    lines = [f"🛒 <b>{store_name}</b>"]
    item_payload = []
    for row in items:
        lines.append(f"• {row['title']} (added by {row['created_by_name']})")
        item_payload.append({"id": row["id"], "title": row["title"]})

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=store_items_keyboard(item_payload, store_id),
    )
    await callback.answer("Updated")


@router.message(F.text == "All active items")
async def all_active_items(message: Message) -> None:
    if not is_allowed(message.from_user.id if message.from_user else None):
        return

    assert DB is not None
    rows = DB.get_all_active_items()
    if not rows:
        await message.answer("No active items.")
        return

    lines = ["📝 <b>All active items</b>"]
    for row in rows:
        lines.append(f"• {row['title']} — [{row['stores']}] (added by {row['created_by_name']})")

    await message.answer("\n".join(lines))


@router.message(F.text == "Bought items")
async def bought_items(message: Message) -> None:
    if not is_allowed(message.from_user.id if message.from_user else None):
        return

    assert DB is not None
    rows = DB.get_recent_bought_items(limit=30)
    if not rows:
        await message.answer("No bought items yet.")
        return

    lines = ["✅ <b>Recently bought</b>"]
    for row in rows:
        buyer = bought_display_name(row["bought_by_user_id"])
        lines.append(
            f"• {row['title']} — [{row['stores']}] | added by {row['created_by_name']} | bought by {buyer}"
        )

    await message.answer("\n".join(lines))


@router.message(F.text)
async def text_fallback(message: Message) -> None:
    if not is_allowed(message.from_user.id if message.from_user else None):
        return

    if message.text in MAIN_MENU_BUTTONS:
        return

    assert DB is not None

    try:
        title, stores = parse_item_input(message.text)
    except ValueError:
        await message.answer(
            "Invalid format. Use:\n"
            "item name | store1, store2"
        )
        return

    item_id = DB.add_item(
        title=title,
        created_by_user_id=message.from_user.id,
        created_by_name=user_display_name(message),
        store_names=stores,
    )

    await message.answer(
        f"Added item #{item_id}: {title}\nStores: {', '.join(stores)}",
        reply_markup=main_menu_keyboard(),
    )
