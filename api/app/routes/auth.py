# Referenced resources:
# - https://jwt.io/introduction

from datetime import datetime, timedelta, timezone

from fastapi import Depends, APIRouter, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from typing_extensions import Annotated, Final

from .. import dependencies as deps
from ..constants import AUTH_SECRET_KEY, AUTH_ALGORITHM
from ..database import db
from ..models import User, UserInDB, get_user_from_db

ACCESS_TOKEN_EXPIRE_MINUTES: Final = 60 * 1


class UserCreationForm(BaseModel):
    username: str
    password: str
    full_name: str
    challenge_answer: int


class Token(BaseModel):
    access_token: str
    token_type: str


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter(tags=["auth"])


def hash_password(password):
    return pwd_context.hash(password)


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


@router.post("/signup", response_model=Token)
async def create_new_user(form_data: UserCreationForm):
    pass


@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    user = authenticate_user(form_data.username, form_data.password)
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


@router.get("/user/{username}")
async def get_user(user: deps.ExistingUser, actor: deps.SignedInUser) -> User:
    if user.username != actor.username and not actor.is_admin:
        raise HTTPException(status_code=403, detail="Resource does not belong to you.")

    return user


@router.delete("/user/{username}", status_code=204)
async def delete_user(user: deps.ExistingUser, actor: deps.SignedInUser) -> None:
    """Delete user from DB, not including owned decks."""
    if user.username != actor.username and not actor.is_admin:
        raise HTTPException(status_code=403, detail="Resource does not belong to you.")
