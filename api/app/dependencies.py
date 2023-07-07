import sqlite3
from typing import Annotated

from fastapi import Depends, HTTPException, Path, status
from fastapi.security import OAuth2PasswordBearer

from .database import open_sqlite_connection
from .models import Deck, SignInSession, User, UserInDB
from .utils import utc_now

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def check_for_resource_owner_or_admin(resource_owner, actor: User) -> None:
    if not actor.is_admin and resource_owner != actor.username:
        raise HTTPException(status_code=403, detail="Resource does not belong to you.")


async def setup_database_connection() -> sqlite3.Connection:
    con = open_sqlite_connection()
    try:
        yield con
    finally:
        con.close()


DBConnection = Annotated[sqlite3.Connection, Depends(setup_database_connection)]


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


async def require_signed_in_user(
    token: Annotated[str, Depends(oauth2_scheme)], db: DBConnection,
) -> UserInDB:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials (invalid or expired session ID)",
        headers={"WWW-Authenticate": "Bearer"},
    )

    row = db.execute("SELECT * FROM sessions WHERE id = ?;", [token]).fetchone()
    if row is None:
        raise credentials_exception

    session = SignInSession(**row)
    if utc_now() > session.expired_at:
        raise credentials_exception

    return db.get_user(session.username)


async def require_admin_user(user: Annotated[UserInDB, Depends(require_signed_in_user)]) -> UserInDB:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Operation requires admin rights.")

    return user


ExistingDeck = Annotated[Deck, Depends(require_existing_deck)]
ExistingUser = Annotated[UserInDB, Depends(require_existing_username)]
SignedInUser = Annotated[UserInDB, Depends(require_signed_in_user)]
SignedInAdmin = Annotated[UserInDB, Depends(require_admin_user)]
