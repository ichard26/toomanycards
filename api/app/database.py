# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import sqlite3
from typing import Optional

import florapi.sqlite
from florapi import flatten, utc_now
from ulid import ULID

from . import constants
from .models import AuthSession, Deck, DeckID, UserInDB, Username

florapi.sqlite.register_adaptors()
sqlite3.register_adapter(ULID, str)


class SQLiteConnection(florapi.sqlite.SQLiteConnection):
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

    def get_auth_session(self, *, access: str = "", refresh: str = "", id: str = "") -> Optional[AuthSession]:
        if sum([bool(access), bool(refresh), bool(id)]) != 1:
            raise ValueError(
                "must specify only one of an access token, refresh token or ULID to search by"
            )

        if access:
            row = self.execute("SELECT * FROM sessions WHERE access_token = ?;", [access]).fetchone()
        if refresh:
            row = self.execute("SELECT * FROM sessions WHERE refresh_token = ?;", [refresh]).fetchone()
        if id:
            row = self.execute("SELECT * FROM sessions WHERE id = ?;", [id]).fetchone()
        return AuthSession(**row) if row else None

    def get_auth_sessions(
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


def open_sqlite_connection() -> SQLiteConnection:
    return florapi.sqlite.open_sqlite_connection(constants.DATABASE_PATH, factory=SQLiteConnection)
