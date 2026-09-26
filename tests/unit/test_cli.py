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
