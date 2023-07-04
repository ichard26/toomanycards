# Referenced resources:
# - https://jwt.io/introduction
# - https://passlib.readthedocs.io/en/stable/

import logging
import secrets
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, Query, status
from fastapi.security import OAuth2PasswordRequestForm
from passlib.context import CryptContext
from pydantic import BaseModel

from .. import dependencies as deps
from ..constants import AUTH_TOKEN_EXPIRE_DELTA, AUTH_TOKEN_PURGE_DELTA
from ..models import SignInSession, User
from ..utils import utc_now

logger = logging.getLogger(__name__)
passlib_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
router = APIRouter(tags=["auth"])


class Token(BaseModel):
    access_token: str
    token_type: str


def authenticate_user(username: str, password: str, db) -> bool:
    user = db.get_user(username)
    return user and passlib_context.verify(password, user.hashed_password)


def create_access_token(
    username: str, expiry_delta: timedelta, db: deps.DBConnection
) -> Token:
    session_id = secrets.token_hex()
    creation_datetime = utc_now()
    with db:
        db.execute(
            "INSERT INTO sessions(id, username, created_at, expired_at) VALUES(?, ?, ?, ?)",
            (session_id, username, creation_datetime, creation_datetime + expiry_delta)
        )
    return Token(access_token=session_id, token_type="bearer")


async def purge_expired_sessions(purge_delta: timedelta, db: deps.DBConnection) -> None:
    for row in db.execute("SELECT * FROM sessions;"):
        session = SignInSession(**row)
        if (session.expired_at + purge_delta) < utc_now():
            created_at = session.created_at.strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"Purging session ({session.username}) from {created_at} - {session.id}")
            db.execute("DELETE FROM sessions WHERE id = ?;", [session.id])
            db.commit()


@router.post("/signup", status_code=201)
async def create_new_user(
    username: Annotated[str, Form(max_length=20, regex=r"^[a-zA-Z\.]+$")],
    password: Annotated[str, Form()],
    full_name: Annotated[str, Form()],
    challenge: Annotated[int, Query(gt=25, lt=27)],
    db: deps.DBConnection,
) -> Token:
    if db.get_user(username) is not None:
        raise HTTPException(status_code=400, detail="Username already exists!")

    data = {
        "username": username,
        "password": passlib_context.hash(password),
        "full_name": full_name,
        "is_admin": False,
        "created_at": utc_now(),
    }
    db.execute("""
        INSERT INTO users (username, hashed_password, full_name, is_admin, created_at)
        VALUES (:username, :password, :full_name, :is_admin, :created_at);
    """, data)
    token = create_access_token(username, AUTH_TOKEN_EXPIRE_DELTA, db)
    db.commit()
    return token


@router.post("/login")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: deps.DBConnection,
    background_tasks: BackgroundTasks,
) -> Token:
    if authenticate_user(form_data.username, form_data.password, db):
        background_tasks.add_task(purge_expired_sessions, AUTH_TOKEN_PURGE_DELTA, db)
        return create_access_token(form_data.username, AUTH_TOKEN_EXPIRE_DELTA, db)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )


@router.get("/user/{username}")
async def get_user(actor: deps.SignedInUser, user: deps.ExistingUser) -> User:
    deps.check_for_resource_owner_or_admin(user.username, actor)
    return user


@router.delete("/user/{username}")
async def delete_user(actor: deps.SignedInUser, user: deps.ExistingUser, db: deps.DBConnection) -> None:
    """Delete user from DB, not including owned decks."""
    deps.check_for_resource_owner_or_admin(user.username, actor)
    db.execute("DELETE FROM users WHERE username = ?;", [user.username])
    db.commit()
