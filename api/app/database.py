import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol


class DB(Protocol):
    def get(self, key: str) -> Any: ...
    def set(self, key: str, value: Any) -> None: ...
    def commit(self) -> None: ...


class FileDB:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        try:
            self.data = json.loads(self.db_path.read_text("utf-8"))
        except FileNotFoundError:
            self.data = {"data": {"users": {}, "decks": {}}}

    def get(self, key: str) -> Any:
        return self.data["data"][key]

    def set(self, key: str, value: Any) -> None:
        self.data["data"][key] = value

    def commit(self) -> None:
        shutil.copy2(self.db_path, self.db_path.with_suffix(".backup.json"))
        self.data["last_modified"] = datetime.now(timezone.utc).isoformat()
        blob = json.dumps(self.data, indent=2)
        self.db_path.write_text(blob, "utf-8")


db = FileDB(Path("/home/ichard26/programming/webdev/toomanycards/api/") / "db.json")
