import itertools
import logging
from collections.abc import Iterable
from datetime import datetime, timezone
from typing import TypeVar

import click
import uvicorn.logging

T = TypeVar("T")


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
