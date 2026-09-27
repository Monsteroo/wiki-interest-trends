"""Charts for the report (matplotlib, headless)."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from .narrative import fmt_pct

PALETTE = ["#0072B2", "#E69F00", "#009E73", "#CC79A7", "#56B4E9", "#D55E00", "#F0E442", "#000000"]
TRUST_COLORS = {"high": "#009E73", "medium": "#E69F00", "low": "#D55E00"}
NO_DATA_COLOR = "#9E9E9E"
TREND_SIZE = (7.3, 2.4)
GROWTH_SIZE = (4.4, 1.9)


def rolling_mean(values: list[float], window: int = 3) -> list[float]:
    out = []
    for i in range(len(values)):
        chunk = values[max(0, i - window + 1): i + 1]
        out.append(sum(chunk) / len(chunk))
    return out


def index_series(values: list[float]) -> list[float] | None:
    """3-month average indexed to 100 = mean of the first 12 months (first half when shorter than 24)."""
    base_len = 12 if len(values) >= 24 else max(1, len(values) // 2)
    base = sum(values[:base_len]) / base_len
    if base == 0:
        return None
    return [v / base * 100 for v in rolling_mean(values)]


def trend_chart(path: Path, months: list[str], series: list[dict], title: str) -> Path:
    fig, ax = plt.subplots(figsize=TREND_SIZE, dpi=200)
    x = list(range(len(months)))
    for i, item in enumerate(series):
        indexed = index_series(item["values"])
        if indexed is None:
            continue
        color = PALETTE[i % len(PALETTE)]
        ax.plot(x, indexed, color=color, linewidth=1.4, label=item["label"])
        marks = [months.index(m) for m in item.get("spike_months", []) if m in months]
        ax.scatter(marks, [indexed[j] for j in marks], color=color, s=12, zorder=3)
    ax.axhline(100, color="#999999", linewidth=0.6, linestyle="--")
    step = max(1, len(months) // 8)
    ax.set_xticks(x[::step], [months[i] for i in x[::step]], fontsize=6)
    ax.tick_params(axis="y", labelsize=6)
    ax.set_title(title, fontsize=7.5, loc="left")
    ax.spines[["top", "right"]].set_visible(False)
    if ax.get_legend_handles_labels()[0]:
        ax.legend(fontsize=6, frameon=False, ncol=4, loc="upper left")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return Path(path)


def bar_label(growth: float, months_up: int | None) -> str:
    pct = fmt_pct(growth)
    return f" {pct} · {months_up}/12 " if months_up is not None else f" {pct} "


def growth_chart(path: Path, bars: list[dict], title: str, na_label: str) -> Path:
    fig, ax = plt.subplots(figsize=GROWTH_SIZE, dpi=200)
    y = list(range(len(bars)))[::-1]
    for yi, bar in zip(y, bars):
        if bar["growth"] is None:
            ax.barh(yi, 0, color=NO_DATA_COLOR)
            ax.text(0, yi, f" {na_label}", va="center", fontsize=6, color="#555555")
            continue
        value = bar["growth"] * 100
        ax.barh(yi, value, color=TRUST_COLORS.get(bar["trust"], NO_DATA_COLOR), height=0.6)
        label = bar_label(bar["growth"], bar.get("months_up"))
        ax.text(value, yi, label, va="center", ha="left" if value >= 0 else "right", fontsize=6)
    ax.set_yticks(y, [b["label"] for b in bars], fontsize=6)
    ax.axvline(0, color="#555555", linewidth=0.6)
    ax.tick_params(axis="x", labelsize=6)
    ax.set_title(title, fontsize=7.5, loc="left")
    ax.spines[["top", "right"]].set_visible(False)
    ax.margins(x=0.25)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return Path(path)
