from datetime import date

from witlib.seasonality import seasonality
from witlib.series import month_list

MONTHS = month_list(date(2021, 9, 1), date(2026, 8, 1))


def series(value):
    return {m: float(value(m)) for m in MONTHS}


def test_january_peak_in_four_of_five_years_is_stable():
    data = series(lambda m: 150 if m.endswith("-01") and m != "2024-01" else (130 if m == "2024-03" else 100))
    result = seasonality(data, MONTHS, level_views=1000)
    assert result["status"] == "stable_peak"
    assert (result["peak_month"], result["peak_years"], result["cycles"]) == (1, 4, 5)
    assert result["uplift"] >= 0.2


def test_flat_series_has_no_stable_pattern():
    assert seasonality(series(lambda m: 100), MONTHS, level_views=1000)["status"] == "no_stable_pattern"


def test_two_years_are_not_enough():
    assert seasonality(series(lambda m: 100), MONTHS[-24:], level_views=1000) == {"status": "insufficient_history", "cycles": 2}


def test_low_traffic_is_not_analysed():
    assert seasonality(series(lambda m: 100), MONTHS, level_views=99) == {"status": "low_volume"}
