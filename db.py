import sqlite3
from datetime import datetime, timezone
from typing import Iterable, List, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Database:
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

    def init(self) -> None:
        with self.conn:
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    created_by_user_id INTEGER NOT NULL,
                    created_by_name TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('active', 'bought')),
                    created_at TEXT NOT NULL,
                    bought_at TEXT,
                    bought_by_user_id INTEGER
                )
                """
            )
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS stores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE
                )
                """
            )
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS item_stores (
                    item_id INTEGER NOT NULL,
                    store_id INTEGER NOT NULL,
                    PRIMARY KEY (item_id, store_id),
                    FOREIGN KEY (item_id) REFERENCES items(id),
                    FOREIGN KEY (store_id) REFERENCES stores(id)
                )
                """
            )

    def get_or_create_store(self, store_name: str) -> int:
        row = self.conn.execute("SELECT id FROM stores WHERE name = ?", (store_name,)).fetchone()
        if row:
            return int(row["id"])

        with self.conn:
            cur = self.conn.execute("INSERT INTO stores(name) VALUES(?)", (store_name,))
            return int(cur.lastrowid)

    def add_item(
        self,
        title: str,
        created_by_user_id: int,
        created_by_name: str,
        store_names: Iterable[str],
    ) -> int:
        with self.conn:
            cur = self.conn.execute(
                """
                INSERT INTO items(title, created_by_user_id, created_by_name, status, created_at)
                VALUES(?, ?, ?, 'active', ?)
                """,
                (title, created_by_user_id, created_by_name, utc_now_iso()),
            )
            item_id = int(cur.lastrowid)

            for store_name in store_names:
                store_id = self.get_or_create_store(store_name)
                self.conn.execute(
                    "INSERT OR IGNORE INTO item_stores(item_id, store_id) VALUES(?, ?)",
                    (item_id, store_id),
                )

        return item_id

    def get_stores_with_active_items(self) -> List[sqlite3.Row]:
        return list(
            self.conn.execute(
                """
                SELECT s.id, s.name
                FROM stores s
                JOIN item_stores ist ON ist.store_id = s.id
                JOIN items i ON i.id = ist.item_id
                WHERE i.status = 'active'
                GROUP BY s.id, s.name
                ORDER BY s.name COLLATE NOCASE
                """
            )
        )

    def get_active_items_for_store(self, store_id: int) -> List[sqlite3.Row]:
        return list(
            self.conn.execute(
                """
                SELECT i.id, i.title, i.created_by_name
                FROM items i
                JOIN item_stores ist ON ist.item_id = i.id
                WHERE ist.store_id = ? AND i.status = 'active'
                ORDER BY i.created_at ASC
                """,
                (store_id,),
            )
        )

    def get_store_name(self, store_id: int) -> Optional[str]:
        row = self.conn.execute("SELECT name FROM stores WHERE id = ?", (store_id,)).fetchone()
        return row["name"] if row else None

    def mark_item_bought(self, item_id: int, bought_by_user_id: int) -> bool:
        with self.conn:
            cur = self.conn.execute(
                """
                UPDATE items
                SET status = 'bought', bought_at = ?, bought_by_user_id = ?
                WHERE id = ? AND status = 'active'
                """,
                (utc_now_iso(), bought_by_user_id, item_id),
            )
            return cur.rowcount > 0

    def get_all_active_items(self) -> List[sqlite3.Row]:
        return list(
            self.conn.execute(
                """
                SELECT
                    i.id,
                    i.title,
                    i.created_by_name,
                    GROUP_CONCAT(s.name, ', ') AS stores
                FROM items i
                JOIN item_stores ist ON ist.item_id = i.id
                JOIN stores s ON s.id = ist.store_id
                WHERE i.status = 'active'
                GROUP BY i.id, i.title, i.created_by_name
                ORDER BY i.created_at ASC
                """
            )
        )

    def get_recent_bought_items(self, limit: int = 20) -> List[sqlite3.Row]:
        return list(
            self.conn.execute(
                """
                SELECT
                    i.id,
                    i.title,
                    i.created_by_name,
                    i.bought_by_user_id,
                    i.bought_at,
                    GROUP_CONCAT(s.name, ', ') AS stores
                FROM items i
                JOIN item_stores ist ON ist.item_id = i.id
                JOIN stores s ON s.id = ist.store_id
                WHERE i.status = 'bought'
                GROUP BY i.id, i.title, i.created_by_name, i.bought_by_user_id, i.bought_at
                ORDER BY i.bought_at DESC
                LIMIT ?
                """,
                (limit,),
            )
        )
