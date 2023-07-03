import os
from pathlib import Path
from typing import Final

ROOT_DIR: Final = Path(__file__).parent.parent.parent

if (_db_path := os.getenv("TMC_DATABASE_PATH")) is not None:
    DATABASE_PATH: Final = Path(_db_path)
else:
    DATABASE_PATH: Final = Path(ROOT_DIR, "db.sqlite3")

DATABASE_BACKUP: Final = False
DATABASE_BACKUP_PATH: Final = DATABASE_PATH.with_stem(DATABASE_PATH.stem + "-backup")

AUTH_ALGORITHM: Final = "HS256"
AUTH_SECRET_KEY: Final = "7c3c743d58707f77168b31fb38e0cbcd3ad3ccb071011dae539898806d05b8e5"
AUTH_TOKEN_EXPIRE_MINUTES: Final = 60 * 1
