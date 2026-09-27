import json
import sys
from pathlib import Path

from fpdf import FPDF

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "evals"))
from check import _t2, allowed_percents, check_scenario, percents_in  # noqa: E402

GOOD = "Інтерес у чеській зріс на 12% за рік, довіра середня. Обмеження: мова ≠ країна."


def workdir(tmp_path, answer, pages=1):
    folder = tmp_path / "wiki-studies" / "s1"
    folder.mkdir(parents=True)
    (folder / "study.json").write_text(json.dumps({"languages": ["cs"]}), encoding="utf-8")
    findings = {"series": [{"key": "cs", "status": "ok", "metrics": {"growth": 0.12, "growth_clean": 0.05}, "spikes": []}], "ranking": []}
    (folder / "findings.json").write_text(json.dumps(findings), encoding="utf-8")
    pdf = FPDF()
    for _ in range(pages):
        pdf.add_page()
    pdf.output(str(folder / "report.pdf"))
    (tmp_path / "answer.md").write_text(answer, encoding="utf-8")
    return tmp_path


def test_percentages_are_read_from_text():
    assert percents_in("+12 %, −5% і 0,5%") == {12, 5, 0}


def test_allowed_percentages_come_from_findings_and_priorities():
    findings = {"series": [{"metrics": {"growth": -0.123, "growth_clean": None}}]}
    assert allowed_percents(findings, {"priorities": {"growth": 0.6, "reach": 0.4}}) >= {0, 12, 60, 40}


def test_allowed_percentages_include_seasonal_uplift():
    findings = {"series": [{"metrics": {}, "seasonality": {"status": "stable_peak", "uplift": 0.713}}]}
    assert allowed_percents(findings, {}) >= {71}


def test_allowed_percentages_do_not_crash_on_missing_metrics_or_seasonality():
    findings = {"series": [{"metrics": None}, {}]}
    assert allowed_percents(findings, {}) == {0}


def test_t2_accepts_the_word_spike():
    findings = {"series": [{"spikes": [{"date": "2026-08-12", "views": 100}]}]}
    assert _t2("сплеск переглядів у серпні", {}, findings) == []


def test_t2_accepts_the_date_of_the_biggest_spike_without_a_keyword():
    findings = {"series": [{"spikes": [{"date": "2026-08-11", "views": 50}, {"date": "2026-08-12", "views": 100}]}]}
    assert _t2("зростання пов'язане з 2026-08-12", {}, findings) == []


def test_t2_no_longer_accepts_generic_event_words():
    findings = {"series": [{"spikes": [{"date": "2026-08-12", "views": 100}]}]}
    failures = _t2("зростання через глобальну подію без деталей", {}, findings)
    assert failures == ["spikes were found but the answer does not mention them"]


def test_good_answer_passes(tmp_path):
    assert check_scenario({"id": "E2"}, workdir(tmp_path, GOOD)) == []


def test_invented_percentage_is_caught(tmp_path):
    assert check_scenario({"id": "E2"}, workdir(tmp_path, GOOD + " Прогноз: +35%.")) == ["percentages not found in findings: [35]"]


def test_missing_trust_limitation_and_extra_pages_are_caught(tmp_path):
    failures = check_scenario({"id": "E2"}, workdir(tmp_path, "Росте на 12%.", pages=3))
    assert failures == ["report.pdf has 3 pages", "answer does not state trust", "answer names no limitation"]


def test_clarifying_question_passes_when_allowed(tmp_path):
    (tmp_path / "answer.md").write_text("Який Меркурій вас цікавить: планета чи хімічний елемент?", encoding="utf-8")
    assert check_scenario({"id": "T1", "clarification_ok": True}, tmp_path) == []
