# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import http.client
import re
import subprocess
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import click
import rich

NGINX_LOG_REGEX = re.compile(
    r'''(?P<src>[0-9\.]+)
        \s-\s-\s
        \[(?P<timestamp>.+)\]
        \s
        "(?P<request>.*?)"
        \s
        (?P<status>[0-9]{1,3})
        \s
        (?P<body_bytes_sent>[0-9]+)
        \s
        "(?P<referrer>.*?)"
        \s
        "(?P<useragent>.*?)"''',
    re.VERBOSE
)
console = rich.get_console()
rprint = console.print


@dataclass
class LogEntry:
    source_ip: str
    timestamp: datetime
    request: str
    status: int
    useragent: str


def parse_log_entry(line) -> LogEntry:
    match = NGINX_LOG_REGEX.match(line)
    assert match, f"should match! ({line})"
    return LogEntry(
        source_ip=match.group("src"),
        # Reference: https://en.wikipedia.org/wiki/Common_Log_Format
        timestamp=datetime.strptime(match.group("timestamp"), "%d/%b/%Y:%H:%M:%S %z"),
        request=match.group("request"),
        status=int(match.group("status")),
        useragent=match.group("useragent"),
    )


@click.command()
@click.argument("nginx-log-path", type=click.Path(exists=True, resolve_path=True, path_type=Path))
@click.option("--update-iptables", default="NO", type=click.Choice(["NO", "LOG_DROP", "LOG_REJECT"]))
def main(nginx_log_path: Path, update_iptables: str) -> None:
    t0 = time.perf_counter()
    blob = nginx_log_path.read_text(encoding="utf-8")
    logs = [parse_log_entry(line) for line in blob.splitlines()]
    elapsed = time.perf_counter() - t0
    console.log(f"[dim]Parsed {len(logs)} logs in {elapsed:.3f}s")

    by_ip = defaultdict(list)
    useragents = set()
    for entry in logs:
        by_ip[entry.source_ip].append(entry)
        useragents.add(entry.useragent)

    rprint(f"[bold]Unique source IPs: {len(by_ip)}")
    rprint(f"[bold]Unique user-agents: {len(useragents)}")

    status_frequency = Counter([e.status for e in logs])
    rprint("[bold]Status breakdown:")
    for s, count in sorted(status_frequency.items(), key=lambda kv: kv[1], reverse=True):
        desc = http.client.responses.get(s, "-")
        rprint(f"  [cyan]{count}[/]: {s} [magenta]{desc}[/]", highlight=False)

    suspect_ips = set(by_ip)
    for entry in logs:
        if (200 <= entry.status < 400) or "/api" in entry.request:
            if entry.source_ip in suspect_ips:
                suspect_ips.remove(entry.source_ip)
    console.line()
    rprint(f"[bold orange3]Suspicious source IPs[/]: {len(suspect_ips)}")

    suspect_useragents = {}
    for ip in suspect_ips:
        for entry in by_ip[ip]:
            suspect_useragents[entry.useragent] = ip
    rprint(f"[orange3] -> Suspicious useragents[/]: {len(suspect_useragents)}")

    if update_iptables != "NO":
        console.log("Adding suspicious IPs to iptables ...")
        for ip in suspect_ips:
            subprocess.run(["iptables", "-A", "INPUT", "-s", ip, "-j", update_iptables])


if __name__ == "__main__":
    main()
