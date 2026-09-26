"""Checks for one eval scenario: artifacts in its work folder and the agent's final answer (answer.md).

Usage: python evals/check.py [evals/workdir]   prints a table for every scenario folder found.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TRUST_WORDS = ("довір", "trust")
LIMIT_WORDS = ("обмежен", "≠", "не дорівнює", "готовність платити", "непрям", "проксі", "замінник", "не країна",
               "limitation", "willingness to pay", "proxy", "indirect", "not the same")
PERCENT_RE = re.compile(r"([+\-−–]?)\s?(\d+(?:[.,]\d+)?)\s?%")


def percents_in(text: str) -> set[int]:
    return {round(float(number.replace(",", "."))) for _sign, number in PERCENT_RE.findall(text)}


def allowed_percents(findings: dict, study: dict) -> set[int]:
    allowed = {0}
    for series in findings.get("series", []):
        for key in ("growth", "growth_views", "growth_share", "growth_clean", "window_growth"):
            value = series.get("metrics", {}).get(key)
            if value is not None:
                allowed.add(abs(round(value * 100)))
    priorities = study.get("priorities") or {}
    total = sum(priorities.values()) or 1
    for value in priorities.values():
        allowed |= {round(value * 100), round(value / total * 100)}
    return allowed


def latest_study(workdir: Path) -> Path | None:
    forms = sorted(workdir.glob("wiki-studies/*/study.json"), key=lambda p: p.stat().st_mtime)
    return forms[-1].parent if forms else None


def _e1(answer, study, findings):
    pl = {s["key"]: s for s in findings.get("series", [])}.get("pl")
    if pl is None:
        return ["pl series missing"]
    if pl["status"] == "no_article" and not any(w in answer for w in ("немає", "відсутн", "no article", "не має")):
        return ["answer does not say the Polish article is missing"]
    if pl.get("substitute") and not any(w in answer for w in ("замінник", "substitute", "непрям", "proxy")):
        return ["answer does not flag the substitute"]
    return []


def _e3(answer, study, findings):
    failures = [] if [r for r in findings.get("ranking", []) if r.get("position")] else ["no ranking computed"]
    if not any(w in answer for w in ("непрям", "проксі", "proxy", "indirect", "замінник")):
        failures.append("answer does not say the English-language article is an indirect measure")
    return failures


def _f1(answer, study, findings):
    return [] if "sk" in study.get("languages", []) else ["sk not added to languages"]


def _f2(answer, study, findings):
    p = study.get("priorities") or {}
    return [] if p and p.get("growth", 0) > max(p.get("interest", 0), p.get("reach", 0)) else ["priorities.growth is not the largest weight"]


def _t1(answer, study, findings):
    named = any(w in answer for w in ("планет", "елемент", "бог", "planet", "element", "god"))
    return [] if ("?" in answer or named) else ["answer neither asks which Mercury nor names the chosen meaning"]


def _t2(answer, study, findings):
    has_spikes = any(s.get("spikes") for s in findings.get("series", []))
    mentioned = any(w in answer for w in ("сплеск", "затемнен", "поді", "spike", "eclipse", "event"))
    return [] if (not has_spikes or mentioned) else ["spikes were found but the answer does not mention them"]


SPECIFIC = {"E1": _e1, "E3": _e3, "F1": _f1, "F2": _f2, "T1": _t1, "T2": _t2}


def check_scenario(scenario: dict, workdir: Path) -> list[str]:
    answer_file = workdir / "answer.md"
    if not answer_file.exists():
        return ["answer.md missing"]
    answer = answer_file.read_text(encoding="utf-8")
    folder = latest_study(workdir)
    if folder is None:
        if scenario.get("clarification_ok") and "?" in answer:
            return []
        return ["no wiki-studies/*/study.json was created"]
    study = json.loads((folder / "study.json").read_text(encoding="utf-8"))
    findings_file = folder / "findings.json"
    findings = json.loads(findings_file.read_text(encoding="utf-8")) if findings_file.exists() else {}
    failures = [] if findings else ["findings.json missing: the run did not finish"]
    pdf = folder / "report.pdf"
    if not pdf.exists():
        failures.append("report.pdf missing")
    else:
        from pypdf import PdfReader

        pages = len(PdfReader(str(pdf)).pages)
        if pages > 2:
            failures.append(f"report.pdf has {pages} pages")
    low = answer.lower()
    if not any(word in low for word in TRUST_WORDS):
        failures.append("answer does not state trust")
    if not any(word in low for word in LIMIT_WORDS):
        failures.append("answer names no limitation")
    unknown = sorted(percents_in(answer) - allowed_percents(findings, study)) if findings else []
    if unknown:
        failures.append(f"percentages not found in findings: {unknown}")
    return failures + SPECIFIC.get(scenario["id"], lambda *_: [])(low, study, findings)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    root = Path(args[0]) if args else HERE / "workdir"
    scenarios = json.loads((HERE / "scenarios.json").read_text(encoding="utf-8"))
    lines, failed = ["| scenario | result | details |", "|---|---|---|"], 0
    for scenario in scenarios:
        workdir = root / scenario["id"]
        if not workdir.exists():
            lines.append(f"| {scenario['id']} | skipped | no work folder |")
            continue
        failures = check_scenario(scenario, workdir)
        failed += bool(failures)
        lines.append(f"| {scenario['id']} | {'FAIL' if failures else 'PASS'} | {'; '.join(failures)} |")
    print("\n".join(lines))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
