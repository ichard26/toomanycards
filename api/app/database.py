import sqlite3
from datetime import datetime
from typing import Optional

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


def open_sqlite_connection() -> sqlite3.Connection:
    con = sqlite3.connect(constants.DATABASE_PATH, factory=SQLiteConnection)
    con.execute("PRAGMA foreign_keys = ON;")
    con.execute("PRAGMA secure_delete = OFF;")
    con.row_factory = sqlite3.Row
    return con
