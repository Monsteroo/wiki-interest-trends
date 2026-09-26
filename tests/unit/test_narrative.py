import pytest

from helpers import make_result
from witlib.narrative import (NarrativeError, agent_texts, build_texts, fmt_int, fmt_pct, fmt_share, invented_numbers,
                              placeholder_values, reason_text, render, template_steps, template_summary)
from witlib.study import parse_study

PEAK = {"status": "stable_peak", "peak_month": 1, "peak_years": 4, "cycles": 5}


def test_number_formats_per_language():
    assert (fmt_pct(0.123), fmt_pct(-0.05), fmt_pct(0.004), fmt_pct(None, "uk")) == ("+12%", "-5%", "0%", "н/д")
    assert (fmt_int(12345, "uk"), fmt_int(12345, "en")) == ("12 345", "12,345")
    assert (fmt_share(1.234, "uk"), fmt_share(1.234, "en")) == ("1,23", "1.23")


def test_placeholders_are_filled_from_results():
    values = placeholder_values([make_result("cs", growth=0.12, months_up=9, trust="medium", seasonality=PEAK)], [], "uk")
    text = "Чехія: {cs.growth}, {cs.months_up}, довіра {cs.trust}, пік — {cs.peak_month}."
    assert render(text, values) == "Чехія: +12%, 9 з 12, довіра середня, пік — січень."


def test_unknown_placeholder_lists_valid_keys():
    with pytest.raises(NarrativeError, match="keys cs"):
        render("{pl.growth}", placeholder_values([make_result("cs")], [], "en"))


@pytest.mark.parametrize("text, found", [
    ("Інтерес виріс на 15%.", ["15%"]),
    ("Ріст у 9 з 12 місяців у 2025 році.", []),
    ("Близько 1 234 переглядів.", ["1 234"]),
    ("{cs.growth} за рік, {cs.views} на місяць.", []),
    ("Понад 150 читачів.", ["150"]),
])
def test_invented_numbers_are_found(text, found):
    assert invented_numbers(text) == found


NBSP, NNBSP = chr(0xA0), chr(0x202F)


@pytest.mark.parametrize("text, found", [
    (f"Було 10{NBSP}050{NBSP}000 переглядів.", [f"10{NBSP}050{NBSP}000"]),
    (f"Близько 10{NNBSP}050 переглядів.", [f"10{NNBSP}050"]),
    (f"Разом 1{NNBSP}250{NBSP}000 читачів.", [f"1{NNBSP}250{NBSP}000"]),
])
def test_invented_numbers_with_non_breaking_thousands_separators(text, found):
    assert invented_numbers(text) == found


def test_agent_text_with_invented_number_is_rejected_with_fix():
    values = placeholder_values([make_result("cs")], [], "uk")
    with pytest.raises(NarrativeError) as info:
        agent_texts("Виріс на 15%.", None, values)
    message = str(info.value)
    assert "'15%'" in message and "FIX" in message and "{cs.growth}" in message


def test_agent_text_is_rendered():
    values = placeholder_values([make_result("cs", growth=0.2)], [], "uk")
    assert agent_texts("Ріст {cs.growth}.", ["Дослідити {cs.title}."], values) == ("Ріст +20%.", ["Дослідити Article."])


def test_reason_text_includes_parameters():
    event = {"code": "event_driven", "level": "low", "date": "2026-03-10", "direction": "up"}
    assert reason_text(event, "uk") == "ріст пояснюється сплеском (2026-03-10)"
    assert reason_text({"code": "low_volume", "level": "low", "views": 85}, "en") == "low traffic (85/month)"


def test_template_summary_mentions_verdict_trust_season_and_ranking():
    results = [make_result("cs", growth=0.2, months_up=10, trust="low", seasonality=PEAK,
                           reasons=[{"code": "low_volume", "level": "low", "views": 85}]),
               make_result("pl", verdict="no_data", status="no_article")]
    ranking = [{"key": "cs", "position": 1, "score": 1.0, "ranks": {}, "trust": "low"}]
    text = template_summary(results, ranking, {"cs": "Чеська", "pl": "Польська"}, "uk")
    assert "Чеська: зростає — +20% за рік, ріст у 10 з 12 місяців; довіра низька: мало переглядів (85/міс.)." in text
    assert "Польська: даних немає — статті немає." in text
    assert "пік у січні — у 4 з 5 років" in text and "на першому місці — Чеська" in text


def test_template_steps_always_end_with_validation():
    results = [make_result("pl", verdict="no_data", status="no_article"),
               make_result("cs", trust="low", reasons=[{"code": "low_volume", "level": "low", "views": 50}])]
    steps = template_steps(results, [], {"pl": "Польська", "cs": "Чеська"}, "uk")
    assert steps[0].startswith("Немає статті: Польська.") and steps[1].startswith("Замало переглядів: Чеська.")
    assert steps[-1].startswith("Перевірте готовність платити") and len(steps) <= 4


def test_build_texts_prefers_agent_text_and_labels_by_language():
    study = parse_study({"question": "Порівняй", "topics": [{"label": "Т", "wikidata": "Q1"}], "languages": ["cs"],
                         "summary": "Ріст {cs.growth}."})
    texts = build_texts(study, [make_result("cs", growth=0.2)], [])
    assert texts["summary"] == "Ріст +20%." and texts["agent_text"] is True
    assert texts["labels"] == {"cs": "Чеська"} and texts["steps"][-1].startswith("Перевірте")
