# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from __future__ import annotations

import sqlite3
from collections.abc import Mapping
from datetime import datetime
from typing import Optional, Sequence

from . import constants
from .models import AuthSession, Deck, DeckID, UserInDB, Username
from .utils import flatten, utc_now


def adapt_datetime_iso(dt: datetime) -> str:
    """Adapt datetime.datetime to a ISO 8601 date."""
    return dt.isoformat()


sqlite3.register_adapter(datetime, adapt_datetime_iso)


class SQLiteConnection(sqlite3.Connection):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def insert(
        self,
        table: str,
        columns_or_values: Sequence[str] | Mapping[str, object],
        values: Sequence[object] | None = None,
    ) -> sqlite3.Cursor:
        if not self._existing_table(table):
            raise sqlite3.DatabaseError(f"table '{table}' does not exist")

        columns_string = ",".join(columns_or_values)
        if isinstance(columns_or_values, Mapping):
            values = columns_or_values
            values_string = ",".join(f":{col}" for col in columns_or_values)
        else:
            values_string = ",".join("?" * len(columns_or_values))
        self.execute(f"INSERT INTO {table}({columns_string}) VALUES({values_string});", values)

    def insert_many(
        self, table: str, columns: Sequence[str], values: Sequence[object]
    ) -> sqlite3.Cursor:
        if not self._existing_table(table):
            raise sqlite3.DatabaseError(f"table '{table}' does not exist")

        columns_string = ",".join(columns)
        values_string = ",".join("?" * len(columns))
        self.executemany(f"INSERT INTO {table}({columns_string}) VALUES({values_string});", values)

    def get_user(self, username: Username) -> Optional[UserInDB]:
        cur = self.execute("SELECT * FROM users WHERE username = ?;", [username])
        if row := cur.fetchone():
            cur = self.execute("SELECT id FROM decks WHERE owner = ?;", [username])
            return UserInDB(**row, decks=flatten(cur))
        else:
            return None

    def get_deck(self, deck_id: DeckID) -> Optional[Deck]:
        cur = self.execute("SELECT * FROM decks WHERE id = ?;", [deck_id])
        if row := cur.fetchone():
            cur = self.execute("SELECT * FROM cards WHERE deck_id = ?;", [deck_id])
            return Deck(**row, cards=list(cur))
        else:
            return None

    def get_sign_in_sessions(
        self, username: Optional[Username], include_expired: bool = True
    ) -> list[AuthSession]:
        if username is not None:
            cur = self.execute("SELECT * FROM sessions WHERE username = ?;", [username])
        else:
            cur = self.execute("SELECT * FROM sessions;")
        sessions = [AuthSession(**row) for row in cur]
        if include_expired:
            return sessions
        else:
            return [s for s in sessions if utc_now() < s.refresh_expiry]

    def _existing_table(self, table: str) -> bool:
        """Check if a table exists in the database."""
        return table in flatten(self.execute("SELECT name FROM sqlite_master WHERE type='table'"))


def open_sqlite_connection() -> sqlite3.Connection:
    con = sqlite3.connect(constants.DATABASE_PATH, factory=SQLiteConnection)
    con.execute("PRAGMA foreign_keys = ON;")
    con.execute("PRAGMA secure_delete = OFF;")
    con.row_factory = sqlite3.Row
    return con
