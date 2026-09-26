import pytest

from witlib.analysis import decide_verdict, growth, mean, months_up_down, window_growth

PREV = [f"2024-{m:02d}" for m in range(9, 13)] + [f"2025-{m:02d}" for m in range(1, 9)]
RECENT = [f"2025-{m:02d}" for m in range(9, 13)] + [f"2026-{m:02d}" for m in range(1, 9)]
MONTHS = PREV + RECENT


def test_mean_of_nothing_is_zero():
    assert mean([]) == 0.0


def test_growth_compares_last_twelve_months_with_previous_twelve():
    series = {m: 100.0 for m in PREV} | {m: 120.0 for m in RECENT}
    assert growth(series, RECENT, PREV) == pytest.approx(0.2)


def test_growth_is_undefined_without_previous_views():
    series = {m: 0.0 for m in PREV} | {m: 50.0 for m in RECENT}
    assert growth(series, RECENT, PREV) is None


def test_months_up_compare_with_the_same_month_a_year_ago():
    seasonal = {m: 100.0 + 50 * m.endswith("-01") for m in PREV}
    series = seasonal | {m: seasonal[p] * 1.1 for p, m in zip(PREV, RECENT)}
    assert months_up_down(series, MONTHS) == (12, 0)


def test_months_down_count_declines_only():
    series = {m: 100.0 for m in PREV} | {m: (90.0 if i < 8 else 100.0) for i, m in enumerate(RECENT)}
    assert months_up_down(series, MONTHS) == (0, 8)


def test_months_up_down_needs_two_full_years():
    with pytest.raises(ValueError, match="at least 24 months"):
        months_up_down({m: 1.0 for m in RECENT}, RECENT)


def test_window_growth_is_annualised_over_three_years():
    window = [f"m{i:02d}" for i in range(36)]
    series = {m: (100.0 if i < 12 else 121.0) for i, m in enumerate(window)}
    assert window_growth(series, window) == pytest.approx(0.1)
    assert window_growth(series, window[:24]) is None


@pytest.mark.parametrize("args, expected", [
    ((0.10, 7, 0), "growing"),
    ((0.0999, 12, 0), "no_clear_trend"),
    ((0.5, 6, 6), "no_clear_trend"),
    ((-0.10, 0, 7), "declining"),
    ((None, 12, 0), "no_clear_trend"),
    ((-0.10, 0, 6), "no_clear_trend"),
    ((-0.0999, 0, 12), "no_clear_trend"),
])
def test_verdict_thresholds(args, expected):
    assert decide_verdict(*args) == expected


def test_window_growth_is_undefined_when_the_first_year_is_empty():
    window = [f"m{i:02d}" for i in range(36)]
    assert window_growth({m: (0.0 if i < 12 else 50.0) for i, m in enumerate(window)}, window) is None
