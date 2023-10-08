# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from pathlib import Path
from typing import Final

from florapi.configuration import Options, TimeDelta

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
opt = Options("TMC")
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

opt.report_errors()
