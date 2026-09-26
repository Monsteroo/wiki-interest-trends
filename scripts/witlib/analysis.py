"""Growth, consistency, spikes, trust, verdicts and ranking: pure functions over pageview series."""
from __future__ import annotations


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
