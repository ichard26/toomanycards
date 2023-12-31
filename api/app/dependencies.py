# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import sqlite3
from typing import Annotated, AsyncIterator, NoReturn, Optional

from fastapi import Depends, HTTPException, Path, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from florapi import utc_now

from .constants import REFRESH_COOKIE_NAME
from .database import SQLiteConnection, open_sqlite_connection
from .models import AuthSession, Card, Deck, User, UserInDB


def check_for_resource_owner_or_admin(resource_owner, actor: User) -> None:
    if not actor.is_admin and resource_owner != actor.username:
        raise HTTPException(status_code=403, detail="Resource does not belong to you.")


def raise_credentials_error() -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials (missing, invalid, or expired access token)",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def setup_database_connection() -> AsyncIterator[sqlite3.Connection]:
    con = open_sqlite_connection()
    try:
        yield con
    finally:
        con.close()


DBConnection = Annotated[SQLiteConnection, Depends(setup_database_connection)]


async def require_existing_username(
    username: Annotated[str, Path(max_length=20)], db: DBConnection
) -> UserInDB:
    if user := db.get_user(username):
        return user

    raise HTTPException(status_code=404, detail="User not found")


async def require_existing_deck(
    deck_id: Annotated[int, Path(ge=1, le=1000)], db: DBConnection
) -> Deck:
    if deck := db.get_deck(deck_id):
        return deck

    raise HTTPException(status_code=404, detail="Deck not found")


async def require_existing_card(card_id: Annotated[str, Path], db: DBConnection) -> Card:
    if row := db.execute("SELECT * FROM cards WHERE id = ?", [card_id]).fetchone():
        return Card(**row), db.get_deck(row["deck_id"])

    raise HTTPException(404, "Card not found")


async def require_access_token(
    token: Annotated[
        Optional[HTTPAuthorizationCredentials], Depends(HTTPBearer(auto_error=False))
    ],
    db: DBConnection,
) -> AuthSession:
    if token is None:
        raise_credentials_error()

    session = db.get_auth_session(access=token.credentials)
    if session is None:
        raise_credentials_error()

    if utc_now() > session.access_expiry:
        raise_credentials_error()

    return session


async def require_signed_in_user(
    session: Annotated[AuthSession, Depends(require_access_token)], db: DBConnection,
) -> UserInDB:
    return db.get_user(session.username)


async def may_have_signed_in_user(
    token: Annotated[
        Optional[HTTPAuthorizationCredentials], Depends(HTTPBearer(auto_error=False))
    ],
    db: DBConnection,
) -> Optional[UserInDB]:
    try:
        session = await require_access_token(token, db)
        return db.get_user(session.username)
    except HTTPException:
        # Fallback to no user if credentials are missing, invalid, or expired.
        return None


async def require_admin_user(user: Annotated[UserInDB, Depends(require_signed_in_user)]) -> UserInDB:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Operation requires admin rights.")

    return user


async def require_refresh_cookie(request: Request, db: DBConnection) -> AuthSession:
    if token := request.cookies.get(REFRESH_COOKIE_NAME):
        if session := db.get_auth_session(refresh=token):
            if utc_now() < session.refresh_expiry:
                return session

    raise HTTPException(401, detail="missing, invalid, or expired refresh cookie")


ExistingCard = Annotated[tuple[Card, Deck], Depends(require_existing_card)]
ExistingDeck = Annotated[Deck, Depends(require_existing_deck)]
ExistingUser = Annotated[UserInDB, Depends(require_existing_username)]
SignedInUser = Annotated[UserInDB, Depends(require_signed_in_user)]
MaybeSignedInUser = Annotated[UserInDB, Depends(may_have_signed_in_user)]
SignedInAdmin = Annotated[UserInDB, Depends(require_admin_user)]
ValidAccessToken = Annotated[AuthSession, Depends(require_access_token)]
ValidRefreshCookie = Annotated[AuthSession, Depends(require_refresh_cookie)]
