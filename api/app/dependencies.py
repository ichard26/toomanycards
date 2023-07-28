import sqlite3
from typing import Annotated, AsyncIterator, Optional

from fastapi import Depends, HTTPException, Path, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .constants import REFRESH_COOKIE_NAME
from .database import SQLiteConnection, open_sqlite_connection
from .models import AuthSession, Deck, User, UserInDB
from .utils import utc_now


def check_for_resource_owner_or_admin(resource_owner, actor: User) -> None:
    if not actor.is_admin and resource_owner != actor.username:
        raise HTTPException(status_code=403, detail="Resource does not belong to you.")


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
    deck_id: Annotated[int, Path(ge=1)], db: DBConnection
) -> Deck:
    if deck := db.get_deck(deck_id):
        return deck

    raise HTTPException(status_code=404, detail="Deck not found")


async def require_access_token(
    token: Annotated[
        Optional[HTTPAuthorizationCredentials], Depends(HTTPBearer(auto_error=False))
    ],
    db: DBConnection,
) -> AuthSession:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials (missing, invalid, or expired access token)",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if token is None:
        raise credentials_exception

    row = db.execute("SELECT * FROM sessions WHERE access_token = ?;", [token.credentials]).fetchone()
    if row is None:
        raise credentials_exception

    session = AuthSession(**row)
    if utc_now() > session.access_expiry:
        raise credentials_exception

    return session


async def require_signed_in_user(
    session: Annotated[AuthSession, Depends(require_access_token)], db: DBConnection,
) -> UserInDB:
    return db.get_user(session.username)


async def require_admin_user(user: Annotated[UserInDB, Depends(require_signed_in_user)]) -> UserInDB:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Operation requires admin rights.")

    return user


async def require_refresh_cookie(request: Request, db: DBConnection) -> AuthSession:
    if token := request.cookies.get(REFRESH_COOKIE_NAME):
        if row := db.execute("SELECT * FROM sessions WHERE refresh_token = ?;", [token]).fetchone():
            session = AuthSession(**row)
            if utc_now() < session.refresh_expiry:
                return session

    raise HTTPException(401, detail="missing, invalid, or expired refresh token")


ExistingDeck = Annotated[Deck, Depends(require_existing_deck)]
ExistingUser = Annotated[UserInDB, Depends(require_existing_username)]
SignedInUser = Annotated[UserInDB, Depends(require_signed_in_user)]
SignedInAdmin = Annotated[UserInDB, Depends(require_admin_user)]
ValidAccessToken = Annotated[AuthSession, Depends(require_access_token)]
ValidRefreshCookie = Annotated[AuthSession, Depends(require_refresh_cookie)]
