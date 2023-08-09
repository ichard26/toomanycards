# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import itertools
import logging
import sqlite3
from collections.abc import Iterable
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, Final, Optional, Sequence, TypeVar, Union, cast

if TYPE_CHECKING:
    ASGI3Application = Any
    ASGIReceiveCallable = Any
    ASGISendCallable = Any
    Headers = dict[bytes, bytes]
    HTTPScope = Any
    Scope = Any
    WebSocketScope = Any

import click
import uvicorn.logging
from pydantic import BaseModel

T = TypeVar("T")
RateLimits = dict[int, int]


def flatten(iterables: Iterable[Iterable[T]]) -> list[T]:
    """Flatten nested iterables into a single list."""
    return list(itertools.chain.from_iterable(iterables))


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AppLogFormatter(uvicorn.logging.DefaultFormatter):
    def formatMessage(self, record: logging.LogRecord) -> str:
        if self.use_colors:
            record.name = click.style(record.name, dim=True)
        return super().formatMessage(record)


class ProxyHeadersMiddleware:
    """
    This middleware can be used when a known proxy is fronting the application,
    and is trusted to be properly setting the `X-Forwarded-Proto`,
    `X-Forwarded-For`, and `X-Forwarded-Client-Port` headers with the connecting
    client information.

    Modifies the `client` and `scheme` information so that they reference
    the connecting client, rather that the connecting proxy.

    Portions taken from the encode/uvicorn project. License can be found in
    :/LICENSE-THIRDPARTY.md

    Copyright © 2017-present, Encode OSS Ltd. All rights reserved.
    """

    def __init__(self, app: "ASGI3Application", require_none_client: bool) -> None:
        self.app = app
        self.trusted_clients = (None,) if require_none_client else ("127.0.0.1", "localhost")

    def rewrite_scheme(self, scope: "Scope", headers: "Headers") -> None:
        # Determine if the incoming request was http or https based on
        # the X-Forwarded-Proto header.
        x_forwarded_proto = (headers[b"x-forwarded-proto"].decode("latin1").strip())
        if scope["type"] == "websocket":
            scope["scheme"] = "wss" if x_forwarded_proto == "https" else "ws"
        else:
            scope["scheme"] = x_forwarded_proto

    def rewrite_client(
        self, scope: "Scope", headers: "Headers", client_host: Optional[str]
    ) -> None:
        # Determine the client address from the X-Real-IP and X-Forwarded-Client-Port
        # headers.
        host = headers[b"x-real-ip"].decode("latin1")
        port = int(headers[b"x-forwarded-client-port"].decode("latin1"))
        scope["client"] = (host, port)

    async def __call__(
        self, scope: "Scope", receive: "ASGIReceiveCallable", send: "ASGISendCallable"
    ) -> None:
        if scope["type"] in ("http", "websocket"):
            scope = cast(Union["HTTPScope", "WebSocketScope"], scope)
            headers = dict(scope["headers"])
            client_addr: Optional[tuple[str, int]] = scope.get("client")
            client_host = client_addr[0] if client_addr else None

            if client_host in self.trusted_clients:
                if b"x-forwarded-proto" in headers:
                    self.rewrite_scheme(scope, headers)
                if b"x-real-ip" in headers:
                    self.rewrite_client(scope, headers, client_host)

        return await self.app(scope, receive, send)


class RateLimitWindow(BaseModel):
    duration: int
    limit: int
    value: int
    expiry: datetime


class RateLimiter:
    MINUTE: Final = 1
    HOUR: Final = 60
    DAY: Final = 1440

    class SQLiteBackend:
        def __init__(self, db: sqlite3.Connection, max_windows: int = 5000) -> None:
            self.db = db
            self.max_windows = max_windows
            self.commit = db.commit

        def get_window(self, key: str, duration: int, limit: int) -> Optional[RateLimitWindow]:
            cur = self.db.execute(
                "SELECT rowid, value, expiry FROM ratelimits WHERE key = ? AND duration = ?;",
                [key, duration]
            )
            if row := cur.fetchone():
                return RateLimitWindow(duration=duration, limit=limit, value=row[1], expiry=row[2])
            return None

        def create_window(self, key: str, duration: int, limit: int, expiry: datetime) -> RateLimitWindow:
            self.db.execute(
                "INSERT INTO ratelimits(key, duration, value, expiry) VALUES(?, ?, ?, ?);",
                [key, duration, 0, expiry]
            )
            return RateLimitWindow(duration=duration, limit=limit, value=0, expiry=expiry)

        def update_window_key(self, key: str, by: int) -> None:
            self.db.execute(
                "UPDATE ratelimits SET value = value + ? WHERE key = ?;", [by, key]
            )

        def delete_window(self, key: str, duration: int) -> None:
            self.db.execute(
                "DELETE FROM ratelimits WHERE key = ? AND duration = ?;", [key, duration]
            )

        def prune(self) -> int:
            count = self.db.execute("SELECT COUNT(*) FROM ratelimits;").fetchone()[0]
            if (to_prune := count - self.max_windows) > 0:
                self.db.execute("DELETE FROM ratelimits ORDER BY expiry LIMIT ?;", [to_prune])

    def __init__(self, key_prefix: str, limits: RateLimits, db: sqlite3.Connection) -> None:
        self.key_prefix = key_prefix + ":"
        self.limits = limits
        self.backend = RateLimiter.SQLiteBackend(db)

    def update(self, key: str, by: int = 1) -> None:
        """Increment all windows.

        New windows are created as needed (none existed or old one was expired).
        """
        for duration in self.limits:
            self._get_or_create_window(self.key_prefix + key, duration)
        self.backend.update_window_key(self.key_prefix + key, by)
        self.backend.prune()
        self.backend.commit()

    def should_block(self, key: str) -> bool:
        """Return whether at least one limit has been reached."""
        return len(self.reached_limits(key)) > 0

    def update_and_check(self, key: str, by: int = 1) -> bool:
        """update() and should_block() combined."""
        block = self.should_block(key)
        self.update(key, by)
        return block

    def windows(self, key: str) -> Sequence[RateLimitWindow]:
        """Return rate limit windows."""
        wins = [self._get_or_create_window(self.key_prefix + key, duration) for duration in self.limits]
        self.backend.commit()
        return wins

    def reached_limits(self, key: str) -> Sequence[RateLimitWindow]:
        """Like windows() but returns only windows whose limit has been reached."""
        return [w for w in self.windows(key) if w.value >= self.limits[w.duration]]

    def _get_or_create_window(self, key: str, duration: int) -> RateLimitWindow:
        limit = self.limits[duration]
        if stored := self.backend.get_window(key, duration, limit):
            if stored.expiry > utc_now():
                return stored

            self.backend.delete_window(key, duration)
        return self.backend.create_window(
            key, duration, limit, expiry=utc_now() + timedelta(minutes=duration)
        )
