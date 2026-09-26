"""End-to-end offline runs of the case scenarios on recorded API responses."""
import io
import json
import shutil
from pathlib import Path

STUDIES = Path(__file__).parent / "studies"
AS_OF = "2026-09-26"


def run_folder(folder, client):
    from witlib.cli import main

    out = io.StringIO()
    code = main(["run", str(folder), "--as-of", AS_OF], client=client, out=out, err=io.StringIO())
    return code, out.getvalue()


def prepare(name, tmp_path, form=None):
    folder = tmp_path / name
    folder.mkdir()
    if form is None:
        shutil.copy(STUDIES / f"{name}.json", folder / "study.json")
    else:
        (folder / "study.json").write_text(json.dumps(form, ensure_ascii=False), encoding="utf-8")
    return folder


def findings(folder):
    return json.loads((folder / "findings.json").read_text(encoding="utf-8"))


def pdf_pages(path):
    from pypdf import PdfReader

    return len(PdfReader(str(path)).pages)


def test_e1_reports_missing_polish_article_and_czech_trend(tmp_path, client):
    folder = prepare("e1_fasting", tmp_path)
    code, out = run_folder(folder, client)
    assert code == 0, out
    series = {s["key"]: s for s in findings(folder)["series"]}
    assert series["pl"]["status"] == "no_article"
    assert series["pl"]["verdict"] == "no_data"
    assert series["cs"]["status"] == "ok"
    assert series["cs"]["verdict"] in {"growing", "declining", "no_clear_trend"}
    assert series["cs"]["trust"] in {"high", "medium", "low"}
    assert pdf_pages(folder / "report.pdf") == 1
    assert len(out.strip().splitlines()) <= 25
    assert "no article" in out


def test_e2_counts_related_article(tmp_path, client):
    folder = prepare("e2_astronomy", tmp_path)
    code, out = run_folder(folder, client)
    assert code == 0, out
    (uk,) = findings(folder)["series"]
    assert uk["articles"][0] == "Астрономія"
    assert "Сонячна система" in uk["articles"]
    assert uk["seasonality"]["status"] in {"stable_peak", "no_stable_pattern", "low_volume", "insufficient_history"}
    assert pdf_pages(folder / "report.pdf") == 1


def test_e3_ranks_audiences_by_priorities(tmp_path, client):
    folder = prepare("e3_english", tmp_path)
    code, out = run_folder(folder, client)
    assert code == 0, out
    ranked = [row for row in findings(folder)["ranking"] if row["position"]]
    assert len(ranked) >= 2
    assert [row["position"] for row in ranked] == list(range(1, len(ranked) + 1))
    assert "RANKING" in out
    assert pdf_pages(folder / "report.pdf") == 1


def test_f1_follow_up_reuses_cached_data(tmp_path, client, fake_transport):
    folder = prepare("e1_fasting", tmp_path)
    assert run_folder(folder, client)[0] == 0
    form = json.loads((folder / "study.json").read_text(encoding="utf-8"))
    form["languages"].append("sk")
    (folder / "study.json").write_text(json.dumps(form, ensure_ascii=False), encoding="utf-8")
    before = len(fake_transport.calls)
    code, out = run_folder(folder, client)
    assert code == 0, out
    second_run = fake_transport.calls[before:]
    assert second_run, "a new language must be fetched"
    assert not [url for url in second_run if "cs.wikipedia.org" in url]
    assert {s["key"] for s in findings(folder)["series"]} == {"pl", "cs", "sk"}


def test_invented_number_in_agent_summary_is_rejected(tmp_path, client):
    form = json.loads((STUDIES / "e1_fasting.json").read_text(encoding="utf-8"))
    form["summary"] = "Інтерес у чеській виріс на 15%."
    folder = prepare("guard", tmp_path, form)
    code, out = run_folder(folder, client)
    assert code == 2
    assert "15%" in out and "FIX" in out
