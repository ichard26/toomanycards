import itertools
from collections.abc import Iterable
from datetime import datetime, timezone
from typing import TypeVar

T = TypeVar("T")


def flatten(iterables: Iterable[Iterable[T]]) -> list[T]:
    """Flatten nested iterables into a single list."""
    return list(itertools.chain.from_iterable(iterables))


def current_datetime_stamp() -> str:
    return datetime.now(timezone.utc).isoformat()
