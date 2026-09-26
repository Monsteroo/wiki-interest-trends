"""The study form (study.json): parsing, defaults and validation with actionable errors."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from .languages import normalize_language

QID_RE = re.compile(r"^Q\d+$")
CYRILLIC_RE = re.compile(r"[Ѐ-ӿ]")
KNOWN_FIELDS = {"question", "topics", "languages", "months", "measure", "priorities", "report_language", "summary", "next_steps"}
PRIORITY_KEYS = ("growth", "interest", "reach")


@dataclass
class Topic:
    label: str
    wikidata: str
    related: list[str] = field(default_factory=list)
    substitutes: dict[str, str] = field(default_factory=dict)


@dataclass
class Study:
    question: str
    topics: list[Topic]
    languages: list[str]
    months: int = 24
    measure: str = "share"
    priorities: dict[str, float] | None = None
    report_language: str = "en"
    summary: str | None = None
    next_steps: list[str] | None = None
    warnings: list[str] = field(default_factory=list)


class StudyError(ValueError):
    """Invalid study form; carries every problem with a concrete fix."""

    def __init__(self, problems: list[tuple[str, str, str]]):
        self.problems = problems
        super().__init__(self.format())

    def format(self) -> str:
        lines = []
        for number, (where, problem, fix) in enumerate(self.problems, 1):
            lines.append(f"{number}. ERROR: {where}: {problem}")
            lines.append(f"   FIX: {fix}")
        return "\n".join(lines)


def load_study(path: str | Path) -> tuple[Study, Path]:
    """Load study.json from a folder or a file path; return the study and its folder."""
    path = Path(path)
    file = path / "study.json" if path.is_dir() else path
    if not file.exists():
        raise StudyError([("study.json", f"not found at {file}", 'Create it with: scripts/wit resolve "<topic>" --langs <codes> --save <folder>')])
    try:
        data = json.loads(file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise StudyError([("study.json", f"is not valid JSON ({exc.msg}, line {exc.lineno}, column {exc.colno})", "Fix quotes, commas and brackets, then run again")]) from exc
    return parse_study(data), file.parent


def parse_study(data: object) -> Study:
    if not isinstance(data, dict):
        raise StudyError([("study.json", "must be a JSON object", "Start from assets/study-template.json")])
    problems: list[tuple[str, str, str]] = []
    warnings = [f"unknown field '{key}' ignored" for key in data if key not in KNOWN_FIELDS]
    question = _question(data.get("question"), problems)
    languages = _languages(data.get("languages"), problems)
    topics = _topics(data.get("topics"), languages, problems)
    if topics and languages and len(topics) * len(languages) > 8:
        problems.append(("topics x languages", f"{len(topics)} x {len(languages)} = {len(topics) * len(languages)} series (max 8)", "Remove topics or languages, or split into two studies"))
    months = data.get("months", 24)
    if not isinstance(months, int) or isinstance(months, bool) or not 12 <= months <= 120:
        problems.append(("months", f"{months!r} must be a whole number from 12 to 120", 'Use 24 for "the last two years"'))
    measure = data.get("measure", "share")
    if measure not in ("share", "views"):
        problems.append(("measure", f"{measure!r} is not supported", 'Use "share" (default) or "views"'))
    priorities = _priorities(data.get("priorities"), problems)
    report_language = data.get("report_language") or ("uk" if CYRILLIC_RE.search(question) else "en")
    if report_language not in ("uk", "en"):
        problems.append(("report_language", f"{report_language!r} is not supported", 'Use "uk" or "en"'))
    summary = data.get("summary")
    if summary is not None and (not isinstance(summary, str) or len(summary) > 600):
        problems.append(("summary", "must be a text of up to 600 characters", "Shorten it; take numbers from placeholders such as {cs.growth}"))
    next_steps = data.get("next_steps")
    if next_steps is not None and (not isinstance(next_steps, list) or len(next_steps) > 5 or any(not isinstance(s, str) or len(s) > 200 for s in next_steps)):
        problems.append(("next_steps", "must be a list of up to 5 texts of up to 200 characters", "Keep 2-4 short action items"))
    if problems:
        raise StudyError(problems)
    return Study(question=question, topics=topics, languages=languages, months=months, measure=measure,
                 priorities=priorities, report_language=report_language, summary=summary,
                 next_steps=next_steps, warnings=warnings)


def _question(value, problems) -> str:
    if not isinstance(value, str) or not value.strip():
        problems.append(("question", "is missing or empty", 'Copy the user\'s question verbatim into "question"'))
        return ""
    if len(value) > 500:
        problems.append(("question", f"has {len(value)} characters (max 500)", "Keep the core of the user's question"))
    return value.strip()


def _languages(value, problems) -> list[str]:
    if not isinstance(value, list) or not value:
        problems.append(("languages", "must be a non-empty list", 'Use Wikipedia codes, e.g. ["pl", "cs"]'))
        return []
    codes: list[str] = []
    for item in value:
        try:
            code = normalize_language(str(item))
        except ValueError as exc:
            problems.append(("languages", str(exc), 'Use Wikipedia language codes such as "pl", "cs", "uk"'))
            continue
        if code not in codes:
            codes.append(code)
    if len(codes) > 8:
        problems.append(("languages", f"has {len(codes)} languages (max 8)", "Split the study into two studies"))
    return codes


def _topics(value, languages, problems) -> list[Topic]:
    if not isinstance(value, list) or not value:
        problems.append(("topics", "must be a non-empty list", "Run scripts/wit resolve and copy the topic it prints"))
        return []
    if len(value) > 3:
        problems.append(("topics", f"has {len(value)} topics (max 3)", "Keep at most 3 topics per study"))
        return []
    topics = []
    for number, raw in enumerate(value, 1):
        where = f"topics[{number}]"
        if not isinstance(raw, dict):
            problems.append((where, "must be an object", 'Use {"label": "...", "wikidata": "Q..."}'))
            continue
        label = raw.get("label")
        if not isinstance(label, str) or not label.strip() or len(label) > 80:
            problems.append((f"{where}.label", "must be a text of 1-80 characters", "Give the topic a short name for the report"))
        qid = raw.get("wikidata")
        if not isinstance(qid, str) or not QID_RE.match(qid):
            problems.append((f"{where}.wikidata", f"{qid!r} is not a Wikidata id like Q1666254", 'Run: scripts/wit resolve "<topic>" --langs <codes>'))
        related = raw.get("related", [])
        if not isinstance(related, list) or len(related) > 10 or any(not isinstance(r, str) or not QID_RE.match(r) for r in related):
            problems.append((f"{where}.related", "must be a list of up to 10 Wikidata ids", 'Example: ["Q544", "Q4213"]'))
            related = []
        substitutes = _substitutes(raw.get("substitutes", {}), where, languages, problems)
        topics.append(Topic(label=str(label or "").strip(), wikidata=str(qid), related=list(dict.fromkeys(related)), substitutes=substitutes))
    return topics


def _substitutes(value, where, languages, problems) -> dict[str, str]:
    if not isinstance(value, dict):
        problems.append((f"{where}.substitutes", "must be an object {language: article title}", 'Example: {"pl": "Głodówka lecznicza"}'))
        return {}
    result = {}
    for lang, title in value.items():
        try:
            code = normalize_language(str(lang))
        except ValueError as exc:
            problems.append((f"{where}.substitutes", str(exc), 'Use a language code from "languages"'))
            continue
        if languages and code not in languages:
            problems.append((f"{where}.substitutes", f"language '{code}' is not in \"languages\"", f'Add "{code}" to "languages" or remove this substitute'))
        if not isinstance(title, str) or not title.strip():
            problems.append((f"{where}.substitutes.{code}", "article title is empty", "Use an exact article title printed by resolve"))
            continue
        result[code] = title.strip()
    return result


def _priorities(value, problems) -> dict[str, float] | None:
    if value is None:
        return None
    valid = (isinstance(value, dict) and not set(value) - set(PRIORITY_KEYS)
             and all(isinstance(v, (int, float)) and not isinstance(v, bool) and v >= 0 for v in value.values())
             and sum(value.values()) > 0)
    if not valid:
        problems.append(("priorities", "must map growth/interest/reach to non-negative numbers with a positive sum", 'Example: {"growth": 0.5, "interest": 0.3, "reach": 0.2}'))
        return None
    total = sum(value.values())
    return {key: value.get(key, 0) / total for key in PRIORITY_KEYS}
