"""Local SQLite bootstrap for the native desktop runtime."""
from __future__ import annotations

import sqlite3

from app_paths import SQLITE_PATH


def init_app_db() -> None:
    SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(SQLITE_PATH) as conn:
        conn.execute(
            """
            create table if not exists app_meta (
                key text primary key,
                value text,
                updated_at text default current_timestamp
            )
            """
        )
        conn.execute(
            """
            insert into app_meta(key, value, updated_at)
            values('schema_version', '1', current_timestamp)
            on conflict(key) do update set updated_at=current_timestamp
            """
        )
        conn.commit()
