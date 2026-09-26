"""Seasonality: month-of-year profile over up to five yearly cycles and the stability of its peak."""
from __future__ import annotations

import math


def seasonality(monthly: dict[str, float], months: list[str], level_views: float, max_cycles: int = 5) -> dict:
    if level_views < 100:
        return {"status": "low_volume"}
    cycles = []
    for c in range(min(max_cycles, len(months) // 12)):
        block = months[len(months) - 12 * (c + 1): len(months) - 12 * c]
        average = sum(monthly.get(m, 0.0) for m in block) / 12
        if average > 0:
            cycles.append({int(m[5:7]): monthly.get(m, 0.0) / average for m in block})
    if len(cycles) < 3:
        return {"status": "insufficient_history", "cycles": len(cycles)}
    profile = {month: sum(cycle[month] for cycle in cycles) / len(cycles) for month in range(1, 13)}
    peak = max(profile, key=profile.get)
    low = min(profile, key=profile.get)
    peak_years = sum(1 for cycle in cycles if max(cycle, key=cycle.get) == peak)
    stable = peak_years >= math.ceil(0.6 * len(cycles)) and profile[peak] >= 1.20
    return {"status": "stable_peak" if stable else "no_stable_pattern", "peak_month": peak, "low_month": low,
            "peak_years": peak_years, "cycles": len(cycles), "uplift": round(profile[peak] - 1, 3),
            "profile": {month: round(value, 3) for month, value in profile.items()}}
