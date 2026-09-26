"""Shared test utilities: replay of recorded HTTP responses and synthetic data builders."""
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures" / "http"


def fixture_path(url: str) -> Path:
    """Recorded responses are gzip-compressed JSON files named by a hash of the URL."""
    return FIXTURES / (hashlib.sha256(url.encode("utf-8")).hexdigest()[:24] + ".json.gz")


class FakeTransport:
    """Replays complete recorded responses by URL; an unknown URL fails the test loudly."""

    def __init__(self, extra=None):
        self.extra = dict(extra or {})
        self.calls: list[str] = []
        self.headers: list[dict] = []

    def __call__(self, url, headers):
        from witlib.api import Response

        self.calls.append(url)
        self.headers.append(dict(headers))
        if url in self.extra:
            item = self.extra[url]
            return item.pop(0) if isinstance(item, list) else item
        path = fixture_path(url)
        if not path.exists():
            raise AssertionError(f"no recorded response for {url} ({path.name}); run: .venv/bin/python tests/fixtures/record.py")
        data = json.loads(gzip.decompress(path.read_bytes()).decode("utf-8"))
        return Response(status=data["status"], body=data["body"], headers=data.get("headers", {}))


def synthetic_input(periods, per_day, *, project=10_000_000, key="cs", lang="cs", status="ok", substitute=False, main_per_day=None, title="Article"):
    """SeriesInput over the whole history; per_day(iso_date) -> views, project: int or month -> int."""
    from witlib.series import SeriesInput, day_list

    days = day_list(periods.history_start, periods.end_day)
    daily = [float(per_day(d)) for d in days]
    main = [float(main_per_day(d)) for d in days] if main_per_day else list(daily)
    totals = {m: (project(m) if callable(project) else project) for m in periods.history_months}
    return SeriesInput(key=key, topic_index=1, topic_label="Topic", lang=lang, status=status, title=title,
                       articles=[title], redirects=0, substitute=substitute, days=days, daily=daily,
                       main_daily=main, project=totals)


def make_result(key="cs", *, lang=None, verdict="growing", trust="high", growth=0.2, months_up=10, months_down=2,
                views=1000, share=1.5, status="ok", reasons=None, seasonality=None, spikes=None,
                substitute=False, title="Article", topic_label="Topic", topic_index=1, months=()):
    from witlib.analysis import SeriesResult

    no_data = verdict == "no_data"
    metrics = {} if no_data else {"views": views, "share": share, "growth": growth, "growth_views": growth,
                                  "growth_share": growth, "growth_clean": growth, "months_up": months_up,
                                  "months_down": months_down, "window_growth": None}
    if reasons is None:
        reasons = [{"code": status, "level": "low"}] if no_data else []
    return SeriesResult(key=key, topic_index=topic_index, topic_label=topic_label, lang=lang or key, status=status,
                        title=title, articles=[title] if title else [], redirects=0, substitute=substitute,
                        verdict=verdict, trust=None if no_data else trust, reasons=reasons, metrics=metrics,
                        monthly={m: {"views": views, "share": share} for m in months}, spikes=spikes or [],
                        seasonality=seasonality or {"status": "no_stable_pattern"})
