import json
from datetime import date
from pathlib import Path

from witlib.series import collect_inputs, compute_periods, series_key
from witlib.study import parse_study

STUDIES = Path(__file__).resolve().parents[1] / "acceptance" / "studies"
PERIODS = compute_periods(date(2026, 9, 26), 24)


def inputs_for(name, client, **changes):
    form = json.loads((STUDIES / f"{name}.json").read_text(encoding="utf-8")) | changes
    return collect_inputs(client, parse_study(form), PERIODS)


def test_series_keys_depend_on_topic_and_language_count():
    assert series_key(1, "cs", 1, 2) == "cs"
    assert series_key(2, "cs", 2, 1) == "t2"
    assert series_key(2, "cs", 2, 3) == "t2.cs"


def test_missing_article_becomes_a_no_article_series(client):
    inputs, _warnings = inputs_for("e1_fasting", client)
    by_key = {i.key: i for i in inputs}
    assert by_key["pl"].status == "no_article" and not any(by_key["pl"].daily)
    cs = by_key["cs"]
    assert cs.status == "ok" and cs.title == "Přerušovaný půst" and cs.articles[0] == "Přerušovaný půst"
    assert len(cs.daily) == len(cs.days) == 1826 and sum(cs.daily) > 0
    assert set(cs.project) == set(PERIODS.history_months)


def test_related_articles_are_added_to_the_series(client):
    (uk,), _ = inputs_for("e2_astronomy", client)
    assert uk.articles[:2] == ["Астрономія", "Сонячна система"]
    assert sum(uk.daily) > sum(uk.main_daily) > 0


def test_one_topic_many_languages_are_keyed_by_language(client):
    inputs, _ = inputs_for("e3_english", client)
    assert [i.key for i in inputs] == ["pl", "cs", "uk", "tr", "id"]
