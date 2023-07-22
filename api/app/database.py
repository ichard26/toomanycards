import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from . import constants
from .models import Deck, DeckID, UserInDB, Username
from .utils import flatten


def adapt_datetime_iso(dt: datetime) -> str:
    """Adapt datetime.datetime to a ISO 8601 date."""
    return dt.isoformat()


sqlite3.register_adapter(datetime, adapt_datetime_iso)


class SQLiteConnection(sqlite3.Connection):
    def __init__(self, *args, **kwargs) -> None:
        self.backup_after_commit = False
        self.backup_path: Path
        super().__init__(*args, **kwargs)

    def commit(self) -> None:
        super().commit()
        if self.backup_after_commit:
            backup_db = sqlite3.connect(self.backup_path)
            try:
                self.backup(backup_db)
            finally:
                backup_db.close()

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


def open_sqlite_connection() -> sqlite3.Connection:
    con = sqlite3.connect(constants.DATABASE_PATH, factory=SQLiteConnection)
    con.execute("PRAGMA foreign_keys = ON;")
    con.execute("PRAGMA secure_delete = OFF;")
    con.row_factory = sqlite3.Row
    con.backup_after_commit = constants.DATABASE_BACKUP
    con.backup_path = constants.DATABASE_BACKUP_PATH
    return con
