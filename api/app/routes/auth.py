# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import logging
import secrets
from datetime import datetime, timedelta
from typing import Annotated, Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Form,
    Header,
    HTTPException,
    Query,
    Request,
    Response,
    status,
)
from florapi import utc_now
from florapi.security import RateLimiter
from passlib.context import CryptContext
from pydantic import BaseModel

from .. import dependencies as deps
from ..constants import (
    ACCESS_TOKEN_LIFETIME,
    ALLOW_NEW_USERS,
    MAX_SESSIONS,
    REFRESH_COOKIE_NAME,
    SESSION_LIFETIME,
    SESSION_PURGE_DELTA,
    TLS_ENABLED,
)
from ..models import AuthSession, User
from ..models import modelfields as MF
from ..vendor.tsidpy import TSID

AccessToken = str

logger = logging.getLogger(__name__)
passlib_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
router = APIRouter(tags=["auth"])


class ExtraSanitizedAuthSession(BaseModel):
    id: str
    access_expiry: datetime
    refresh_expiry: datetime


class SanitizedAuthSession(ExtraSanitizedAuthSession):
    access_token: str


class SignInResponse(BaseModel):
    session: SanitizedAuthSession
    user: User


class UserUpdateTemplate(BaseModel):
    username: str = MF.Username(default="")
    display_name: str = MF.DisplayName(default="")
    # TODO: find a way to require password reauthentication for "sensitive" endpoints.
    password: str = MF.Password(default="")


def authenticate_user(username: str, password: str, db) -> Optional[User]:
    user = db.get_user(username)
    if user and passlib_context.verify(password, user.hashed_password):
        return user
    return None


def add_auth_session(
    db: deps.DBConnection,
    username: str,
    access_lifetime: timedelta = ACCESS_TOKEN_LIFETIME,
    session_lifetime: timedelta = SESSION_LIFETIME,
) -> AuthSession:
    """Generate an access token w/ a refresh token and add to the DB.

    The access and refresh tokens are generated securely using a CSPRNG.
    """
    # FIXME: retry session generation on collisions...
    access_token = "A:" + secrets.token_hex()
    access_expiry = utc_now() + access_lifetime
    refresh_token = "R:" + secrets.token_hex()
    refresh_expiry = utc_now() + session_lifetime
    with db:
        db.insert(
            "sessions",
            ("id", "username", "refresh_token", "refresh_expiry", "access_token", "access_expiry", "created_at"),
            (TSID.create(), username, refresh_token, refresh_expiry, access_token, access_expiry, utc_now()),
        )
    return db.get_auth_session(access=access_token)


def refresh_auth_session(
    db: deps.DBConnection,
    refresh_token: str,
    access_lifetime: timedelta = ACCESS_TOKEN_LIFETIME
) -> AccessToken:
    """Regenerate a new access token for a pre-existing session (refresh token)."""
    access_token = "A:" + secrets.token_hex()
    access_expiry = utc_now() + access_lifetime
    with db:
        db.update(
            "sessions", {"access_token": access_token, "access_expiry": access_expiry},
            where={"refresh_token": refresh_token}
        )
    return access_token


async def purge_expired_sessions(purge_delta: timedelta, db: deps.DBConnection) -> None:
    with db:
        for session in db.get_auth_sessions(username=None):
            if (session.refresh_expiry + purge_delta) < utc_now():
                id = session.refresh_token
                created_at = session.created_at.strftime("%Y-%m-%d %H:%M:%S")
                logger.info(f"Purging session ({session.username}) from {created_at} - {id}")
                db.delete("sessions", {"refresh_token": id})


@router.post("/signup", status_code=201)
async def create_new_user(
    username: Annotated[str, Form(**MF.Username)],
    password: Annotated[str, Form(**MF.Password)],
    display_name: Annotated[str, Form(**MF.DisplayName)],
    challenge: Annotated[int, Query(gt=25, lt=27)],
    db: deps.DBConnection,
    request: Request,
    response: Response,
    background_tasks: BackgroundTasks,
) -> AccessToken:
    if not ALLOW_NEW_USERS:
        raise HTTPException(403, "User sign-ups are currently disabled")

    limiter = RateLimiter("signup", {RateLimiter.DAY: 5}, db)
    if limiter.update_and_check(request.client.host):
        raise HTTPException(429)

    username = username.lower()
    if db.get_user(username) is not None:
        raise HTTPException(status_code=400, detail="Username already exists!")

    with db:
        db.insert("users", {
            "username": username,
            "hashed_password": passlib_context.hash(password),
            "display_name": display_name,
            "is_admin": False,
            "created_at": utc_now(),
        })
    return await login_for_access_token(
        username, password, "no-csrf-here", db, request, response, background_tasks
    )


