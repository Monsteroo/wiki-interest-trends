from datetime import date

import pytest

from helpers import make_result, synthetic_input
from witlib.analysis import analyze, rank_positions, rank_series
from witlib.series import compute_periods

PERIODS = compute_periods(date(2026, 9, 26), 24)
RECENT_START = "2025-09-01"


def test_steady_growth_is_growing_with_high_trust():
    r = analyze(synthetic_input(PERIODS, lambda d: 60 if d >= RECENT_START else 50), PERIODS, "views")
    assert r.verdict == "growing" and r.trust == "high" and r.reasons == []
    assert r.metrics["growth"] == pytest.approx(0.2) and r.metrics["months_up"] == 12
    assert r.metrics["views"] == round(60 * 365 / 12)
    assert set(r.monthly) == set(PERIODS.history_months)


def test_growth_made_by_one_spike_has_low_trust():
    per_day = lambda d: (52 if d >= RECENT_START else 50) + (4000 if d == "2026-03-10" else 0)  # noqa: E731
    r = analyze(synthetic_input(PERIODS, per_day), PERIODS, "views")
    assert r.verdict == "growing" and r.trust == "low"
    assert r.reasons[0]["code"] == "event_driven" and r.reasons[0]["date"] == "2026-03-10"
    assert r.metrics["growth_clean"] == pytest.approx(0.04)
    assert r.spikes[0]["date"] == "2026-03-10"


def test_missing_article_has_no_data():
    r = analyze(synthetic_input(PERIODS, lambda d: 0, status="no_article", title=None), PERIODS, "share")
    assert (r.verdict, r.trust, r.reasons, r.metrics) == ("no_data", None, [{"code": "no_article", "level": "low"}], {})


def test_new_article_is_flagged():
    r = analyze(synthetic_input(PERIODS, lambda d: 30 if d >= "2025-03-01" else 0), PERIODS, "views")
    assert "new_article" in [x["code"] for x in r.reasons] and r.trust == "low"


def test_share_accounts_for_a_growing_language_edition():
    inp = synthetic_input(PERIODS, lambda d: 100, project=lambda m: 20_000_000 if m >= "2025-09" else 10_000_000)
    r = analyze(inp, PERIODS, "share")
    assert r.metrics["growth_views"] == pytest.approx(0.0) and r.metrics["growth_share"] == pytest.approx(-0.5)
    assert r.verdict == "declining" and r.trust == "high"


def test_rank_positions_average_ties():
    assert rank_positions([3.0, 1.0, 2.0]) == [1.0, 3.0, 2.0]
    assert rank_positions([2.0, 2.0, 1.0]) == [1.5, 1.5, 3.0]


def test_ranking_follows_priorities_and_puts_no_data_last():
    results = [make_result("pl", growth=0.1, share=3.0, views=9000), make_result("cs", growth=0.5, share=1.0, views=100),
               make_result("sk", verdict="no_data", status="no_article")]
    by_growth = rank_series(results, {"growth": 1.0, "interest": 0.0, "reach": 0.0})
    assert [(row["key"], row["position"]) for row in by_growth] == [("cs", 1), ("pl", 2), ("sk", None)]
    by_reach = rank_series(results, {"growth": 0.0, "interest": 0.0, "reach": 1.0})
    assert by_reach[0]["key"] == "pl" and by_reach[0]["ranks"] == {"growth": 2.0, "interest": 1.0, "reach": 1.0}


def test_no_ranking_without_priorities_or_with_one_series():
    results = [make_result("pl"), make_result("cs")]
    assert rank_series(results, None) == []
    assert rank_series(results[:1], {"growth": 1.0, "interest": 0.0, "reach": 0.0}) == []
