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


# --- Boundary tests for the thresholds in references/methodology.md §Seasonality:
# "at least three [cycles]"; "top month in at least 60% of cycles"; "at least 20% above the yearly mean". ---


def test_three_cycles_are_evaluated_not_insufficient():
    result = seasonality(series(lambda m: 100), MONTHS[-36:], level_views=1000)
    assert result["status"] != "insufficient_history"
    assert result["cycles"] == 3


def test_two_cycles_are_not_enough_data():
    assert seasonality(series(lambda m: 100), MONTHS[-24:], level_views=1000) == {"status": "insufficient_history", "cycles": 2}


def _cycle_months(idx):
    """The idx-th cycle counting from the most recent (idx=0 is the last 12 months of MONTHS)."""
    end = len(MONTHS) - 12 * idx
    return MONTHS[end - 12:end]


def _elevated_block(block_months, jan_value, total=12288):
    """One yearly block (12 months) where January = jan_value and the other 11 months share the rest of `total`."""
    jan_month = next(m for m in block_months if m.endswith("-01"))
    others = [m for m in block_months if m != jan_month]
    other_total = total - jan_value
    base, remainder = divmod(other_total, len(others))
    values = {m: float(base) for m in others}
    values[others[-1]] += remainder
    values[jan_month] = float(jan_value)
    return values


def _flat_block(block_months, value=1024):
    return {m: float(value) for m in block_months}


def _alt_peak_block(block_months, alt_value, base=100.0):
    """All months at base except March, which is elevated instead -> January is not this block's top month."""
    alt_month = next(m for m in block_months if m.endswith("-03"))
    return {m: (alt_value if m == alt_month else base) for m in block_months}


def test_peak_top_in_three_of_five_cycles_is_stable():
    # January is the block's own maximum (elevated, ratio 1.5) in cycles 0, 1, 2 and merely average (tied,
    # loses to September's dict order) in cycles 3, 4 -> peak_years = 3 = ceil(0.6 * 5), the 60% boundary,
    # with profile comfortably above the separate 1.20 uplift threshold.
    data: dict[str, float] = {}
    for idx in (0, 1, 2):
        data.update(_elevated_block(_cycle_months(idx), jan_value=1536))
    for idx in (3, 4):
        data.update(_flat_block(_cycle_months(idx)))
    result = seasonality(data, MONTHS, level_views=1000)
    assert result["status"] == "stable_peak"
    assert result["peak_month"] == 1
    assert result["peak_years"] == 3


def test_peak_top_in_two_of_five_cycles_is_not_stable():
    # January is only the block's own maximum in 2 of the 5 cycles (below the 60% boundary): the other 3
    # cycles have March as their top month instead. January's profile average is still pushed well above
    # the 1.20 uplift threshold, isolating the peak_years condition as the reason it is not stable.
    data: dict[str, float] = {}
    for idx in (0, 1):
        data.update(_elevated_block(_cycle_months(idx), jan_value=3000))
    for idx in (2, 3, 4):
        data.update(_alt_peak_block(_cycle_months(idx), alt_value=130))
    result = seasonality(data, MONTHS, level_views=1000)
    assert result["peak_month"] == 1
    assert result["peak_years"] == 2
    assert result["profile"][1] >= 1.20
    assert result["status"] == "no_stable_pattern"


def test_profile_uplift_of_exactly_1_20_is_stable():
    # Three cycles where January is the local max, with profile ratios 1.5, 1.25, 1.25 (all exact in binary
    # floating point against a block average of 1024), plus two flat cycles (ratio 1.0, not top). Average =
    # (1.5 + 1.25 + 1.25 + 1.0 + 1.0) / 5 = 6.0 / 5 = 1.20 exactly -> right at the ">= 1.20" boundary.
    data: dict[str, float] = {}
    for idx, jan_value in zip((0, 1, 2), (1536, 1280, 1280)):
        data.update(_elevated_block(_cycle_months(idx), jan_value))
    for idx in (3, 4):
        data.update(_flat_block(_cycle_months(idx)))
    result = seasonality(data, MONTHS, level_views=1000)
    assert result["status"] == "stable_peak"
    assert result["peak_month"] == 1
    assert result["profile"][1] == 1.2


def test_profile_uplift_of_1_19_is_not_stable():
    # Same shape as above, tuned so the average profile lands just under the 1.20 uplift threshold (~1.19)
    # while peak_years (3) still clears the 60% boundary on its own.
    data: dict[str, float] = {}
    for idx in (0, 1, 2):
        data.update(_elevated_block(_cycle_months(idx), jan_value=1348))
    for idx in (3, 4):
        data.update(_flat_block(_cycle_months(idx)))
    result = seasonality(data, MONTHS, level_views=1000)
    assert result["peak_month"] == 1
    assert result["peak_years"] == 3
    assert result["profile"][1] < 1.20
    assert result["status"] == "no_stable_pattern"
