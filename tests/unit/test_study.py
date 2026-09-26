import json

import pytest

from witlib.study import StudyError, load_study, parse_study

VALID = {"question": "Порівняй інтерес", "topics": [{"label": "Тема", "wikidata": "Q1666254"}], "languages": ["pl", "cs"]}


def form(**changes):
    data = json.loads(json.dumps(VALID))
    data.update(changes)
    return data


def problems_of(data):
    with pytest.raises(StudyError) as info:
        parse_study(data)
    return info.value.problems


def test_minimal_form_gets_defaults():
    study = parse_study(form())
    assert (study.months, study.measure, study.priorities, study.report_language) == (24, "share", None, "uk")
    assert study.topics[0].related == [] and study.topics[0].substitutes == {}


def test_report_language_defaults_to_english_for_latin_question():
    assert parse_study(form(question="Compare interest")).report_language == "en"


def test_missing_question_has_fix():
    (problem,) = problems_of(form(question=""))
    assert problem[0] == "question" and "verbatim" in problem[2]


def test_language_names_are_normalised():
    assert parse_study(form(languages=["Polish", "чеська"])).languages == ["pl", "cs"]


def test_unknown_language_is_reported_with_hint():
    (problem,) = problems_of(form(languages=["polsih"]))
    assert "did you mean 'pl'" in problem[1]


def test_all_problems_are_reported_at_once():
    fields = [p[0] for p in problems_of(form(topics=[], months=5, measure="clicks"))]
    assert fields == ["topics", "months", "measure"]


def test_bad_wikidata_id_points_to_resolve():
    (problem,) = problems_of(form(topics=[{"label": "Тема", "wikidata": "intermittent fasting"}]))
    assert problem[0] == "topics[1].wikidata" and "resolve" in problem[2]


def test_substitute_language_must_be_studied():
    data = form(topics=[{"label": "Тема", "wikidata": "Q1", "substitutes": {"de": "Fasten"}}])
    (problem,) = problems_of(data)
    assert "not in \"languages\"" in problem[1]


def test_substitutes_are_normalised_and_kept():
    data = form(topics=[{"label": "Тема", "wikidata": "Q1", "substitutes": {"Polish": "Głodówka lecznicza"}}])
    assert parse_study(data).topics[0].substitutes == {"pl": "Głodówka lecznicza"}


def test_priorities_are_normalised_to_sum_one():
    study = parse_study(form(priorities={"growth": 2, "interest": 1, "reach": 1}))
    assert study.priorities == {"growth": 0.5, "interest": 0.25, "reach": 0.25}


def test_too_many_series_is_rejected():
    topics = [{"label": f"T{i}", "wikidata": f"Q{i}"} for i in range(1, 4)]
    fields = [p[0] for p in problems_of(form(topics=topics, languages=["pl", "cs", "uk"]))]
    assert fields == ["topics x languages"]


def test_long_summary_is_rejected():
    assert problems_of(form(summary="x" * 601))[0][0] == "summary"


def test_unknown_field_is_only_a_warning():
    assert parse_study(form(colour="red")).warnings == ["unknown field 'colour' ignored"]


def test_error_format_is_numbered_with_fix():
    text = StudyError([("question", "is missing or empty", "Copy it")]).format()
    assert text == "1. ERROR: question: is missing or empty\n   FIX: Copy it"


def test_load_study_from_folder_and_invalid_json(tmp_path):
    (tmp_path / "study.json").write_text(json.dumps(form(), ensure_ascii=False), encoding="utf-8")
    study, folder = load_study(tmp_path)
    assert folder == tmp_path and study.languages == ["pl", "cs"]
    (tmp_path / "study.json").write_text("{bad", encoding="utf-8")
    with pytest.raises(StudyError, match="not valid JSON"):
        load_study(tmp_path)
