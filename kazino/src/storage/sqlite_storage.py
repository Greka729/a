from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Tuple


class SQLiteStorage:
    """Minimal scaffold for future migration from JSON to SQLite."""

    def __init__(self, db_path: str = "data/casino.db") -> None:
        Path("data").mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self._migrate()

    def _migrate(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_version (
              version INTEGER NOT NULL
            );
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS user (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              name TEXT NOT NULL,
              locale TEXT NOT NULL DEFAULT 'ru',
              created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS wallet (
              user_id INTEGER NOT NULL,
              balance INTEGER NOT NULL,
              updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
              FOREIGN KEY(user_id) REFERENCES user(id)
            );
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS game_session (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              user_id INTEGER NOT NULL,
              game_id TEXT NOT NULL,
              stake INTEGER NOT NULL,
              payout INTEGER NOT NULL,
              result_json TEXT NOT NULL,
              created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
              FOREIGN KEY(user_id) REFERENCES user(id)
            );
            """
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()