@router.post("/login")
async def login_for_access_token(
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
    x_csrf_protection: Annotated[str, Header()],
    db: deps.DBConnection,
    request: Request,
    response: Response,
    background_tasks: BackgroundTasks,
) -> SignInResponse:
    """On sucessful login, return a new access token and set its associated (session)
    refresh cookie.

    The access token **must** be provided (in the `Authorization` header) for endpoints
    requiring authentication. It has a limited lifespan after which a client must request
    a new access token by calling `/session/refresh`.
    """
    limiter = RateLimiter("login:failed-attempt", {RateLimiter.DAY: 10}, db)
    if limiter.should_block(request.client.host) or limiter.should_block(username):
        raise HTTPException(429)

    if user := authenticate_user(username, password, db):
        if len(db.get_auth_sessions(username, include_expired=False)) >= MAX_SESSIONS:
            raise HTTPException(429, detail="Too many registered sessions")

        background_tasks.add_task(purge_expired_sessions, SESSION_PURGE_DELTA, db)
        session = add_auth_session(db, username)
        response.set_cookie(
            REFRESH_COOKIE_NAME,
            session.refresh_token,
            secure=TLS_ENABLED,
            httponly=True,
            samesite="lax",
            max_age=int(SESSION_LIFETIME.total_seconds()),
        )
        return SignInResponse(session=session, user=user)

    limiter.update(request.client.host)
    limiter.update(username)
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )


@router.post("/logout")
async def logout_session(
    actor: deps.SignedInUser, session: deps.ValidAccessToken, db: deps.DBConnection, response: Response
) -> None:
    """Revoke the current login session (as per the access token).

    This endpoint is similar to `/session/revoke/`, however the `Clear-Site-Data` header
    is returned to also purge client side data.
    """
    # XXX: browser support for this header is quite limited, *sigh*
    # https://bugs.chromium.org/p/chromium/issues/detail?id=898503
    response.headers["Clear-Site-Data"] = '"cookies", "storage"'
    with db:
        db.delete("sessions", {"access_token": session.access_token})


@router.post("/session/refresh")
async def refresh_session(session: deps.ValidRefreshCookie, db: deps.DBConnection) -> SignInResponse:
    """Generate a new access token for the current login session (as per the refresh cookie)."""
    access_token = refresh_auth_session(db, session.refresh_token)
    return SignInResponse(
        session=db.get_auth_session(access=access_token),
        user=db.get_user(session.username)
    )


@router.get("/session/list")
async def list_sessions(
    actor: deps.SignedInUser, db: deps.DBConnection
) -> list[ExtraSanitizedAuthSession]:
    return db.get_auth_sessions(username=actor.username)


@router.delete("/session/revoke/{id}")
async def revoke_session(actor: deps.SignedInUser, id: str, db: deps.DBConnection) -> None:
    """Revoke (delete) a login session by ID."""
    session = db.get_auth_session(tsid=id)
    if session is None:
        raise HTTPException(404, "Session not found")

    deps.check_for_resource_owner_or_admin(session.username, actor)
    with db:
        db.delete("sessions", {"access_token": session.access_token})


@router.get("/user")
async def get_current_user(actor: deps.SignedInUser) -> User:
    return actor


@router.get("/user/{username}")
async def get_user(actor: deps.SignedInUser, user: deps.ExistingUser) -> User:
    deps.check_for_resource_owner_or_admin(user.username, actor)
    return user


@router.patch("/user/{username}")
async def update_user(
    actor: deps.SignedInUser,
    user: deps.ExistingUser,
    template: UserUpdateTemplate,
    db: deps.DBConnection,
) -> None:
    deps.check_for_resource_owner_or_admin(user.username, actor)
    update_data = template.dict(exclude_unset=True)
    if password := update_data.get("password"):
        update_data["hashed_password"] = passlib_context.hash(password)
    new_user = user.copy(update=update_data)
    with db:
        db.update(
            "users",
            {
                "username": new_user.username,
                "display_name": new_user.display_name,
                "hashed_password": new_user.hashed_password
            },
            where={"username": user.username}
        )


@router.delete("/user/{username}")
async def delete_user(actor: deps.SignedInUser, user: deps.ExistingUser, db: deps.DBConnection) -> None:
    """Delete user from DB, not including owned decks."""
    deps.check_for_resource_owner_or_admin(user.username, actor)
    with db:
        db.delete("users", {"username": user.username})
