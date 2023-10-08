# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import logging

import click
import uvicorn.logging


class AppLogFormatter(uvicorn.logging.DefaultFormatter):
    def formatMessage(self, record: logging.LogRecord) -> str:
        if self.use_colors:
            record.name = click.style(record.name, dim=True)
        return super().formatMessage(record)
