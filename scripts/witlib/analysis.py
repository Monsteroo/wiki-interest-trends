"""Growth, consistency, spikes, trust, verdicts and ranking: pure functions over pageview series."""
from __future__ import annotations

import statistics

LEVEL_ORDER = {"low": 0, "medium": 1, "note": 2}


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
