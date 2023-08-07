# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import os
from datetime import timedelta
from pathlib import Path
from typing import Any, Callable, Final, TypeVar

T = TypeVar("T")
_MISSING: Final = object()


def TimeDelta(value: str) -> timedelta:
    kwargs = {}
    for argument_string in value.replace(" ", "").split(","):
        unit, value = argument_string.split("=")
        kwargs[unit] = int(value)
    return timedelta(**kwargs)


def opt(name: str, type: Callable[[Any], T], default: Any = _MISSING) -> T:
    """Read a value from the environment, after conversion.

    The environment variable read is the option name uppercased with dashes
    replaced with underscores and prefixed with TMC_. Example:

        use-tls -> TMC_USE_TLS

    If the envvar is missing, then the default is used. If a default is not
    specified, a RuntimeError is raised.
    """
    name = "TMC_" + name.replace("-", "_").upper()
    raw_value = os.getenv(name, default)
    if raw_value is _MISSING:
        raise RuntimeError(f"Missing environment variable: {name}")

    try:
        return type(raw_value)
    except (TypeError, ValueError) as error:
        context = f"|\n╰─> {error.__class__.__name__}: {error}"
        raise RuntimeError(f"Invalid environment variable: {name}\n{context}")


LOG_CONFIG: Final = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "app.utils.AppLogFormatter",
            "fmt": "%(levelprefix)s [%(name)s] %(message)s",
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
    },
    "loggers": {
        "app": {"handlers": ["default"], "level": "INFO", "propagate": False},
    },
}

# fmt: off
# --- Database --- #

DATABASE_PATH: Final = opt("database", Path)

# --- Authentication --- #

ALLOW_NEW_USERS: Final       = opt("allow-new-users",       bool,      default=False)
REFRESH_COOKIE_NAME: Final   = opt("refresh-cookie-name",   str,       default="RefreshCookie")

ACCESS_TOKEN_LIFETIME: Final = opt("access-token-lifetime", TimeDelta, default="minutes=30")
SESSION_LIFETIME: Final      = opt("session-lifetime",      TimeDelta, default="days=1")
SESSION_PURGE_DELTA: Final   = opt("session-purge-after",   TimeDelta, default="days=2")
MAX_SESSIONS: Final          = opt("max-sessions",          int,       default=50)

# --- Deployment --- #

TLS_ENABLED: Final            = opt("tls",                bool, default=False)
USE_UNIX_DOMAIN_SOCKET: Final = opt("unix-domain-socket", bool, default=False)
