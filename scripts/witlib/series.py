"""Periods, pageview fetching and construction of daily and monthly series."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from urllib.parse import quote

from .api import ApiClient
from .resolve import get_entities, page_info
from .study import Study, StudyError

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


def series_key(topic_index: int, lang: str, n_topics: int, n_langs: int) -> str:
    if n_topics == 1:
        return lang
    if n_langs == 1:
        return f"t{topic_index}"
    return f"t{topic_index}.{lang}"


def collect_inputs(client: ApiClient, study: Study, periods: Periods) -> tuple[list[SeriesInput], list[str]]:
    """Find the articles of every topic x language, fetch their daily views and the language totals."""
    warnings: list[str] = []
    qids = list(dict.fromkeys([t.wikidata for t in study.topics] + [q for t in study.topics for q in t.related]))
    entities = get_entities(client, qids, study.languages)
    missing = [q for q in qids if q not in entities]
    if missing:
        raise StudyError([("topics", f"Wikidata item(s) {', '.join(missing)} not found", "Run scripts/wit resolve again and copy the id it prints")])
    start, end = periods.history_start, periods.end_day
    days = day_list(start, end)
    zeros = [0.0] * len(days)
    project = {lang: fetch_project_monthly(client, lang, start, end) for lang in study.languages}
    inputs: list[SeriesInput] = []
    for ti, topic in enumerate(study.topics, 1):
        for lang in study.languages:
            key = series_key(ti, lang, len(study.topics), len(study.languages))
            base = dict(key=key, topic_index=ti, topic_label=topic.label, lang=lang, days=days, project=project[lang])
            substitute = topic.substitutes.get(lang)
            main = substitute or entities[topic.wikidata]["sitelinks"].get(lang)
            if main is None:
                inputs.append(SeriesInput(**base, status="no_article", title=None, articles=[], redirects=0,
                                          substitute=False, daily=zeros, main_daily=zeros))
                continue
            related = [entities[q]["sitelinks"][lang] for q in topic.related if lang in entities[q]["sitelinks"]]
            related = [t for t in dict.fromkeys(related) if t != main]
            info = page_info(client, lang, [main] + related)
            main_info = info[main]
            if not main_info["exists"] or main_info["disambiguation"]:
                status = "disambiguation" if main_info["disambiguation"] else "no_article"
                what = "a disambiguation page" if status == "disambiguation" else "not an existing article"
                warnings.append(f"{key}: '{main}' is {what} in {lang}.wikipedia")
                inputs.append(SeriesInput(**base, status=status, title=main, articles=[], redirects=0,
                                          substitute=bool(substitute), daily=zeros, main_daily=zeros))
                continue
            redirects = main_info["redirects"]
            if len(redirects) > MAX_REDIRECTS:
                warnings.append(f"{key}: {len(redirects)} redirects to '{main_info['title']}', only the first {MAX_REDIRECTS} counted")
                redirects = redirects[:MAX_REDIRECTS]
            main_titles = [main_info["title"]] + redirects
            related_titles = [info[t]["title"] for t in related if info[t]["exists"] and not info[t]["disambiguation"]]
            main_daily = sum_daily([fetch_daily(client, lang, t, start, end) for t in main_titles], days)
            related_daily = sum_daily([fetch_daily(client, lang, t, start, end) for t in related_titles], days)
            daily = [a + b for a, b in zip(main_daily, related_daily)]
            inputs.append(SeriesInput(**base, status="ok" if any(daily) else "no_views", title=main_info["title"],
                                      articles=main_titles[:1] + related_titles, redirects=len(redirects),
                                      substitute=bool(substitute), daily=daily, main_daily=main_daily))
    return inputs, warnings
