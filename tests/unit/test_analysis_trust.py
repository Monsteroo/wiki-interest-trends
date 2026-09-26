import pytest

from witlib.analysis import cap_spikes, detect_spikes, trust_level, trust_reasons


def test_single_day_spike_is_detected_with_its_typical_value():
    daily = [30.0] * 60
    daily[40] = 400.0
    spikes, typical = detect_spikes(daily)
    assert spikes == [40]
    assert typical[40] == 30.0


def test_small_absolute_jumps_are_not_spikes():
    daily = [2.0] * 60
    daily[40] = 19.0
    assert detect_spikes(daily)[0] == []


def test_step_change_is_not_a_spike():
    assert detect_spikes([50.0] * 60 + [60.0] * 60)[0] == []


def test_capping_replaces_spike_days_with_typical_values():
    assert cap_spikes([1.0, 50.0, 1.0], [1], [1.0, 1.0, 1.0]) == [1.0, 1.0, 1.0]


BASE = dict(level_views=1000, verdict="growing", growth=0.3, growth_clean=0.28, months_up=10, months_down=2,
            first_view_month="2015-07", comparison_start="2024-09", substitute_title=None, top_spike=None,
            growth_views=0.3, growth_share=0.3)


def reasons(**changes):
    return trust_reasons(**(BASE | changes))


def codes(**changes):
    return [r["code"] for r in reasons(**changes)]


def test_clean_series_has_high_trust():
    assert reasons() == [] and trust_level([]) == "high"


@pytest.mark.parametrize("views, expected", [(99, "low"), (100, "medium"), (499, "medium"), (500, "high")])
def test_volume_thresholds(views, expected):
    assert trust_level(reasons(level_views=views)) == expected


def test_growth_in_seven_or_eight_months_caps_trust_at_medium():
    assert codes(months_up=8) == ["inconsistent"] and trust_level(reasons(months_up=8)) == "medium"
    assert codes(months_up=9) == []


def test_growth_that_disappears_without_spikes_is_event_driven():
    found = reasons(growth_clean=0.05, top_spike="2026-03-10")
    assert found[0] == {"code": "event_driven", "level": "low", "date": "2026-03-10", "direction": "up"}


def test_decline_explained_by_last_years_spike_is_event_driven():
    found = reasons(verdict="declining", growth=-0.3, growth_clean=-0.05, months_up=0, months_down=12)
    assert [r["code"] for r in found] == ["event_driven"] and found[0]["direction"] == "down"


def test_new_article_lowers_trust():
    assert codes(first_view_month="2025-03") == ["new_article"]


def test_substitute_caps_trust_at_medium():
    assert trust_level(reasons(substitute_title="Głodówka lecznicza")) == "medium"


def test_divergence_between_views_and_share_is_only_a_note():
    found = reasons(growth_views=-0.2, growth_share=0.3)
    assert [r["code"] for r in found] == ["divergence"] and trust_level(found) == "high"


def test_reasons_are_ordered_low_first():
    assert [r["level"] for r in reasons(level_views=200, first_view_month="2025-03")] == ["low", "medium"]
