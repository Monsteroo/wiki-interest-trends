import io
import json

from witlib.api import ApiClient, Response
from witlib.cli import main
from witlib.study import parse_study


def run(argv, client):
    out = io.StringIO()
    code = main(argv, client=client, out=out, err=io.StringIO())
    return code, out.getvalue()


def test_resolve_prints_topic_articles_and_related(client):
    code, out = run(["resolve", "інтервальне голодування", "--langs", "pl,cs"], client)
    assert code == 0, out
    assert "TOPIC     Q1666254  Інтервальне голодування" in out
    assert "pl  — no article" in out and "cs  Přerušovaný půst" in out and "RELATED" in out
    assert len(out.splitlines()) <= 30


def test_resolve_save_writes_a_valid_form(client, tmp_path):
    folder = tmp_path / "fasting"
    argv = ["resolve", "інтервальне голодування", "--langs", "pl,cs", "--question", "Порівняй інтерес", "--save", str(folder)]
    code, out = run(argv, client)
    assert code == 0, out
    study = parse_study(json.loads((folder / "study.json").read_text(encoding="utf-8")))
    assert study.topics[0].wikidata == "Q1666254" and study.languages == ["pl", "cs"]


def test_resolve_rejects_unknown_language(client):
    code, out = run(["resolve", "x", "--langs", "polsih"], client)
    assert code == 2 and "did you mean 'pl'" in out


def test_run_without_form_explains_how_to_create_it(client, tmp_path):
    code, out = run(["run", str(tmp_path)], client)
    assert code == 2 and "ERROR: study.json" in out and "FIX" in out


def test_network_failure_exits_with_code_3(tmp_path):
    form = {"question": "q", "topics": [{"label": "T", "wikidata": "Q1"}], "languages": ["cs"]}
    (tmp_path / "study.json").write_text(json.dumps(form), encoding="utf-8")
    client = ApiClient(transport=lambda url, headers: Response(503, "", {}), cache_dir=tmp_path / "cache",
                       sleep=lambda s: None, max_attempts=2)
    code, out = run(["run", str(tmp_path), "--as-of", "2026-09-26"], client)
    assert code == 3 and "FIX" in out


def test_summary_mentions_extra_pages(tmp_path):
    from datetime import date

    from helpers import make_result
    from witlib.cli import _summary
    from witlib.narrative import build_texts
    from witlib.series import compute_periods
    from witlib.study import parse_study

    study = parse_study({"question": "q", "topics": [{"label": "T", "wikidata": "Q1"}], "languages": ["cs"]})
    results = [make_result("cs")]
    texts = build_texts(study, results, [])
    periods = compute_periods(date(2026, 9, 26), 24)
    two = _summary(study, periods, results, [], [], tmp_path, texts, pages=2)
    one = _summary(study, periods, results, [], [], tmp_path, texts)
    assert any("2 pages" in line for line in two if line.startswith("FILES"))
    assert not any("pages" in line for line in one if line.startswith("FILES"))


def _run_summary(tmp_path, results):
    from datetime import date

    from witlib.narrative import build_texts
    from witlib.series import compute_periods
    from witlib.study import parse_study

    study = parse_study({"question": "q", "topics": [{"label": "T", "wikidata": "Q1"}], "languages": ["cs"]})
    texts = build_texts(study, results, [])
    periods = compute_periods(date(2026, 9, 26), 24)
    from witlib.cli import _summary
    lines = _summary(study, periods, results, [], [], tmp_path, texts)
    return next(line for line in lines if line.strip().startswith("cs"))


def test_summary_lists_top_three_spikes_by_views_largest_first(tmp_path):
    from helpers import make_result

    spikes = [
        {"date": "2026-01-05", "views": 100, "typical": 10},
        {"date": "2026-02-05", "views": 500, "typical": 10},
        {"date": "2026-03-05", "views": 300, "typical": 10},
        {"date": "2026-04-05", "views": 200, "typical": 10},
        {"date": "2026-05-05", "views": 150, "typical": 10},
    ]
    line = _run_summary(tmp_path, [make_result("cs", spikes=spikes)])
    assert "spikes: 2026-02-05, 2026-03-05, 2026-04-05 (+2 more)" in line


def test_summary_has_no_spikes_text_when_series_has_none(tmp_path):
    from helpers import make_result

    line = _run_summary(tmp_path, [make_result("cs", spikes=[])])
    assert "spikes:" not in line


def test_summary_shows_seasonal_uplift_with_stable_peak(tmp_path):
    from helpers import make_result

    seasonality = {"status": "stable_peak", "peak_month": 9, "peak_years": 3, "cycles": 5, "uplift": 0.713}
    line = _run_summary(tmp_path, [make_result("cs", seasonality=seasonality)])
    assert "peak September +71% (3/5 years)" in line


def test_next_line_mentions_spikes_when_summary_lacks_agent_text(tmp_path):
    from helpers import make_result
    from witlib.cli import _summary
    from witlib.narrative import build_texts
    from witlib.series import compute_periods
    from witlib.study import parse_study
    from datetime import date

    study = parse_study({"question": "q", "topics": [{"label": "T", "wikidata": "Q1"}], "languages": ["cs"]})
    results = [make_result("cs")]
    texts = build_texts(study, results, [])
    periods = compute_periods(date(2026, 9, 26), 24)
    lines = _summary(study, periods, results, [], [], tmp_path, texts)
    next_line = next(line for line in lines if line.startswith("NEXT"))
    assert next_line == ("NEXT     answer: verdict, growth, trust + reason, spikes if listed, one limitation, report path; "
                          "copy numbers exactly. Optional: add summary/next_steps with {key.metric} placeholders and run again")
