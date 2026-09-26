"""Periods, pageview fetching and construction of daily and monthly series."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from urllib.parse import quote

from .api import ApiClient

PAGEVIEWS = "https://wikimedia.org/api/rest_v1/metrics/pageviews"
DATA_START = date(2015, 7, 1)
MAX_REDIRECTS = 10


@dataclass(frozen=True)
class Periods:
    as_of: date
    last_month: date
    analysis_start: date
    history_start: date

    @property
    def end_day(self) -> date:
        return month_end(self.last_month)

    @property
    def history_months(self) -> list[str]:
        return month_list(self.history_start, self.last_month)

    @property
    def analysis_months(self) -> list[str]:
        return month_list(self.analysis_start, self.last_month)


@dataclass
class SeriesInput:
    key: str
    topic_index: int
    topic_label: str
    lang: str
    status: str
    title: str | None
    articles: list[str]
    redirects: int
    substitute: bool
    days: list[str]
    daily: list[float]
    main_daily: list[float]
    project: dict[str, int]


def month_add(first: date, n: int) -> date:
    years, month = divmod(first.month - 1 + n, 12)
    return date(first.year + years, month + 1, 1)


def month_end(first: date) -> date:
    return month_add(first, 1) - timedelta(days=1)


def month_list(start: date, last: date) -> list[str]:
    months, current = [], start
    while current <= last:
        months.append(f"{current:%Y-%m}")
        current = month_add(current, 1)
    return months


def day_list(start: date, end: date) -> list[str]:
    return [(start + timedelta(days=i)).isoformat() for i in range((end - start).days + 1)]


def compute_periods(as_of: date, months: int, history_months: int = 60) -> Periods:
    back = 2 if as_of.day <= 2 else 1
    last = month_add(as_of.replace(day=1), -back)
    analysis_start = max(month_add(last, -(months - 1)), DATA_START)
    history_start = max(month_add(last, -(max(months, history_months) - 1)), DATA_START)
    return Periods(as_of=as_of, last_month=last, analysis_start=analysis_start, history_start=history_start)


def article_url(lang: str, title: str, start: date, end: date) -> str:
    encoded = quote(title.replace(" ", "_"), safe="")
    return f"{PAGEVIEWS}/per-article/{lang}.wikipedia.org/all-access/user/{encoded}/daily/{start:%Y%m%d}00/{end:%Y%m%d}00"


def aggregate_url(lang: str, start: date, end: date) -> str:
    return f"{PAGEVIEWS}/aggregate/{lang}.wikipedia.org/all-access/user/monthly/{start:%Y%m%d}00/{end:%Y%m%d}00"


def _day(timestamp: str) -> str:
    return f"{timestamp[0:4]}-{timestamp[4:6]}-{timestamp[6:8]}"


def fetch_daily(client: ApiClient, lang: str, title: str, start: date, end: date) -> dict[str, int]:
    data = client.get_json(article_url(lang, title, start, end), allow_404=True) or {}
    return {_day(item["timestamp"]): int(item["views"]) for item in data.get("items", [])}


def fetch_project_monthly(client: ApiClient, lang: str, start: date, end: date) -> dict[str, int]:
    data = client.get_json(aggregate_url(lang, start, end), allow_404=True) or {}
    return {_day(item["timestamp"])[:7]: int(item["views"]) for item in data.get("items", [])}


def sum_daily(parts: list[dict[str, int]], days: list[str]) -> list[float]:
    return [float(sum(part.get(day, 0) for part in parts)) for day in days]


def monthly_sums(days: list[str], values: list[float]) -> dict[str, float]:
    months: dict[str, float] = {}
    for day, value in zip(days, values):
        months[day[:7]] = months.get(day[:7], 0.0) + value
    return months


def shares(views: dict[str, float], project: dict[str, int]) -> dict[str, float]:
    return {m: (v / project[m] * 1_000_000 if project.get(m) else 0.0) for m, v in views.items()}
