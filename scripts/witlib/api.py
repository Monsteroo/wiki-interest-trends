"""HTTP access to Wikimedia APIs: identifying User-Agent, pacing, retries and a disk cache."""
from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from . import __version__

DEFAULT_CONTACT = "https://github.com/Monsteroo/wiki-interest-trends"
RETRY_STATUSES = {429, 500, 502, 503, 504}


@dataclass
class Response:
    status: int
    body: str
    headers: dict[str, str]


class TransientError(Exception):
    """A connection-level failure that is worth retrying."""


class WitNetworkError(RuntimeError):
    """The API stayed unavailable after all retries, or answered with an unexpected status."""


class WitBudgetError(RuntimeError):
    """A single run would send too many requests."""


Transport = Callable[[str, dict[str, str]], Response]


def requests_transport(url: str, headers: dict[str, str]) -> Response:
    import requests

    try:
        reply = requests.get(url, headers=headers, timeout=30)
    except requests.RequestException as exc:
        raise TransientError(str(exc)) from exc
    return Response(reply.status_code, reply.text, {k.lower(): v for k, v in reply.headers.items()})


def user_agent(contact: str | None = None) -> str:
    import requests

    contact = contact or os.environ.get("WIT_CONTACT") or DEFAULT_CONTACT
    return f"wiki-interest-trends/{__version__} ({contact}) python-requests/{requests.__version__}"


def default_cache_dir() -> Path:
    env = os.environ.get("WIT_CACHE_DIR")
    return Path(env) if env else Path.home() / ".cache" / "wiki-interest-trends" / "http"


class ApiClient:
    def __init__(self, transport: Transport = requests_transport, cache_dir: Path | None = None, *,
                 min_interval: float = 0.35, max_attempts: int = 4, max_requests: int = 400, refresh: bool = False,
                 sleep: Callable[[float], None] = time.sleep, clock: Callable[[], float] = time.monotonic,
                 now: Callable[[], float] = time.time, progress: Callable[[str], None] | None = None):
        self.transport = transport
        self.cache_dir = Path(cache_dir) if cache_dir else default_cache_dir()
        self.min_interval = min_interval
        self.max_attempts = max_attempts
        self.max_requests = max_requests
        self.refresh = refresh
        self.sleep = sleep
        self.clock = clock
        self.now = now
        self.progress = progress
        self.headers = {"User-Agent": user_agent(), "Accept": "application/json"}
        self.request_count = 0
        self.cache_hits = 0
        self._last_request: float | None = None

    def get_json(self, url: str, *, ttl: float | None = None, allow_404: bool = False) -> dict | None:
        """GET a JSON document. ttl=None keeps it cached forever; allow_404 turns 404 into None."""
        cached = self._read_cache(url, ttl)
        if cached is not None:
            self.cache_hits += 1
            return self._decode(url, cached["status"], cached["body"], allow_404)
        reply = self._fetch(url)
        if reply.status == 200 or (reply.status == 404 and allow_404):
            self._write_cache(url, reply)
        return self._decode(url, reply.status, reply.body, allow_404)

    def _decode(self, url: str, status: int, body: str, allow_404: bool) -> dict | None:
        if status == 404 and allow_404:
            return None
        if status != 200:
            raise WitNetworkError(f"HTTP {status} for {url}")
        return json.loads(body)

    def _fetch(self, url: str) -> Response:
        if self.request_count >= self.max_requests:
            raise WitBudgetError(f"this run needs more than {self.max_requests} API requests")
        last_error = ""
        for attempt in range(1, self.max_attempts + 1):
            self._pace()
            self.request_count += 1
            if self.progress and self.request_count % 10 == 0:
                self.progress(f"... {self.request_count} API requests")
            try:
                reply = self.transport(url, dict(self.headers))
            except TransientError as exc:
                reply, last_error = None, str(exc)
            if reply is not None and reply.status not in RETRY_STATUSES:
                return reply
            if reply is not None:
                last_error = f"HTTP {reply.status}"
            if attempt < self.max_attempts:
                self.sleep(self._retry_delay(reply, attempt))
        raise WitNetworkError(f"{last_error} after {self.max_attempts} attempts for {url}")

    @staticmethod
    def _retry_delay(reply: Response | None, attempt: int) -> float:
        if reply is not None:
            retry_after = reply.headers.get("retry-after", "")
            if retry_after.isdigit():
                return float(retry_after)
        return float(2 ** attempt)

    def _pace(self) -> None:
        if self._last_request is not None:
            wait = self.min_interval - (self.clock() - self._last_request)
            if wait > 0:
                self.sleep(wait)
        self._last_request = self.clock()

    def _cache_file(self, url: str) -> Path:
        return self.cache_dir / (hashlib.sha256(url.encode("utf-8")).hexdigest() + ".json")

    def _read_cache(self, url: str, ttl: float | None) -> dict | None:
        if self.refresh:
            return None
        path = self._cache_file(url)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        if ttl is not None and self.now() - data.get("fetched_at", 0) > ttl:
            return None
        return data

    def _write_cache(self, url: str, reply: Response) -> None:
        path = self._cache_file(url)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps({"url": url, "status": reply.status, "body": reply.body, "fetched_at": self.now()}), encoding="utf-8")
        tmp.replace(path)
