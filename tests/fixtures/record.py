"""Record complete real API responses for the offline tests. Test utility, run manually:

    .venv/bin/python tests/fixtures/record.py

Every URL that the recorded flows request is saved to tests/fixtures/http/ as gzip-compressed JSON.
"""
from __future__ import annotations

import gzip
import json
import sys
import tempfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "tests")]

from helpers import fixture_path  # noqa: E402
from witlib.api import ApiClient, requests_transport  # noqa: E402

AS_OF = date(2026, 9, 26)


def recording_transport(url, headers):
    reply = requests_transport(url, headers)
    path = fixture_path(url)
    path.parent.mkdir(parents=True, exist_ok=True)
    keep = {k: v for k, v in reply.headers.items() if k in ("content-type", "retry-after")}
    record = {"url": url, "status": reply.status, "body": reply.body, "headers": keep}
    path.write_bytes(gzip.compress(json.dumps(record, ensure_ascii=False).encode("utf-8"), mtime=0))
    return reply


def record_resolve(client):
    from witlib.resolve import page_info, resolve_topic

    resolve_topic(client, "інтервальне голодування", ["pl", "cs"])
    resolve_topic(client, "Меркурій", ["de"])
    page_info(client, "de", ["Achtsamkeit"])


FLOWS = [record_resolve]


def main():
    client = ApiClient(transport=recording_transport, cache_dir=Path(tempfile.mkdtemp()))
    for flow in FLOWS:
        flow(client)
    print(f"recorded {client.request_count} responses into {fixture_path('x').parent}")


if __name__ == "__main__":
    main()
