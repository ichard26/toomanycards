import os
from pathlib import Path
from typing import List, Tuple

import click

_HASH_HEADER = """\
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""
_SLASH_HEADER = _HASH_HEADER.replace("#", "//")
_FENCED_STAR_HEADER = """\
/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */
"""
_HTML_HEADER = """\
<!-- This Source Code Form is subject to the terms of the Mozilla Public
   - License, v. 2.0. If a copy of the MPL was not distributed with this
   - file, You can obtain one at https://mozilla.org/MPL/2.0/. -->
"""
HEADERS = {
    ".py": _HASH_HEADER,
    ".svelte": _HTML_HEADER,
    ".js": _SLASH_HEADER,
    ".html": _HTML_HEADER,
    ".css": _FENCED_STAR_HEADER,
}


def scan(directory: os.PathLike) -> List[Path]:
    """Scan a directory for all contained files."""
    files = []
    for entry in os.scandir(directory):
        if entry.is_file():
            files.append(Path(entry))
        elif entry.is_dir():
            files.extend(scan(entry))

    return files


@click.command
@click.argument("src", nargs=-1, type=click.Path(exists=True, path_type=Path))
@click.option("-y", "--yes", is_flag=True)
def main(src: Tuple[Path, ...], yes: bool) -> None:
    files = []
    for s in src:
        if s.is_dir():
            files.extend(scan(s))
        else:
            files.append(s)

    index = 1
    need_header = {}
    for p in files:
        if header := HEADERS.get(p.suffix, None):
            current_text = p.read_text("utf-8")
            if header not in current_text:
                need_header[p] = (header, current_text)
                click.secho(f"{index}. {p}", fg="cyan")
                index += 1

    if not need_header:
        return

    if not yes and not click.confirm("\nAdd header to listed files?"):
        return

    for p, (header, current_text) in need_header.items():
        newline = "\n" if current_text.strip() else ""
        p.write_text(header + newline + current_text, "utf-8")


if __name__ == "__main__":
    main()
