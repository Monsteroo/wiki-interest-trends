"""Growth, consistency, spikes, trust, verdicts and ranking: pure functions over pageview series."""
from __future__ import annotations

import statistics
from dataclasses import dataclass

from .seasonality import seasonality
from .series import Periods, SeriesInput, monthly_sums, shares

LEVEL_ORDER = {"low": 0, "medium": 1, "note": 2}
CRITERIA = (("growth", "growth"), ("interest", "share"), ("reach", "views"))


@dataclass
class SeriesResult:
    key: str
    topic_index: int
    topic_label: str
    lang: str
    status: str
    title: str | None
    articles: list[str]
    redirects: int
    substitute: bool
    verdict: str
    trust: str | None
    reasons: list[dict]
    metrics: dict
    monthly: dict[str, dict[str, float]]
    spikes: list[dict]
    seasonality: dict


def mean(values) -> float:
    values = list(values)
    return sum(values) / len(values) if values else 0.0


def growth(series: dict[str, float], recent: list[str], previous: list[str]) -> float | None:
    before = mean(series[m] for m in previous)
    if before == 0:
        return None
    return round(mean(series[m] for m in recent) / before - 1, 6)


def months_up_down(series: dict[str, float], months: list[str]) -> tuple[int, int]:
    if len(months) < 24:
        raise ValueError(f"months_up_down needs at least 24 months, got {len(months)}")
    up = down = 0
    for i in range(len(months) - 12, len(months)):
        now, year_ago = series[months[i]], series[months[i - 12]]
        up += now > year_ago
        down += now < year_ago
    return up, down


def window_growth(series: dict[str, float], window: list[str]) -> float | None:
    if len(window) < 36:
        return None
    first = mean(series[m] for m in window[:12])
    last = mean(series[m] for m in window[-12:])
    if first == 0:
        return None
    return round((last / first) ** (12 / (len(window) - 12)) - 1, 6)


def decide_verdict(g: float | None, months_up: int, months_down: int) -> str:
    if g is None:
        return "no_clear_trend"
    if g >= 0.10 and months_up >= 7:
        return "growing"
    if g <= -0.10 and months_down >= 7:
        return "declining"
    return "no_clear_trend"


def detect_spikes(daily: list[float], window: int = 28, min_history: int = 7, min_views: float = 20.0,
                  ratio: float = 5.0, mad_k: float = 10.0) -> tuple[list[int], list[float]]:
    """Return indices of spike days and the typical (trailing-median) value for every day."""
    spikes: list[int] = []
    typical: list[float] = []
    for i, value in enumerate(daily):
        history = daily[max(0, i - window):i]
        if len(history) < min_history:
            typical.append(value)
            continue
        med = statistics.median(history)
        mad = statistics.median(abs(x - med) for x in history)
        typical.append(med)
        if value >= min_views and value > max(ratio * med, med + mad_k * mad):
            spikes.append(i)
    return spikes, typical


def cap_spikes(daily: list[float], spike_idx: list[int], typical: list[float]) -> list[float]:
    marked = set(spike_idx)
    return [typical[i] if i in marked else value for i, value in enumerate(daily)]


def trust_reasons(*, level_views: float, verdict: str, growth: float | None, growth_clean: float | None,
                  months_up: int, months_down: int, first_view_month: str | None, comparison_start: str,
                  substitute_title: str | None, top_spike: str | None, growth_views: float | None,
                  growth_share: float | None) -> list[dict]:
    reasons: list[dict] = []
    if level_views < 100:
        reasons.append({"code": "low_volume", "level": "low", "views": round(level_views)})
    elif level_views < 500:
        reasons.append({"code": "moderate_volume", "level": "medium", "views": round(level_views)})
    if verdict == "growing" and months_up in (7, 8):
        reasons.append({"code": "inconsistent", "level": "medium", "months": months_up, "direction": "up"})
    if verdict == "declining" and months_down in (7, 8):
        reasons.append({"code": "inconsistent", "level": "medium", "months": months_down, "direction": "down"})
    if verdict == "growing" and growth is not None and growth_clean is not None and (growth_clean < 0.10 or growth_clean < growth / 2):
        reasons.append({"code": "event_driven", "level": "low", "date": top_spike, "direction": "up"})
    if verdict == "declining" and growth is not None and growth_clean is not None and (growth_clean > -0.10 or growth_clean > growth / 2):
        reasons.append({"code": "event_driven", "level": "low", "date": top_spike, "direction": "down"})
    if first_view_month is not None and first_view_month >= comparison_start:
        reasons.append({"code": "new_article", "level": "low", "month": first_view_month})
    if substitute_title:
        reasons.append({"code": "substitute", "level": "medium", "title": substitute_title})
    if (growth_views is not None and growth_share is not None and min(abs(growth_views), abs(growth_share)) >= 0.05
            and (growth_views > 0) != (growth_share > 0)):
        reasons.append({"code": "divergence", "level": "note", "growth_views": growth_views, "growth_share": growth_share})
    return sorted(reasons, key=lambda reason: LEVEL_ORDER[reason["level"]])


