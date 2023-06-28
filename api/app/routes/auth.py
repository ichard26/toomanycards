# Referenced resources:
# - https://jwt.io/introduction

from datetime import datetime, timedelta, timezone
from typing_extensions import Annotated, Final

from fastapi import APIRouter, Depends, Form, HTTPException, Query, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from .. import dependencies as deps
from ..constants import AUTH_ALGORITHM, AUTH_SECRET_KEY
from ..database import db
from ..models import User, get_user_from_db

ACCESS_TOKEN_EXPIRE_MINUTES: Final = 60 * 1

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
router = APIRouter(tags=["auth"])


class Token(BaseModel):
    access_token: str
    token_type: str


def authenticate_user(username: str, password: str):
    user = get_user_from_db(username)
    if user is None:
        return False
    if not pwd_context.verify(password, user.hashed_password):
        return False

    return user


def create_access_token(data: dict, expires_delta: timedelta) -> str:
    to_encode = data.copy()
    to_encode.update({"exp": datetime.now(timezone.utc) + expires_delta})
    return jwt.encode(to_encode, AUTH_SECRET_KEY, algorithm=AUTH_ALGORITHM)


def login(username: str, password: str):
    user = authenticate_user(username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/signup", status_code=201, response_model=Token)
async def create_new_user(
    username: Annotated[str, Form(max_length=20, regex=r"^[a-zA-Z\.]+$")],
    password: Annotated[str, Form()],
    full_name: Annotated[str, Form()],
    challenge: Annotated[int, Query()],
) -> Token:
    if challenge != 26:
        raise HTTPException(status_code=400, detail="Challenge failed (should be integer 26).")

    users = db.get("users")
    if username in users:
        raise HTTPException(status_code=400, detail="Username already exists!")

    users[username] = {
        "username": username,
        "full_name": full_name,
        "is_admin": False,
        "decks": [],
        "hashed_password": pwd_context.hash(password),
    }

    token = login(username, password)
    db.commit()
    return token


@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    return login(form_data.username, form_data.password)


@router.get("/user/{username}")
async def get_user(actor: deps.SignedInUser, user: deps.ExistingUser) -> User:
    if user.username != actor.username and not actor.is_admin:
        raise HTTPException(status_code=403, detail="Resource does not belong to you.")

    return user


@router.delete("/user/{username}", status_code=204)
async def delete_user(actor: deps.SignedInUser, user: deps.ExistingUser) -> None:
    """Delete user from DB, not including owned decks."""
    if user.username != actor.username and not actor.is_admin:
        raise HTTPException(status_code=403, detail="Resource does not belong to you.")

    users = db.get("users")
    del users[user.username]
    db.commit()
