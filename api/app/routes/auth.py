# Referenced resources:
# - https://jwt.io/introduction
# - https://passlib.readthedocs.io/en/stable/

from datetime import datetime, timedelta, timezone
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Query, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt as jwtlib
from passlib.context import CryptContext
from pydantic import BaseModel

from .. import dependencies as deps
from ..constants import AUTH_ALGORITHM, AUTH_SECRET_KEY, AUTH_TOKEN_EXPIRE_MINUTES
from ..models import User
from ..utils import current_datetime_stamp

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
    username: str,
    expires_delta: timedelta = timedelta(minutes=AUTH_TOKEN_EXPIRE_MINUTES)
) -> Token:
    to_encode = {"sub": username, "exp": datetime.now(timezone.utc) + expires_delta}
    jwt = jwtlib.encode(to_encode, AUTH_SECRET_KEY, algorithm=AUTH_ALGORITHM)
    return Token(access_token=jwt, token_type="bearer")


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
        "created_at": current_datetime_stamp(),
    }
    db.execute("""
        INSERT INTO users (username, hashed_password, full_name, is_admin, created_at)
        VALUES (:username, :password, :full_name, :is_admin, :created_at);
    """, data)
    token = create_access_token(username)
    db.commit()
    return token


@router.post("/login")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: deps.DBConnection,
) -> Token:
    if authenticate_user(form_data.username, form_data.password, db):
        return create_access_token(form_data.username)

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
