import logging
import secrets
from datetime import timedelta
from typing import Annotated

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
from passlib.context import CryptContext

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
from ..models import User
from ..utils import RateLimiter, utc_now

AccessToken = str
RefreshToken = str

logger = logging.getLogger(__name__)
passlib_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
router = APIRouter(tags=["auth"])


def authenticate_user(username: str, password: str, db) -> bool:
    user = db.get_user(username)
    return user and passlib_context.verify(password, user.hashed_password)


def add_auth_session(
    db: deps.DBConnection,
    username: str,
    access_lifetime: timedelta = ACCESS_TOKEN_LIFETIME,
    session_lifetime: timedelta = SESSION_LIFETIME,
) -> tuple[AccessToken, RefreshToken]:
    """Generate an access token w/ a refresh token and add to the DB.

    The access and refresh tokens are generated securely using a CSPRNG.
    """
    access_token = "A:" + secrets.token_hex()
    access_expiry = utc_now() + access_lifetime
    refresh_token = "R:" + secrets.token_hex()
    refresh_expiry = utc_now() + session_lifetime
    with db:
        db.execute(
            """
            INSERT INTO sessions(
                username, refresh_token, refresh_expiry, access_token, access_expiry, created_at
            )
            VALUES(?, ?, ?, ?, ?, ?);
            """,
            (username, refresh_token, refresh_expiry, access_token, access_expiry, utc_now())
        )
    return (access_token, refresh_token)


def refresh_auth_session(
    db: deps.DBConnection,
    refresh_token: str,
    access_lifetime: timedelta = ACCESS_TOKEN_LIFETIME
) -> AccessToken:
    """Regenerate a new access token for a pre-existing session (refresh token)."""
    access_token = "A:" + secrets.token_hex()
    access_expiry = utc_now() + access_lifetime
    with db:
        db.execute(
            "UPDATE sessions SET access_token = ?, access_expiry = ? WHERE refresh_token = ?;",
            [access_token, access_expiry, refresh_token]
        )
    return access_token


async def purge_expired_sessions(purge_delta: timedelta, db: deps.DBConnection) -> None:
    for session in db.get_sign_in_sessions(username=None):
        if (session.refresh_expiry + purge_delta) < utc_now():
            id = session.refresh_token
            created_at = session.created_at.strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"Purging session ({session.username}) from {created_at} - {id}")
            db.execute("DELETE FROM sessions WHERE refresh_token = ?;", [id])
            db.commit()


@router.post("/signup", status_code=201)
async def create_new_user(
    username: Annotated[str, Form(min_length=1, max_length=20, regex=r"^[a-z0-9\.-]+$")],
    password: Annotated[str, Form(min_length=1, max_length=100)],
    full_name: Annotated[str, Form(max_length=50)],
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

    data = {
        "username": username,
        "password": passlib_context.hash(password),
        "full_name": full_name,
        "is_admin": False,
        "created_at": utc_now(),
    }
    with db:
        db.execute("""
            INSERT INTO users (username, hashed_password, full_name, is_admin, created_at)
            VALUES (:username, :password, :full_name, :is_admin, :created_at);
        """, data)
    return await login_for_access_token(username, password, db, request, response, background_tasks)


@router.post("/login")
async def login_for_access_token(
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
    x_csrf_protection: Annotated[str, Header()],
    db: deps.DBConnection,
    request: Request,
    response: Response,
    background_tasks: BackgroundTasks,
) -> AccessToken:
    limiter = RateLimiter("login:failed-attempt", {RateLimiter.DAY: 10}, db)
    if limiter.should_block(request.client.host) or limiter.should_block(username):
        raise HTTPException(429)

    if authenticate_user(username, password, db):
        if len(db.get_sign_in_sessions(username, include_expired=False)) >= MAX_SESSIONS:
            raise HTTPException(429, detail="Too many registered sessions")

        background_tasks.add_task(purge_expired_sessions, SESSION_PURGE_DELTA, db)
        access_token, refresh_token = add_auth_session(db, username)
        response.set_cookie(
            REFRESH_COOKIE_NAME,
            refresh_token,
            secure=TLS_ENABLED,
            httponly=True,
            samesite="lax",
            max_age=int(SESSION_LIFETIME.total_seconds()),
        )
        return access_token

    limiter.update(request.client.host)
    limiter.update(username)
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )


@router.post("/logout")
async def logout_session(
    session: deps.ValidAccessToken, db: deps.DBConnection, response: Response
) -> None:
    # XXX: browser support for this header is quite limited, *sigh*
    # https://bugs.chromium.org/p/chromium/issues/detail?id=898503
    response.headers["Clear-Site-Data"] = '"cookies", "storage"'
    with db:
        db.execute("DELETE FROM sessions WHERE access_token = ?;", [session.access_token])


@router.post("/refresh-session")
async def refresh_session(session: deps.ValidRefreshCookie, db: deps.DBConnection) -> AccessToken:
    return refresh_auth_session(db, session.refresh_token)


@router.get("/current-user")
async def get_current_user(actor: deps.SignedInUser) -> User:
    return actor


@router.get("/user/{username}")
async def get_user(actor: deps.SignedInUser, user: deps.ExistingUser) -> User:
    deps.check_for_resource_owner_or_admin(user.username, actor)
    return user


@router.delete("/user/{username}")
async def delete_user(actor: deps.SignedInUser, user: deps.ExistingUser, db: deps.DBConnection) -> None:
    """Delete user from DB, not including owned decks."""
    deps.check_for_resource_owner_or_admin(user.username, actor)
    with db:
        db.execute("DELETE FROM sessions WHERE username = ?;", [user.username])
        db.execute("DELETE FROM users WHERE username = ?;", [user.username])
