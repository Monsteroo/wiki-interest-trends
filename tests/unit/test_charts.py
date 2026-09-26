from witlib.charts import growth_chart, index_series, rolling_mean, trend_chart

MONTHS = [f"2025-{m:02d}" for m in range(1, 13)] + [f"2026-{m:02d}" for m in range(1, 13)]
PNG = b"\x89PNG"


def test_rolling_mean_and_index():
    assert rolling_mean([3.0, 6.0, 9.0, 12.0]) == [3.0, 4.5, 6.0, 9.0]
    assert index_series([0.0] * 24) is None
    assert index_series([10.0] * 24) == [100.0] * 24


def test_trend_chart_draws_many_series_and_skips_empty_ones(tmp_path):
    series = [{"label": f"L{i}", "values": [float(i + 1)] * 24, "spike_months": ["2026-03"]} for i in range(7)]
    series.append({"label": "empty", "values": [0.0] * 24, "spike_months": []})
    assert trend_chart(tmp_path / "trend.png", MONTHS, series, "Динаміка інтересу").read_bytes()[:4] == PNG


def test_growth_chart_handles_missing_data(tmp_path):
    bars = [{"label": "Чеська", "growth": 0.12, "months_up": 9, "trust": "medium"},
            {"label": "Польська", "growth": None, "months_up": None, "trust": None},
            {"label": "Словацька", "growth": -0.3, "months_up": 2, "trust": "low"}]
    assert growth_chart(tmp_path / "growth.png", bars, "Ріст за рік", "н/д").read_bytes()[:4] == PNG