def trust_level(reasons: list[dict]) -> str:
    levels = {reason["level"] for reason in reasons}
    if "low" in levels:
        return "low"
    return "medium" if "medium" in levels else "high"


def analyze(inp: SeriesInput, periods: Periods, measure: str) -> SeriesResult:
    """Compute metrics, verdict, trust, spikes and seasonality for one topic x language series."""
    hist, window = periods.history_months, periods.analysis_months
    views = {m: 0.0 for m in hist} | monthly_sums(inp.days, inp.daily)
    share = shares(views, inp.project)
    base = dict(key=inp.key, topic_index=inp.topic_index, topic_label=inp.topic_label, lang=inp.lang,
                status=inp.status, title=inp.title, articles=inp.articles, redirects=inp.redirects,
                substitute=inp.substitute,
                monthly={m: {"views": round(views[m]), "share": round(share[m], 4)} for m in hist})
    if inp.status != "ok":
        return SeriesResult(**base, verdict="no_data", trust=None, reasons=[{"code": inp.status, "level": "low"}],
                            metrics={}, spikes=[], seasonality={"status": "no_data"})
    spike_idx, typical = detect_spikes(inp.daily)
    views_clean = {m: 0.0 for m in hist} | monthly_sums(inp.days, cap_spikes(inp.daily, spike_idx, typical))
    share_clean = shares(views_clean, inp.project)
    primary, primary_clean = (share, share_clean) if measure == "share" else (views, views_clean)
    recent, previous = hist[-12:], hist[-24:-12]
    enough = len(hist) >= 24
    g_views = growth(views, recent, previous) if enough else None
    g_share = growth(share, recent, previous) if enough else None
    g = g_share if measure == "share" else g_views
    g_clean = growth(primary_clean, recent, previous) if enough else None
    up, down = months_up_down(primary, hist) if enough else (0, 0)
    level_views = mean(views[m] for m in recent)
    main_monthly = monthly_sums(inp.days, inp.main_daily)
    first_view = next((m for m in hist if main_monthly.get(m, 0) > 0), None)
    verdict = decide_verdict(g, up, down)
    spikes = _spikes(inp.days, inp.daily, typical, spike_idx)
    event_period = set(previous if verdict == "declining" else recent)
    top_spike = next((s["date"] for s in spikes if s["date"][:7] in event_period), None)
    reasons = trust_reasons(level_views=level_views, verdict=verdict, growth=g, growth_clean=g_clean, months_up=up,
                            months_down=down, first_view_month=first_view,
                            comparison_start=previous[0] if previous else hist[0],
                            substitute_title=inp.title if inp.substitute else None, top_spike=top_spike,
                            growth_views=g_views, growth_share=g_share)
    metrics = {"views": round(level_views), "share": round(mean(share[m] for m in recent), 2), "growth": g,
               "growth_views": g_views, "growth_share": g_share, "growth_clean": g_clean, "months_up": up,
               "months_down": down, "window_growth": window_growth(primary, window)}
    in_window = set(window)
    return SeriesResult(**base, verdict=verdict, trust=trust_level(reasons), reasons=reasons, metrics=metrics,
                        spikes=[s for s in spikes if s["date"][:7] in in_window][:5],
                        seasonality=seasonality(primary_clean, hist, level_views))


def _spikes(days: list[str], daily: list[float], typical: list[float], idx: list[int]) -> list[dict]:
    rows = [{"date": days[i], "views": round(daily[i]), "typical": round(typical[i], 1)} for i in idx]
    return sorted(rows, key=lambda r: r["views"] / r["typical"] if r["typical"] else float("inf"), reverse=True)


def rank_positions(values: list[float]) -> list[float]:
    """1-based ranks, highest value first; ties share the average rank."""
    order = sorted(range(len(values)), key=lambda i: -values[i])
    ranks = [0.0] * len(values)
    start = 0
    while start < len(order):
        end = start
        while end + 1 < len(order) and values[order[end + 1]] == values[order[start]]:
            end += 1
        for k in range(start, end + 1):
            ranks[order[k]] = (start + end) / 2 + 1
        start = end + 1
    return ranks


def rank_series(results: list[SeriesResult], priorities: dict[str, float] | None) -> list[dict]:
    ranked = [r for r in results if r.verdict != "no_data" and r.metrics.get("growth") is not None]
    if not priorities or len(ranked) < 2:
        return []
    n = len(ranked)
    positions = {crit: rank_positions([r.metrics[metric] for r in ranked]) for crit, metric in CRITERIA}
    rows = []
    for i, r in enumerate(ranked):
        score = sum(priorities[crit] * (n - positions[crit][i]) / (n - 1) for crit, _ in CRITERIA)
        rows.append({"key": r.key, "score": round(score, 3), "ranks": {crit: positions[crit][i] for crit, _ in CRITERIA},
                     "trust": r.trust, "growth": r.metrics["growth"]})
    rows.sort(key=lambda row: (-row["score"], -row["growth"]))
    for position, row in enumerate(rows, 1):
        row["position"] = position
        del row["growth"]
    ranked_keys = {r.key for r in ranked}
    rows += [{"key": r.key, "score": None, "ranks": {}, "trust": r.trust, "position": None}
             for r in results if r.key not in ranked_keys]
    return rows
