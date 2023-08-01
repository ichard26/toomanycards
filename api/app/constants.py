import os
from datetime import timedelta
from pathlib import Path
from typing import Final

ROOT_DIR: Final = Path(__file__).parent.parent.parent

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

# --- Database --- #

if (_db_path := os.getenv("TMC_DATABASE_PATH")) is not None:
    DATABASE_PATH = Path(_db_path)
else:
    DATABASE_PATH = Path(ROOT_DIR, "db.sqlite3")

# --- Authentication --- #

ACCESS_TOKEN_LIFETIME: Final = timedelta(minutes=30)
ALLOW_NEW_USERS: Final = bool(os.getenv("TMC_ALLOW_NEW_USERS", False))
MAX_SESSIONS: Final = 50
REFRESH_COOKIE_NAME: Final = "RefreshToken"
SESSION_LIFETIME: Final = timedelta(days=1)
SESSION_PURGE_DELTA: Final = timedelta(days=2)

# --- Deployment --- #

TLS_ENABLED: Final = bool(os.getenv("TMC_TLS_ENABLED", False))
USE_UNIX_DOMAIN_SOCKET: Final = bool(os.getenv("TMC_USE_UNIX_DOMAIN_SOCKET", False))
