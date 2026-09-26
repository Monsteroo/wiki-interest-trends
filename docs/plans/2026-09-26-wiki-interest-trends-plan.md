# wiki-interest-trends — план реалізації

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Навичка у форматі Agent Skills: агент на Haiku 4.5 заповнює бланк дослідження, а Python-код навички завантажує перегляди Wikipedia, рахує ріст, довіру, сезонність і рейтинг, будує графіки і PDF на одну сторінку.

**Architecture:** варіант C з [ADR-001](../adr/0001-architecture.md): «бланк `study.json` + рушій». Дві команди CLI (`resolve`, `run`), пакет `scripts/witlib/` із модулями з однією відповідальністю, чисті функції аналізу, мережа лише через `ApiClient` із підмінним транспортом.

**Tech Stack:** Python ≥ 3.12, requests, matplotlib (Agg), fpdf2, pytest, pypdf. Wikimedia Pageviews API, Wikidata API, MediaWiki Action API.

**Специфікація:** [docs/specs/2026-09-26-wiki-interest-trends-design.md](../specs/2026-09-26-wiki-interest-trends-design.md)

## Global Constraints

- Python ≥ 3.12; усі команди запускаються з кореня навички `wiki-interest-trends/`.
- Runtime-залежності мають точні версії: `requests==2.34.2`, `matplotlib==3.11.2`, `fpdf2==2.8.8`. Dev: `pytest==9.1.1`, `pypdf==6.19.0`.
- Скомпільованих файлів у навичці немає. Весь власний код і матеріали лежать у теці навички.
- `name: wiki-interest-trends` збігається з назвою теки. `description` ≤ 1024 символів, `compatibility` ≤ 500, SKILL.md < 500 рядків.
- До API — лише послідовні запити: пауза ≥ 0,35 с, User-Agent `wiki-interest-trends/<версія> (<контакт>) python-requests/<версія>`, не більше 4 спроб на 429/5xx, не більше 400 запитів за запуск.
- Pageviews: `agent=user`, `access=all-access`, лише повні місяці; якщо `as_of` припадає на 1-ше або 2-ге число, беремо ще на місяць раніше. Історія — 60 місяців, але не раніше 2015-07.
- Пороги методики (спека §7): вердикт ±10% і ≥ 7 з 12 місяців; довіра R1 < 100 → low, < 500 → medium; R2 7–8 → medium; R3 подія → low; R4 нова стаття → low; R5 замінник → medium. Сплеск — `≥ 20` і `> max(5·med, med + 10·MAD)` за 28 попередніх днів. Сезонність стабільна, якщо пік повторюється у ≥ 60% циклів і профіль ≥ 1.20, при ≥ 3 циклах.
- Бланк: ≤ 3 теми, ≤ 8 мов, тем × мов ≤ 8, `months` 12–120, `summary` ≤ 600 символів, `next_steps` ≤ 5 × 200.
- Коди виходу: 0 — успіх, 2 — помилка бланку або тексту, 3 — мережа, 4 — немає даних, 5 — середовище.
- Вижимка `run` — не більше 25 рядків. PDF — A4, мета — 1 сторінка: при переповненні шрифти зменшуються до мінімумів; якщо й тоді не вміщується, звіт займає 2 сторінки, текст не обрізається, а `run` показує кількість сторінок (рішення користувача). Шрифт DejaVu; «Головне» і «Що робити далі» ніколи не дрібніші за 7 pt, а таблиця, бічний блок і футер (дрібний друк) — за 5,5 pt.
- TDD: кожне завдання — тест, що падає → мінімальний код → тест проходить → коміт. Погоджені винятки: конфігурація (`requirements*.txt`, `pytest.ini`, обгортка `scripts/wit`), зовнішній вигляд графіків і PDF, текст `SKILL.md` (його перевіряють сценарії на Haiku).
- У тестах підміняємо лише HTTP-транспорт; записані відповіді повні й справжні; невідомий URL — помилка.
- Кожен коміт закінчується рядком `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Рішення, які треба підтвердити до старту

- **Контакт у User-Agent** (відкрите питання 1 специфікації): за замовчуванням `DEFAULT_CONTACT = "https://github.com/Monsteroo/wiki-interest-trends"` в `scripts/witlib/api.py` (Task 3). Змінюється одним рядком або змінною `WIT_CONTACT`.
- **Як запускати Haiku** (відкрите питання 2): варіант A — CLI Claude Code (`evals/run_evals.py`), варіант B — Haiku-субагент із цієї сесії (Task 17, крок 5). Від вибору залежать лише Task 17–18.

## Структура файлів

```
wiki-interest-trends/
├── SKILL.md                        T18  інструкція для агента
├── README.md, LICENSE              T15  для людей
├── requirements.in                 T1   прямі runtime-залежності
├── requirements.txt                T1   повний lock (pip freeze)
├── requirements-dev.txt            T1   + pytest, pypdf
├── pytest.ini, .gitignore          T1
├── scripts/
│   ├── wit                         T14  bash-обгортка: uv або venv
│   ├── wit.py                      T14  точка входу
│   └── witlib/
│       ├── __init__.py             T1   __version__
│       ├── languages.py            T2   мови: код ↔ назви
│       ├── study.py                T2   бланк: перевірка, помилки з FIX
│       ├── api.py                  T3   HTTP-клієнт: UA, пауза, повтори, кеш
│       ├── series.py               T4, T10  періоди, завантаження, ряди, збір входів
│       ├── analysis.py             T5, T6, T8  ріст, сплески, довіра, вердикт, аналіз ряду, рейтинг
│       ├── seasonality.py          T7   сезонність
│       ├── resolve.py              T9   Wikidata, статті, неоднозначність, замінники, morelike
│       ├── narrative.py            T11  тексти uk/en, плейсхолдери, запобіжник чисел
│       ├── charts.py               T12  графіки
│       ├── report.py               T13  PDF на 1 сторінку
│       └── cli.py                  T14  команди resolve/run, вижимка
├── references/                     T15  methodology.md, study-fields.md, roadmap.md
├── assets/study-template.json      T15
├── tests/
│   ├── helpers.py, conftest.py     T1   FakeTransport, фабрики даних
│   ├── fixtures/record.py          T9, T10  запис справжніх відповідей
│   ├── fixtures/http/*.json        T9, T10  записані відповіді
│   ├── unit/test_*.py              T2–T14, T17, T18
│   ├── acceptance/                 T1   сценарії E1–E3, F1, запобіжник
│   └── live/                       T16
├── evals/                          T17  scenarios.json, check.py, run_evals.py, results/
└── docs/                           specs/, plans/, adr/, verification.md (T16, T18)
```

Залежності модулів: `analysis → series, seasonality`; `series → api, resolve, study`; `resolve → api`; `report → charts, narrative`; `narrative → languages`; `study → languages`; `cli → усі`.

---

### Task 1: Каркас, тестове середовище і приймальні тести (червоні)

**Files:**
- Create: `requirements.in`, `requirements.txt` (генерується), `requirements-dev.txt`, `pytest.ini`, `.gitignore`
- Create: `scripts/witlib/__init__.py`
- Create: `tests/helpers.py`, `tests/conftest.py`
- Create: `tests/acceptance/studies/e1_fasting.json`, `e2_astronomy.json`, `e3_english.json`
- Test: `tests/acceptance/test_run_offline.py`

**Interfaces:**
- Consumes: —
- Produces: `helpers.fixture_path(url) -> Path`, `helpers.FakeTransport(extra: dict[str, Response | list[Response]] | None)` (атрибути `calls: list[str]`, `headers: list[dict]`), `helpers.synthetic_input(...)`, `helpers.make_result(...)`, pytest-фікстури `fake_transport`, `client` (`ApiClient` з тимчасовим кешем і без пауз). Приймальні тести викликають `witlib.cli.main(argv, *, client, out, err) -> int`.

- [ ] **Step 1: Конфігурація**

`requirements.in`:
```
requests==2.34.2
matplotlib==3.11.2
fpdf2==2.8.8
```

`requirements-dev.txt`:
```
-r requirements.txt
pytest==9.1.1
pypdf==6.19.0
```

`pytest.ini`:
```ini
[pytest]
testpaths = tests
pythonpath = scripts tests
markers =
    live: calls the real Wikimedia APIs (run explicitly: pytest -m live)
addopts = -q -m "not live"
```

`.gitignore`:
```
__pycache__/
*.pyc
.pytest_cache/
.venv/
wiki-studies/
evals/workdir/
```

`scripts/witlib/__init__.py`:
```python
"""wiki-interest-trends: Wikipedia pageview analysis for product decisions."""

__version__ = "1.0.0"
```

- [ ] **Step 2: Середовище і lock-файл**

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --quiet -r requirements.in
.venv/bin/python -m pip freeze > requirements.txt
.venv/bin/python -m pip install --quiet -r requirements-dev.txt
.venv/bin/python -c "import requests, matplotlib, fpdf, pytest, pypdf; print('ok')"
```
Очікувано: `ok`. `requirements.txt` містить точні версії всіх runtime-пакетів (requests, matplotlib, fpdf2, numpy, pillow, fonttools, …) і нічого з dev.

- [ ] **Step 3: Тестові утиліти**

`tests/helpers.py`:
```python
"""Shared test utilities: replay of recorded HTTP responses and synthetic data builders."""
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures" / "http"


def fixture_path(url: str) -> Path:
    """Recorded responses are gzip-compressed JSON files named by a hash of the URL."""
    return FIXTURES / (hashlib.sha256(url.encode("utf-8")).hexdigest()[:24] + ".json.gz")


class FakeTransport:
    """Replays complete recorded responses by URL; an unknown URL fails the test loudly."""

    def __init__(self, extra=None):
        self.extra = dict(extra or {})
        self.calls: list[str] = []
        self.headers: list[dict] = []

    def __call__(self, url, headers):
        from witlib.api import Response

        self.calls.append(url)
        self.headers.append(dict(headers))
        if url in self.extra:
            item = self.extra[url]
            return item.pop(0) if isinstance(item, list) else item
        path = fixture_path(url)
        if not path.exists():
            raise AssertionError(f"no recorded response for {url} ({path.name}); run: .venv/bin/python tests/fixtures/record.py")
        data = json.loads(gzip.decompress(path.read_bytes()).decode("utf-8"))
        return Response(status=data["status"], body=data["body"], headers=data.get("headers", {}))


def synthetic_input(periods, per_day, *, project=10_000_000, key="cs", lang="cs", status="ok", substitute=False, main_per_day=None, title="Article"):
    """SeriesInput over the whole history; per_day(iso_date) -> views, project: int or month -> int."""
    from witlib.series import SeriesInput, day_list

    days = day_list(periods.history_start, periods.end_day)
    daily = [float(per_day(d)) for d in days]
    main = [float(main_per_day(d)) for d in days] if main_per_day else list(daily)
    totals = {m: (project(m) if callable(project) else project) for m in periods.history_months}
    return SeriesInput(key=key, topic_index=1, topic_label="Topic", lang=lang, status=status, title=title,
                       articles=[title], redirects=0, substitute=substitute, days=days, daily=daily,
                       main_daily=main, project=totals)


def make_result(key="cs", *, lang=None, verdict="growing", trust="high", growth=0.2, months_up=10, months_down=2,
                views=1000, share=1.5, status="ok", reasons=None, seasonality=None, spikes=None,
                substitute=False, title="Article", topic_label="Topic", topic_index=1, months=()):
    from witlib.analysis import SeriesResult

    no_data = verdict == "no_data"
    metrics = {} if no_data else {"views": views, "share": share, "growth": growth, "growth_views": growth,
                                  "growth_share": growth, "growth_clean": growth, "months_up": months_up,
                                  "months_down": months_down, "window_growth": None}
    if reasons is None:
        reasons = [{"code": status, "level": "low"}] if no_data else []
    return SeriesResult(key=key, topic_index=topic_index, topic_label=topic_label, lang=lang or key, status=status,
                        title=title, articles=[title] if title else [], redirects=0, substitute=substitute,
                        verdict=verdict, trust=None if no_data else trust, reasons=reasons, metrics=metrics,
                        monthly={m: {"views": views, "share": share} for m in months}, spikes=spikes or [],
                        seasonality=seasonality or {"status": "no_stable_pattern"})
```

`tests/conftest.py`:
```python
import pytest

from helpers import FakeTransport


@pytest.fixture
def fake_transport():
    return FakeTransport()


@pytest.fixture
def client(tmp_path, fake_transport):
    from witlib.api import ApiClient

    return ApiClient(transport=fake_transport, cache_dir=tmp_path / "cache", sleep=lambda s: None)
```

- [ ] **Step 4: Бланки трьох сценаріїв кейсу**

`tests/acceptance/studies/e1_fasting.json`:
```json
{
  "question": "Порівняй зростання інтересу до інтервального голодування в польськомовній та чеськомовній Wikipedia за останні два роки.",
  "topics": [{"label": "Інтервальне голодування", "wikidata": "Q1666254"}],
  "languages": ["pl", "cs"],
  "months": 24
}
```

`tests/acceptance/studies/e2_astronomy.json`:
```json
{
  "question": "Ми думаємо додати курс з астрономії до освітнього застосунку. Чи зростає інтерес до цієї теми в україномовній Wikipedia, і наскільки цьому зростанню можна довіряти?",
  "topics": [{"label": "Астрономія", "wikidata": "Q333", "related": ["Q544"]}],
  "languages": ["uk"],
  "months": 24
}
```

`tests/acceptance/studies/e3_english.json`:
```json
{
  "question": "Ми створюємо застосунок для вивчення мов. Порівняй інтерес до вивчення англійської у вибраних нами мовних розділах та підготуй короткий звіт: які аудиторії варто дослідити наступними й чому?",
  "topics": [{"label": "Вивчення англійської", "wikidata": "Q1860", "related": ["Q490396", "Q487425", "Q130192"]}],
  "languages": ["pl", "cs", "uk", "tr", "id"],
  "months": 24,
  "priorities": {"growth": 0.4, "interest": 0.3, "reach": 0.3}
}
```

- [ ] **Step 5: Приймальні тести**

`tests/acceptance/test_run_offline.py`:
```python
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
```

- [ ] **Step 6: Переконатися, що тести червоні з правильної причини**

Run: `.venv/bin/python -m pytest tests/acceptance -q`
Очікувано: 5 errors at setup — фікстура `client` не може імпортувати `witlib.api` (`ModuleNotFoundError`). Це правильна причина: модулів ще немає. Після Task 3 ці тести перейдуть у стан FAILED із `No module named 'witlib.cli'`, а зеленими стануть у Task 14.

- [ ] **Step 7: Коміт**

```bash
git add requirements.in requirements.txt requirements-dev.txt pytest.ini .gitignore scripts/witlib/__init__.py tests
git commit -m "test: add scaffolding and failing acceptance tests for the case scenarios" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Мови і бланк дослідження

**Files:**
- Create: `scripts/witlib/languages.py`, `scripts/witlib/study.py`
- Test: `tests/unit/test_languages.py`, `tests/unit/test_study.py`

**Interfaces:**
- Consumes: —
- Produces: `normalize_language(value: str) -> str` (ValueError з підказкою «did you mean»), `language_name(code: str, lang: str) -> str`, `LANGUAGES: dict[str, tuple[str, str, str]]`; `Topic(label, wikidata, related, substitutes)`, `Study(question, topics, languages, months, measure, priorities, report_language, summary, next_steps, warnings)`, `StudyError(problems: list[tuple[str, str, str]])` з методом `format() -> str`, `parse_study(data) -> Study`, `load_study(path) -> tuple[Study, Path]`.

- [ ] **Step 1: Тести мов**

`tests/unit/test_languages.py`:
```python
import pytest

from witlib.languages import language_name, normalize_language


@pytest.mark.parametrize("value", ["pl", "PL", "Polish", "polski", "польська", " Polish "])
def test_codes_and_names_map_to_code(value):
    assert normalize_language(value) == "pl"


def test_unknown_language_suggests_closest_code():
    with pytest.raises(ValueError, match="did you mean 'pl'"):
        normalize_language("polsih")


def test_language_name_is_localised():
    assert language_name("cs", "uk") == "чеська"
    assert language_name("cs", "en") == "Czech"
```

- [ ] **Step 2: Тести бланку**

`tests/unit/test_study.py`:
```python
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
```

- [ ] **Step 3: Переконатися, що тести падають**

Run: `.venv/bin/python -m pytest tests/unit/test_languages.py tests/unit/test_study.py -q`
Очікувано: FAIL/ERROR з `ModuleNotFoundError: No module named 'witlib.languages'`.

- [ ] **Step 4: Реалізація `languages.py`**

`scripts/witlib/languages.py`:
```python
"""Wikipedia language editions known by name: code -> (English, Ukrainian, native)."""
from __future__ import annotations

import difflib

LANGUAGES: dict[str, tuple[str, str, str]] = {
    "en": ("English", "англійська", "English"),
    "de": ("German", "німецька", "Deutsch"),
    "fr": ("French", "французька", "Français"),
    "es": ("Spanish", "іспанська", "Español"),
    "it": ("Italian", "італійська", "Italiano"),
    "pl": ("Polish", "польська", "Polski"),
    "pt": ("Portuguese", "португальська", "Português"),
    "ru": ("Russian", "російська", "Русский"),
    "uk": ("Ukrainian", "українська", "Українська"),
    "nl": ("Dutch", "нідерландська", "Nederlands"),
    "sv": ("Swedish", "шведська", "Svenska"),
    "ja": ("Japanese", "японська", "日本語"),
    "zh": ("Chinese", "китайська", "中文"),
    "ar": ("Arabic", "арабська", "العربية"),
    "fa": ("Persian", "перська", "فارسی"),
    "cs": ("Czech", "чеська", "Čeština"),
    "sk": ("Slovak", "словацька", "Slovenčina"),
    "hu": ("Hungarian", "угорська", "Magyar"),
    "ro": ("Romanian", "румунська", "Română"),
    "tr": ("Turkish", "турецька", "Türkçe"),
    "id": ("Indonesian", "індонезійська", "Bahasa Indonesia"),
    "vi": ("Vietnamese", "в'єтнамська", "Tiếng Việt"),
    "ko": ("Korean", "корейська", "한국어"),
    "he": ("Hebrew", "іврит", "עברית"),
    "fi": ("Finnish", "фінська", "Suomi"),
    "no": ("Norwegian", "норвезька", "Norsk"),
    "da": ("Danish", "данська", "Dansk"),
    "el": ("Greek", "грецька", "Ελληνικά"),
    "bg": ("Bulgarian", "болгарська", "Български"),
    "sr": ("Serbian", "сербська", "Српски"),
    "hr": ("Croatian", "хорватська", "Hrvatski"),
    "sl": ("Slovenian", "словенська", "Slovenščina"),
    "lt": ("Lithuanian", "литовська", "Lietuvių"),
    "lv": ("Latvian", "латиська", "Latviešu"),
    "et": ("Estonian", "естонська", "Eesti"),
    "be": ("Belarusian", "білоруська", "Беларуская"),
    "kk": ("Kazakh", "казахська", "Қазақша"),
    "ka": ("Georgian", "грузинська", "ქართული"),
    "hy": ("Armenian", "вірменська", "Հայերեն"),
    "az": ("Azerbaijani", "азербайджанська", "Azərbaycanca"),
    "uz": ("Uzbek", "узбецька", "Oʻzbekcha"),
    "hi": ("Hindi", "гінді", "हिन्दी"),
    "bn": ("Bengali", "бенгальська", "বাংলা"),
    "ta": ("Tamil", "тамільська", "தமிழ்"),
    "th": ("Thai", "тайська", "ไทย"),
    "ms": ("Malay", "малайська", "Bahasa Melayu"),
    "ca": ("Catalan", "каталанська", "Català"),
    "eu": ("Basque", "баскська", "Euskara"),
    "gl": ("Galician", "галісійська", "Galego"),
    "ur": ("Urdu", "урду", "اردو"),
    "mr": ("Marathi", "маратхі", "मराठी"),
    "te": ("Telugu", "телугу", "తెలుగు"),
    "ml": ("Malayalam", "малаялам", "മലയാളം"),
    "af": ("Afrikaans", "африкаанс", "Afrikaans"),
    "sq": ("Albanian", "албанська", "Shqip"),
    "mk": ("Macedonian", "македонська", "Македонски"),
    "is": ("Icelandic", "ісландська", "Íslenska"),
    "ga": ("Irish", "ірландська", "Gaeilge"),
    "cy": ("Welsh", "валлійська", "Cymraeg"),
    "eo": ("Esperanto", "есперанто", "Esperanto"),
}

_ALIASES: dict[str, str] = {}
for _code, _names in LANGUAGES.items():
    _ALIASES[_code] = _code
    for _name in _names:
        _ALIASES[_name.casefold()] = _code


def normalize_language(value: str) -> str:
    """Return the Wikipedia code for a code or a language name; raise ValueError with a hint."""
    key = value.strip().casefold()
    if key in _ALIASES:
        return _ALIASES[key]
    close = difflib.get_close_matches(key, list(_ALIASES), n=1, cutoff=0.6)
    hint = f"; did you mean '{_ALIASES[close[0]]}'?" if close else ""
    raise ValueError(f"unknown language '{value}'{hint}")


def language_name(code: str, lang: str) -> str:
    english, ukrainian, _native = LANGUAGES[code]
    return ukrainian if lang == "uk" else english
```

- [ ] **Step 5: Реалізація `study.py`**

`scripts/witlib/study.py`:
```python
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
```

- [ ] **Step 6: Тести проходять**

Run: `.venv/bin/python -m pytest tests/unit/test_languages.py tests/unit/test_study.py -q`
Очікувано: усі PASS (23 passed).

- [ ] **Step 7: Коміт**

```bash
git add scripts/witlib/languages.py scripts/witlib/study.py tests/unit/test_languages.py tests/unit/test_study.py
git commit -m "feat: study form validation with actionable errors and language names" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: HTTP-клієнт

**Files:**
- Create: `scripts/witlib/api.py`
- Test: `tests/unit/test_api.py`

**Interfaces:**
- Consumes: `witlib.__version__`
- Produces: `Response(status: int, body: str, headers: dict[str, str])`, `TransientError`, `WitNetworkError`, `WitBudgetError`, `requests_transport(url, headers) -> Response`, `user_agent(contact=None) -> str`, `default_cache_dir() -> Path`, `ApiClient(transport=requests_transport, cache_dir=None, *, min_interval=0.35, max_attempts=4, max_requests=400, refresh=False, sleep=time.sleep, clock=time.monotonic, now=time.time, progress=None)` з методом `get_json(url, *, ttl: float | None = None, allow_404=False) -> dict | None` і лічильниками `request_count`, `cache_hits`. `DEFAULT_CONTACT` — одне місце для контакту в User-Agent.

- [ ] **Step 1: Тести**

`tests/unit/test_api.py`:
```python
import itertools

import pytest

from witlib.api import ApiClient, Response, TransientError, WitBudgetError, WitNetworkError

URL = "https://example.org/data"
OK = Response(200, '{"ok": 1}', {})


class Script:
    """Transport returning scripted responses in order and recording what it was asked."""

    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, url, headers):
        self.calls.append((url, headers))
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def make_client(tmp_path, transport, **kw):
    sleeps = []
    kw.setdefault("clock", itertools.count(0, 10).__next__)
    client = ApiClient(transport=transport, cache_dir=tmp_path, sleep=sleeps.append, **kw)
    return client, sleeps


def test_sends_identifying_user_agent_with_contact(tmp_path, monkeypatch):
    monkeypatch.setenv("WIT_CONTACT", "team@example.org")
    transport = Script(OK)
    client, _ = make_client(tmp_path, transport)
    assert client.get_json(URL) == {"ok": 1}
    agent = transport.calls[0][1]["User-Agent"]
    assert agent.startswith("wiki-interest-trends/1.0.0 (team@example.org) python-requests/")


def test_retries_429_honouring_retry_after(tmp_path):
    transport = Script(Response(429, "", {"retry-after": "3"}), OK)
    client, sleeps = make_client(tmp_path, transport)
    assert client.get_json(URL) == {"ok": 1}
    assert sleeps == [3.0]


def test_retries_connection_errors(tmp_path):
    transport = Script(TransientError("reset"), OK)
    client, sleeps = make_client(tmp_path, transport)
    assert client.get_json(URL) == {"ok": 1}
    assert sleeps == [2.0]


def test_gives_up_after_four_attempts(tmp_path):
    transport = Script(*[Response(503, "", {})] * 4)
    client, sleeps = make_client(tmp_path, transport)
    with pytest.raises(WitNetworkError, match="HTTP 503 after 4 attempts"):
        client.get_json(URL)
    assert sleeps == [2.0, 4.0, 8.0]


def test_allowed_404_returns_none_and_is_cached(tmp_path):
    transport = Script(Response(404, '{"title": "Not found"}', {}))
    client, _ = make_client(tmp_path, transport)
    assert client.get_json(URL, allow_404=True) is None
    assert client.get_json(URL, allow_404=True) is None
    assert len(transport.calls) == 1


def test_unexpected_404_is_an_error(tmp_path):
    client, _ = make_client(tmp_path, Script(Response(404, "", {})))
    with pytest.raises(WitNetworkError, match="HTTP 404"):
        client.get_json(URL)


def test_second_request_is_served_from_cache(tmp_path):
    transport = Script(OK)
    client, _ = make_client(tmp_path, transport)
    client.get_json(URL)
    assert client.get_json(URL) == {"ok": 1}
    assert (len(transport.calls), client.request_count, client.cache_hits) == (1, 1, 1)


def test_expired_ttl_refetches(tmp_path):
    transport = Script(OK, Response(200, '{"ok": 2}', {}))
    times = iter([1000.0, 1061.0, 1061.0])
    client, _ = make_client(tmp_path, transport, now=lambda: next(times))
    client.get_json(URL, ttl=60)
    assert client.get_json(URL, ttl=60) == {"ok": 2}


def test_refresh_ignores_cache(tmp_path):
    transport = Script(OK, OK)
    client, _ = make_client(tmp_path, transport)
    client.get_json(URL)
    client.refresh = True
    client.get_json(URL)
    assert len(transport.calls) == 2


def test_request_budget_is_enforced(tmp_path):
    client, _ = make_client(tmp_path, Script(OK, OK), max_requests=2)
    client.get_json(URL + "/1")
    client.get_json(URL + "/2")
    with pytest.raises(WitBudgetError):
        client.get_json(URL + "/3")


def test_consecutive_requests_are_paced(tmp_path):
    client, sleeps = make_client(tmp_path, Script(OK, OK), clock=lambda: 5.0)
    client.get_json(URL + "/1")
    client.get_json(URL + "/2")
    assert sleeps == [pytest.approx(0.35)]
```

- [ ] **Step 2: Переконатися, що тести падають**

Run: `.venv/bin/python -m pytest tests/unit/test_api.py -q`
Очікувано: ERROR — `ModuleNotFoundError: No module named 'witlib.api'`.

- [ ] **Step 3: Реалізація**

`scripts/witlib/api.py`:
```python
"""HTTP access to Wikimedia APIs: identifying User-Agent, pacing, retries and a disk cache."""
from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from . import __version__

DEFAULT_CONTACT = "https://github.com/Monsteroo/wiki-interest-trends"
RETRY_STATUSES = {429, 500, 502, 503, 504}


@dataclass
class Response:
    status: int
    body: str
    headers: dict[str, str]


class TransientError(Exception):
    """A connection-level failure that is worth retrying."""


class WitNetworkError(RuntimeError):
    """The API stayed unavailable after all retries, or answered with an unexpected status."""


class WitBudgetError(RuntimeError):
    """A single run would send too many requests."""


Transport = Callable[[str, dict[str, str]], Response]


def requests_transport(url: str, headers: dict[str, str]) -> Response:
    import requests

    try:
        reply = requests.get(url, headers=headers, timeout=30)
    except requests.RequestException as exc:
        raise TransientError(str(exc)) from exc
    return Response(reply.status_code, reply.text, {k.lower(): v for k, v in reply.headers.items()})


def user_agent(contact: str | None = None) -> str:
    import requests

    contact = contact or os.environ.get("WIT_CONTACT") or DEFAULT_CONTACT
    return f"wiki-interest-trends/{__version__} ({contact}) python-requests/{requests.__version__}"


def default_cache_dir() -> Path:
    env = os.environ.get("WIT_CACHE_DIR")
    return Path(env) if env else Path.home() / ".cache" / "wiki-interest-trends" / "http"


class ApiClient:
    def __init__(self, transport: Transport = requests_transport, cache_dir: Path | None = None, *,
                 min_interval: float = 0.35, max_attempts: int = 4, max_requests: int = 400, refresh: bool = False,
                 sleep: Callable[[float], None] = time.sleep, clock: Callable[[], float] = time.monotonic,
                 now: Callable[[], float] = time.time, progress: Callable[[str], None] | None = None):
        self.transport = transport
        self.cache_dir = Path(cache_dir) if cache_dir else default_cache_dir()
        self.min_interval = min_interval
        self.max_attempts = max_attempts
        self.max_requests = max_requests
        self.refresh = refresh
        self.sleep = sleep
        self.clock = clock
        self.now = now
        self.progress = progress
        self.headers = {"User-Agent": user_agent(), "Accept": "application/json"}
        self.request_count = 0
        self.cache_hits = 0
        self._last_request: float | None = None

    def get_json(self, url: str, *, ttl: float | None = None, allow_404: bool = False) -> dict | None:
        """GET a JSON document. ttl=None keeps it cached forever; allow_404 turns 404 into None."""
        cached = self._read_cache(url, ttl)
        if cached is not None:
            self.cache_hits += 1
            return self._decode(url, cached["status"], cached["body"], allow_404)
        reply = self._fetch(url)
        if reply.status == 200 or (reply.status == 404 and allow_404):
            self._write_cache(url, reply)
        return self._decode(url, reply.status, reply.body, allow_404)

    def _decode(self, url: str, status: int, body: str, allow_404: bool) -> dict | None:
        if status == 404 and allow_404:
            return None
        if status != 200:
            raise WitNetworkError(f"HTTP {status} for {url}")
        return json.loads(body)

    def _fetch(self, url: str) -> Response:
        if self.request_count >= self.max_requests:
            raise WitBudgetError(f"this run needs more than {self.max_requests} API requests")
        last_error = ""
        for attempt in range(1, self.max_attempts + 1):
            self._pace()
            self.request_count += 1
            if self.progress and self.request_count % 10 == 0:
                self.progress(f"... {self.request_count} API requests")
            try:
                reply = self.transport(url, dict(self.headers))
            except TransientError as exc:
                reply, last_error = None, str(exc)
            if reply is not None and reply.status not in RETRY_STATUSES:
                return reply
            if reply is not None:
                last_error = f"HTTP {reply.status}"
            if attempt < self.max_attempts:
                self.sleep(self._retry_delay(reply, attempt))
        raise WitNetworkError(f"{last_error} after {self.max_attempts} attempts for {url}")

    @staticmethod
    def _retry_delay(reply: Response | None, attempt: int) -> float:
        if reply is not None:
            retry_after = reply.headers.get("retry-after", "")
            if retry_after.isdigit():
                return float(retry_after)
        return float(2 ** attempt)

    def _pace(self) -> None:
        if self._last_request is not None:
            wait = self.min_interval - (self.clock() - self._last_request)
            if wait > 0:
                self.sleep(wait)
        self._last_request = self.clock()

    def _cache_file(self, url: str) -> Path:
        return self.cache_dir / (hashlib.sha256(url.encode("utf-8")).hexdigest() + ".json")

    def _read_cache(self, url: str, ttl: float | None) -> dict | None:
        if self.refresh:
            return None
        path = self._cache_file(url)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        if ttl is not None and self.now() - data.get("fetched_at", 0) > ttl:
            return None
        return data

    def _write_cache(self, url: str, reply: Response) -> None:
        path = self._cache_file(url)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps({"url": url, "status": reply.status, "body": reply.body, "fetched_at": self.now()}), encoding="utf-8")
        tmp.replace(path)
```

- [ ] **Step 4: Тести проходять**

Run: `.venv/bin/python -m pytest tests/unit/test_api.py -q`
Очікувано: 11 passed.

- [ ] **Step 5: Коміт**

```bash
git add scripts/witlib/api.py tests/unit/test_api.py
git commit -m "feat: polite Wikimedia API client with retries, pacing, budget and disk cache" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Періоди, завантаження переглядів, місячні ряди

**Files:**
- Create: `scripts/witlib/series.py`
- Test: `tests/unit/test_series.py`

**Interfaces:**
- Consumes: `ApiClient.get_json`
- Produces: `PAGEVIEWS`, `DATA_START = date(2015, 7, 1)`, `MAX_REDIRECTS = 10`, `Periods(as_of, last_month, analysis_start, history_start)` з властивостями `end_day`, `history_months`, `analysis_months`; `month_add(first, n)`, `month_end(first)`, `month_list(start, last) -> list[str "YYYY-MM"]`, `day_list(start, end) -> list[str "YYYY-MM-DD"]`, `compute_periods(as_of, months, history_months=60) -> Periods`, `article_url(lang, title, start, end)`, `aggregate_url(lang, start, end)`, `fetch_daily(client, lang, title, start, end) -> dict[day, int]`, `fetch_project_monthly(client, lang, start, end) -> dict[month, int]`, `sum_daily(parts, days) -> list[float]`, `monthly_sums(days, values) -> dict[month, float]`, `shares(views, project) -> dict[month, float]`, `SeriesInput(key, topic_index, topic_label, lang, status, title, articles, redirects, substitute, days, daily, main_daily, project)`.

- [ ] **Step 1: Тести**

`tests/unit/test_series.py`:
```python
from datetime import date

from helpers import FakeTransport
from witlib.api import ApiClient, Response
from witlib.series import (article_url, aggregate_url, compute_periods, day_list, fetch_daily, fetch_project_monthly,
                           month_end, month_list, monthly_sums, shares, sum_daily)


def test_periods_use_complete_months_and_five_years_of_history():
    p = compute_periods(date(2026, 9, 26), 24)
    assert (p.last_month, p.analysis_start, p.history_start) == (date(2026, 8, 1), date(2024, 9, 1), date(2021, 9, 1))
    assert p.end_day == date(2026, 8, 31)
    assert len(p.history_months) == 60 and p.analysis_months[0] == "2024-09" and p.analysis_months[-1] == "2026-08"


def test_first_days_of_a_month_skip_the_not_yet_loaded_month():
    assert compute_periods(date(2026, 9, 2), 24).last_month == date(2026, 7, 1)


def test_periods_never_start_before_the_data():
    p = compute_periods(date(2017, 1, 15), 24)
    assert p.analysis_start == p.history_start == date(2015, 7, 1)


def test_month_helpers():
    assert month_end(date(2024, 2, 1)) == date(2024, 2, 29)
    assert month_list(date(2025, 11, 1), date(2026, 2, 1)) == ["2025-11", "2025-12", "2026-01", "2026-02"]
    assert day_list(date(2026, 2, 27), date(2026, 3, 1)) == ["2026-02-27", "2026-02-28", "2026-03-01"]


def test_urls_encode_titles_and_dates():
    assert article_url("cs", "Přerušovaný půst", date(2021, 9, 1), date(2026, 8, 31)) == (
        "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/cs.wikipedia.org/all-access/user/"
        "P%C5%99eru%C5%A1ovan%C3%BD_p%C5%AFst/daily/2021090100/2026083100")
    assert "/AC%2FDC/" in article_url("en", "AC/DC", date(2026, 1, 1), date(2026, 1, 31))
    assert aggregate_url("uk", date(2021, 9, 1), date(2026, 8, 31)).endswith("/aggregate/uk.wikipedia.org/all-access/user/monthly/2021090100/2026083100")


def client_with(url, response, tmp_path):
    return ApiClient(transport=FakeTransport({url: response}), cache_dir=tmp_path, sleep=lambda s: None)


def test_fetch_daily_parses_items_and_treats_404_as_no_views(tmp_path):
    start, end = date(2026, 8, 1), date(2026, 8, 3)
    url = article_url("cs", "Půst", start, end)
    body = '{"items": [{"timestamp": "2026080100", "views": 5}, {"timestamp": "2026080300", "views": 7}]}'
    assert fetch_daily(client_with(url, Response(200, body, {}), tmp_path), "cs", "Půst", start, end) == {"2026-08-01": 5, "2026-08-03": 7}
    assert fetch_daily(client_with(url, Response(404, "", {}), tmp_path / "b"), "cs", "Půst", start, end) == {}


def test_fetch_project_monthly_keys_by_month(tmp_path):
    start, end = date(2026, 7, 1), date(2026, 8, 31)
    url = aggregate_url("cs", start, end)
    body = '{"items": [{"timestamp": "2026070100", "views": 100}, {"timestamp": "2026080100", "views": 90}]}'
    assert fetch_project_monthly(client_with(url, Response(200, body, {}), tmp_path), "cs", start, end) == {"2026-07": 100, "2026-08": 90}


def test_daily_parts_are_summed_with_zero_filled_gaps():
    days = ["2026-08-01", "2026-08-02", "2026-08-03"]
    assert sum_daily([{"2026-08-01": 1, "2026-08-03": 2}, {"2026-08-03": 5}], days) == [1.0, 0.0, 7.0]


def test_monthly_sums_and_share_per_million():
    months = monthly_sums(["2026-07-31", "2026-08-01", "2026-08-02"], [1.0, 2.0, 3.0])
    assert months == {"2026-07": 1.0, "2026-08": 5.0}
    assert shares(months, {"2026-07": 1_000_000, "2026-08": 2_500_000}) == {"2026-07": 1.0, "2026-08": 2.0}
    assert shares({"2026-08": 5.0}, {}) == {"2026-08": 0.0}
```

- [ ] **Step 2: Переконатися, що тести падають**

Run: `.venv/bin/python -m pytest tests/unit/test_series.py -q`
Очікувано: ERROR — `ModuleNotFoundError: No module named 'witlib.series'`.

- [ ] **Step 3: Реалізація (частина без `collect_inputs`)**

`scripts/witlib/series.py`:
```python
"""Periods, pageview fetching and construction of daily and monthly series."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from urllib.parse import quote

from .api import ApiClient

PAGEVIEWS = "https://wikimedia.org/api/rest_v1/metrics/pageviews"
DATA_START = date(2015, 7, 1)
MAX_REDIRECTS = 10


@dataclass(frozen=True)
class Periods:
    as_of: date
    last_month: date
    analysis_start: date
    history_start: date

    @property
    def end_day(self) -> date:
        return month_end(self.last_month)

    @property
    def history_months(self) -> list[str]:
        return month_list(self.history_start, self.last_month)

    @property
    def analysis_months(self) -> list[str]:
        return month_list(self.analysis_start, self.last_month)


@dataclass
class SeriesInput:
    key: str
    topic_index: int
    topic_label: str
    lang: str
    status: str
    title: str | None
    articles: list[str]
    redirects: int
    substitute: bool
    days: list[str]
    daily: list[float]
    main_daily: list[float]
    project: dict[str, int]


def month_add(first: date, n: int) -> date:
    years, month = divmod(first.month - 1 + n, 12)
    return date(first.year + years, month + 1, 1)


def month_end(first: date) -> date:
    return month_add(first, 1) - timedelta(days=1)


def month_list(start: date, last: date) -> list[str]:
    months, current = [], start
    while current <= last:
        months.append(f"{current:%Y-%m}")
        current = month_add(current, 1)
    return months


def day_list(start: date, end: date) -> list[str]:
    return [(start + timedelta(days=i)).isoformat() for i in range((end - start).days + 1)]


def compute_periods(as_of: date, months: int, history_months: int = 60) -> Periods:
    back = 2 if as_of.day <= 2 else 1
    last = month_add(as_of.replace(day=1), -back)
    analysis_start = max(month_add(last, -(months - 1)), DATA_START)
    history_start = max(month_add(last, -(max(months, history_months) - 1)), DATA_START)
    return Periods(as_of=as_of, last_month=last, analysis_start=analysis_start, history_start=history_start)


def article_url(lang: str, title: str, start: date, end: date) -> str:
    encoded = quote(title.replace(" ", "_"), safe="")
    return f"{PAGEVIEWS}/per-article/{lang}.wikipedia.org/all-access/user/{encoded}/daily/{start:%Y%m%d}00/{end:%Y%m%d}00"


def aggregate_url(lang: str, start: date, end: date) -> str:
    return f"{PAGEVIEWS}/aggregate/{lang}.wikipedia.org/all-access/user/monthly/{start:%Y%m%d}00/{end:%Y%m%d}00"


def _day(timestamp: str) -> str:
    return f"{timestamp[0:4]}-{timestamp[4:6]}-{timestamp[6:8]}"


def fetch_daily(client: ApiClient, lang: str, title: str, start: date, end: date) -> dict[str, int]:
    data = client.get_json(article_url(lang, title, start, end), allow_404=True) or {}
    return {_day(item["timestamp"]): int(item["views"]) for item in data.get("items", [])}


def fetch_project_monthly(client: ApiClient, lang: str, start: date, end: date) -> dict[str, int]:
    data = client.get_json(aggregate_url(lang, start, end), allow_404=True) or {}
    return {_day(item["timestamp"])[:7]: int(item["views"]) for item in data.get("items", [])}


def sum_daily(parts: list[dict[str, int]], days: list[str]) -> list[float]:
    return [float(sum(part.get(day, 0) for part in parts)) for day in days]


def monthly_sums(days: list[str], values: list[float]) -> dict[str, float]:
    months: dict[str, float] = {}
    for day, value in zip(days, values):
        months[day[:7]] = months.get(day[:7], 0.0) + value
    return months


def shares(views: dict[str, float], project: dict[str, int]) -> dict[str, float]:
    return {m: (v / project[m] * 1_000_000 if project.get(m) else 0.0) for m, v in views.items()}
```

- [ ] **Step 4: Тести проходять**

Run: `.venv/bin/python -m pytest tests/unit/test_series.py -q`
Очікувано: 9 passed.

- [ ] **Step 5: Коміт**

```bash
git add scripts/witlib/series.py tests/unit/test_series.py
git commit -m "feat: complete-month periods, pageview fetching and monthly series" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---
### Task 5: Ріст, сталість і вердикт

**Files:**
- Create: `scripts/witlib/analysis.py`
- Test: `tests/unit/test_analysis_growth.py`

**Interfaces:**
- Consumes: —
- Produces: `mean(values) -> float`, `growth(series: dict[month, float], recent: list[str], previous: list[str]) -> float | None` (округлення до 6 знаків), `months_up_down(series, months) -> tuple[int, int]` (останні 12 місяців проти тих самих місяців роком раніше), `window_growth(series, window) -> float | None` (лише для вікна ≥ 36 місяців), `decide_verdict(growth, months_up, months_down) -> "growing" | "declining" | "no_clear_trend"`.

- [ ] **Step 1: Тести**

`tests/unit/test_analysis_growth.py`:
```python
import pytest

from witlib.analysis import decide_verdict, growth, mean, months_up_down, window_growth

PREV = [f"2024-{m:02d}" for m in range(9, 13)] + [f"2025-{m:02d}" for m in range(1, 9)]
RECENT = [f"2025-{m:02d}" for m in range(9, 13)] + [f"2026-{m:02d}" for m in range(1, 9)]
MONTHS = PREV + RECENT


def test_mean_of_nothing_is_zero():
    assert mean([]) == 0.0


def test_growth_compares_last_twelve_months_with_previous_twelve():
    series = {m: 100.0 for m in PREV} | {m: 120.0 for m in RECENT}
    assert growth(series, RECENT, PREV) == pytest.approx(0.2)


def test_growth_is_undefined_without_previous_views():
    series = {m: 0.0 for m in PREV} | {m: 50.0 for m in RECENT}
    assert growth(series, RECENT, PREV) is None


def test_months_up_compare_with_the_same_month_a_year_ago():
    seasonal = {m: 100.0 + 50 * m.endswith("-01") for m in PREV}
    series = seasonal | {m: seasonal[p] * 1.1 for p, m in zip(PREV, RECENT)}
    assert months_up_down(series, MONTHS) == (12, 0)


def test_months_down_count_declines_only():
    series = {m: 100.0 for m in PREV} | {m: (90.0 if i < 8 else 100.0) for i, m in enumerate(RECENT)}
    assert months_up_down(series, MONTHS) == (0, 8)


def test_window_growth_is_annualised_over_three_years():
    window = [f"m{i:02d}" for i in range(36)]
    series = {m: (100.0 if i < 12 else 121.0) for i, m in enumerate(window)}
    assert window_growth(series, window) == pytest.approx(0.1)
    assert window_growth(series, window[:24]) is None


@pytest.mark.parametrize("args, expected", [
    ((0.10, 7, 0), "growing"),
    ((0.0999, 12, 0), "no_clear_trend"),
    ((0.5, 6, 6), "no_clear_trend"),
    ((-0.10, 0, 7), "declining"),
    ((None, 12, 0), "no_clear_trend"),
])
def test_verdict_thresholds(args, expected):
    assert decide_verdict(*args) == expected
```

- [ ] **Step 2: Переконатися, що тести падають**

Run: `.venv/bin/python -m pytest tests/unit/test_analysis_growth.py -q`
Очікувано: ERROR — `ModuleNotFoundError: No module named 'witlib.analysis'`.

- [ ] **Step 3: Реалізація**

`scripts/witlib/analysis.py`:
```python
"""Growth, consistency, spikes, trust, verdicts and ranking: pure functions over pageview series."""
from __future__ import annotations


def mean(values) -> float:
    values = list(values)
    return sum(values) / len(values) if values else 0.0


def growth(series: dict[str, float], recent: list[str], previous: list[str]) -> float | None:
    before = mean(series[m] for m in previous)
    if before == 0:
        return None
    return round(mean(series[m] for m in recent) / before - 1, 6)


def months_up_down(series: dict[str, float], months: list[str]) -> tuple[int, int]:
    up = down = 0
    for i in range(len(months) - 12, len(months)):
        now, year_ago = series[months[i]], series[months[i - 12]]
        up += now > year_ago
        down += now < year_ago
    return up, down


def window_growth(series: dict[str, float], window: list[str]) -> float | None:
    if len(window) < 36:
        return None
    first = mean(series[m] for m in window[:12])
    last = mean(series[m] for m in window[-12:])
    if first == 0:
        return None
    return round((last / first) ** (12 / (len(window) - 12)) - 1, 6)


def decide_verdict(g: float | None, months_up: int, months_down: int) -> str:
    if g is None:
        return "no_clear_trend"
    if g >= 0.10 and months_up >= 7:
        return "growing"
    if g <= -0.10 and months_down >= 7:
        return "declining"
    return "no_clear_trend"
```

- [ ] **Step 4: Тести проходять**

Run: `.venv/bin/python -m pytest tests/unit/test_analysis_growth.py -q`
Очікувано: 11 passed.

- [ ] **Step 5: Коміт**

```bash
git add scripts/witlib/analysis.py tests/unit/test_analysis_growth.py
git commit -m "feat: year-over-year growth, month consistency and verdict rules" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 6: Сплески і правила довіри

**Files:**
- Modify: `scripts/witlib/analysis.py` (додати в кінець)
- Test: `tests/unit/test_analysis_trust.py`

**Interfaces:**
- Consumes: —
- Produces: `detect_spikes(daily, window=28, min_history=7, min_views=20.0, ratio=5.0, mad_k=10.0) -> tuple[list[int], list[float]]` (індекси сплесків і типове значення для кожного дня), `cap_spikes(daily, spike_idx, typical) -> list[float]`, `trust_reasons(*, level_views, verdict, growth, growth_clean, months_up, months_down, first_view_month, comparison_start, substitute_title, top_spike, growth_views, growth_share) -> list[dict]` (причини з полями `code`, `level` ∈ {low, medium, note} і параметрами; спершу low), `trust_level(reasons) -> "high" | "medium" | "low"`, `LEVEL_ORDER`.

- [ ] **Step 1: Тести**

`tests/unit/test_analysis_trust.py`:
```python
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
```

- [ ] **Step 2: Переконатися, що тести падають**

Run: `.venv/bin/python -m pytest tests/unit/test_analysis_trust.py -q`
Очікувано: ERROR — `ImportError: cannot import name 'cap_spikes' from 'witlib.analysis'`.

- [ ] **Step 3: Реалізація**

На початку `scripts/witlib/analysis.py`, одразу після рядка `from __future__ import annotations`, додати:
```python

import statistics

LEVEL_ORDER = {"low": 0, "medium": 1, "note": 2}
```

У кінець `scripts/witlib/analysis.py` додати:
```python


def detect_spikes(daily: list[float], window: int = 28, min_history: int = 7, min_views: float = 20.0,
                  ratio: float = 5.0, mad_k: float = 10.0) -> tuple[list[int], list[float]]:
    """Return indices of spike days and the typical (trailing-median) value for every day."""
    spikes: list[int] = []
    typical: list[float] = []
    for i, value in enumerate(daily):
        history = daily[max(0, i - window):i]
        if len(history) < min_history:
            typical.append(value)
            continue
        med = statistics.median(history)
        mad = statistics.median(abs(x - med) for x in history)
        typical.append(med)
        if value >= min_views and value > max(ratio * med, med + mad_k * mad):
            spikes.append(i)
    return spikes, typical


def cap_spikes(daily: list[float], spike_idx: list[int], typical: list[float]) -> list[float]:
    marked = set(spike_idx)
    return [typical[i] if i in marked else value for i, value in enumerate(daily)]


def trust_reasons(*, level_views: float, verdict: str, growth: float | None, growth_clean: float | None,
                  months_up: int, months_down: int, first_view_month: str | None, comparison_start: str,
                  substitute_title: str | None, top_spike: str | None, growth_views: float | None,
                  growth_share: float | None) -> list[dict]:
    reasons: list[dict] = []
    if level_views < 100:
        reasons.append({"code": "low_volume", "level": "low", "views": round(level_views)})
    elif level_views < 500:
        reasons.append({"code": "moderate_volume", "level": "medium", "views": round(level_views)})
    if verdict == "growing" and months_up in (7, 8):
        reasons.append({"code": "inconsistent", "level": "medium", "months": months_up, "direction": "up"})
    if verdict == "declining" and months_down in (7, 8):
        reasons.append({"code": "inconsistent", "level": "medium", "months": months_down, "direction": "down"})
    if verdict == "growing" and growth_clean is not None and (growth_clean < 0.10 or growth_clean < growth / 2):
        reasons.append({"code": "event_driven", "level": "low", "date": top_spike, "direction": "up"})
    if verdict == "declining" and growth_clean is not None and (growth_clean > -0.10 or growth_clean > growth / 2):
        reasons.append({"code": "event_driven", "level": "low", "date": top_spike, "direction": "down"})
    if first_view_month is not None and first_view_month >= comparison_start:
        reasons.append({"code": "new_article", "level": "low", "month": first_view_month})
    if substitute_title:
        reasons.append({"code": "substitute", "level": "medium", "title": substitute_title})
    if (growth_views is not None and growth_share is not None and min(abs(growth_views), abs(growth_share)) >= 0.05
            and (growth_views > 0) != (growth_share > 0)):
        reasons.append({"code": "divergence", "level": "note", "growth_views": growth_views, "growth_share": growth_share})
    return sorted(reasons, key=lambda reason: LEVEL_ORDER[reason["level"]])


def trust_level(reasons: list[dict]) -> str:
    levels = {reason["level"] for reason in reasons}
    if "low" in levels:
        return "low"
    return "medium" if "medium" in levels else "high"
```

- [ ] **Step 4: Тести проходять**

Run: `.venv/bin/python -m pytest tests/unit/test_analysis_trust.py tests/unit/test_analysis_growth.py -q`
Очікувано: 27 passed.

- [ ] **Step 5: Коміт**

```bash
git add scripts/witlib/analysis.py tests/unit/test_analysis_trust.py
git commit -m "feat: spike detection and explainable trust rules" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 7: Сезонність

**Files:**
- Create: `scripts/witlib/seasonality.py`
- Test: `tests/unit/test_seasonality.py`

**Interfaces:**
- Consumes: —
- Produces: `seasonality(monthly: dict[month, float], months: list[str], level_views: float, max_cycles=5) -> dict` зі `status` ∈ {`stable_peak`, `no_stable_pattern`, `insufficient_history`, `low_volume`} і, коли рахується, полями `peak_month` (1–12), `low_month`, `peak_years`, `cycles`, `uplift`, `profile`.

- [ ] **Step 1: Тести**

`tests/unit/test_seasonality.py`:
```python
from datetime import date

from witlib.seasonality import seasonality
from witlib.series import month_list

MONTHS = month_list(date(2021, 9, 1), date(2026, 8, 1))


def series(value):
    return {m: float(value(m)) for m in MONTHS}


def test_january_peak_in_four_of_five_years_is_stable():
    data = series(lambda m: 150 if m.endswith("-01") and m != "2024-01" else (130 if m == "2024-03" else 100))
    result = seasonality(data, MONTHS, level_views=1000)
    assert result["status"] == "stable_peak"
    assert (result["peak_month"], result["peak_years"], result["cycles"]) == (1, 4, 5)
    assert result["uplift"] >= 0.2


def test_flat_series_has_no_stable_pattern():
    assert seasonality(series(lambda m: 100), MONTHS, level_views=1000)["status"] == "no_stable_pattern"


def test_two_years_are_not_enough():
    assert seasonality(series(lambda m: 100), MONTHS[-24:], level_views=1000) == {"status": "insufficient_history", "cycles": 2}


def test_low_traffic_is_not_analysed():
    assert seasonality(series(lambda m: 100), MONTHS, level_views=99) == {"status": "low_volume"}
```

- [ ] **Step 2: Переконатися, що тести падають**

Run: `.venv/bin/python -m pytest tests/unit/test_seasonality.py -q`
Очікувано: ERROR — `ModuleNotFoundError: No module named 'witlib.seasonality'`.

- [ ] **Step 3: Реалізація**

`scripts/witlib/seasonality.py`:
```python
"""Seasonality: month-of-year profile over up to five yearly cycles and the stability of its peak."""
from __future__ import annotations

import math


def seasonality(monthly: dict[str, float], months: list[str], level_views: float, max_cycles: int = 5) -> dict:
    if level_views < 100:
        return {"status": "low_volume"}
    cycles = []
    for c in range(min(max_cycles, len(months) // 12)):
        block = months[len(months) - 12 * (c + 1): len(months) - 12 * c]
        average = sum(monthly.get(m, 0.0) for m in block) / 12
        if average > 0:
            cycles.append({int(m[5:7]): monthly.get(m, 0.0) / average for m in block})
    if len(cycles) < 3:
        return {"status": "insufficient_history", "cycles": len(cycles)}
    profile = {month: sum(cycle[month] for cycle in cycles) / len(cycles) for month in range(1, 13)}
    peak = max(profile, key=profile.get)
    low = min(profile, key=profile.get)
    peak_years = sum(1 for cycle in cycles if max(cycle, key=cycle.get) == peak)
    stable = peak_years >= math.ceil(0.6 * len(cycles)) and profile[peak] >= 1.20
    return {"status": "stable_peak" if stable else "no_stable_pattern", "peak_month": peak, "low_month": low,
            "peak_years": peak_years, "cycles": len(cycles), "uplift": round(profile[peak] - 1, 3),
            "profile": {month: round(value, 3) for month, value in profile.items()}}
```

- [ ] **Step 4: Тести проходять**

Run: `.venv/bin/python -m pytest tests/unit/test_seasonality.py -q`
Очікувано: 4 passed.

- [ ] **Step 5: Коміт**

```bash
git add scripts/witlib/seasonality.py tests/unit/test_seasonality.py
git commit -m "feat: seasonality profile with peak stability over five years" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 8: Аналіз ряду і рейтинг

**Files:**
- Modify: `scripts/witlib/analysis.py`
- Test: `tests/unit/test_analysis_series.py`

**Interfaces:**
- Consumes: `SeriesInput`, `Periods`, `monthly_sums`, `shares` (Task 4); `seasonality` (Task 7); функції Task 5–6.
- Produces: `SeriesResult(key, topic_index, topic_label, lang, status, title, articles, redirects, substitute, verdict, trust, reasons, metrics, monthly, spikes, seasonality)`; `metrics` має ключі `views` (int), `share` (2 знаки), `growth`, `growth_views`, `growth_share`, `growth_clean`, `months_up`, `months_down`, `window_growth`; `monthly[month] = {"views": int, "share": float}` за всю історію; `spikes` — до 5 найсильніших днів у вікні аналізу `{"date", "views", "typical"}`. `analyze(inp, periods, measure) -> SeriesResult`, `rank_positions(values) -> list[float]`, `rank_series(results, priorities) -> list[dict]` (рядки `{"key", "score", "ranks", "trust", "position"}`; ряди без даних стоять у кінці з `position=None`).

- [ ] **Step 1: Тести**

`tests/unit/test_analysis_series.py`:
```python
from datetime import date

import pytest

from helpers import make_result, synthetic_input
from witlib.analysis import analyze, rank_positions, rank_series
from witlib.series import compute_periods

PERIODS = compute_periods(date(2026, 9, 26), 24)
RECENT_START = "2025-09-01"


def test_steady_growth_is_growing_with_high_trust():
    r = analyze(synthetic_input(PERIODS, lambda d: 60 if d >= RECENT_START else 50), PERIODS, "views")
    assert r.verdict == "growing" and r.trust == "high" and r.reasons == []
    assert r.metrics["growth"] == pytest.approx(0.2) and r.metrics["months_up"] == 12
    assert r.metrics["views"] == round(60 * 365 / 12)
    assert set(r.monthly) == set(PERIODS.history_months)


def test_growth_made_by_one_spike_has_low_trust():
    per_day = lambda d: (52 if d >= RECENT_START else 50) + (4000 if d == "2026-03-10" else 0)  # noqa: E731
    r = analyze(synthetic_input(PERIODS, per_day), PERIODS, "views")
    assert r.verdict == "growing" and r.trust == "low"
    assert r.reasons[0]["code"] == "event_driven" and r.reasons[0]["date"] == "2026-03-10"
    assert r.metrics["growth_clean"] == pytest.approx(0.04)
    assert r.spikes[0]["date"] == "2026-03-10"


def test_missing_article_has_no_data():
    r = analyze(synthetic_input(PERIODS, lambda d: 0, status="no_article", title=None), PERIODS, "share")
    assert (r.verdict, r.trust, r.reasons, r.metrics) == ("no_data", None, [{"code": "no_article", "level": "low"}], {})


def test_new_article_is_flagged():
    r = analyze(synthetic_input(PERIODS, lambda d: 30 if d >= "2025-03-01" else 0), PERIODS, "views")
    assert "new_article" in [x["code"] for x in r.reasons] and r.trust == "low"


def test_share_accounts_for_a_growing_language_edition():
    inp = synthetic_input(PERIODS, lambda d: 100, project=lambda m: 20_000_000 if m >= "2025-09" else 10_000_000)
    r = analyze(inp, PERIODS, "share")
    assert r.metrics["growth_views"] == pytest.approx(0.0) and r.metrics["growth_share"] == pytest.approx(-0.5)
    assert r.verdict == "declining" and r.trust == "high"


def test_rank_positions_average_ties():
    assert rank_positions([3.0, 1.0, 2.0]) == [1.0, 3.0, 2.0]
    assert rank_positions([2.0, 2.0, 1.0]) == [1.5, 1.5, 3.0]


def test_ranking_follows_priorities_and_puts_no_data_last():
    results = [make_result("pl", growth=0.1, share=3.0, views=9000), make_result("cs", growth=0.5, share=1.0, views=100),
               make_result("sk", verdict="no_data", status="no_article")]
    by_growth = rank_series(results, {"growth": 1.0, "interest": 0.0, "reach": 0.0})
    assert [(row["key"], row["position"]) for row in by_growth] == [("cs", 1), ("pl", 2), ("sk", None)]
    by_reach = rank_series(results, {"growth": 0.0, "interest": 0.0, "reach": 1.0})
    assert by_reach[0]["key"] == "pl" and by_reach[0]["ranks"] == {"growth": 2.0, "interest": 1.0, "reach": 1.0}


def test_no_ranking_without_priorities_or_with_one_series():
    results = [make_result("pl"), make_result("cs")]
    assert rank_series(results, None) == []
    assert rank_series(results[:1], {"growth": 1.0, "interest": 0.0, "reach": 0.0}) == []
```

- [ ] **Step 2: Переконатися, що тести падають**

Run: `.venv/bin/python -m pytest tests/unit/test_analysis_series.py -q`
Очікувано: ERROR — `ImportError: cannot import name 'analyze' from 'witlib.analysis'` (`helpers.make_result` падає на імпорті `SeriesResult` так само).

- [ ] **Step 3: Реалізація**

Блок імпортів на початку `scripts/witlib/analysis.py` замінити на:
```python
from __future__ import annotations

import statistics
from dataclasses import dataclass

from .seasonality import seasonality
from .series import Periods, SeriesInput, monthly_sums, shares

LEVEL_ORDER = {"low": 0, "medium": 1, "note": 2}
CRITERIA = (("growth", "growth"), ("interest", "share"), ("reach", "views"))


@dataclass
class SeriesResult:
    key: str
    topic_index: int
    topic_label: str
    lang: str
    status: str
    title: str | None
    articles: list[str]
    redirects: int
    substitute: bool
    verdict: str
    trust: str | None
    reasons: list[dict]
    metrics: dict
    monthly: dict[str, dict[str, float]]
    spikes: list[dict]
    seasonality: dict
```

У кінець `scripts/witlib/analysis.py` додати:
```python


def analyze(inp: SeriesInput, periods: Periods, measure: str) -> SeriesResult:
    """Compute metrics, verdict, trust, spikes and seasonality for one topic x language series."""
    hist, window = periods.history_months, periods.analysis_months
    views = {m: 0.0 for m in hist} | monthly_sums(inp.days, inp.daily)
    share = shares(views, inp.project)
    base = dict(key=inp.key, topic_index=inp.topic_index, topic_label=inp.topic_label, lang=inp.lang,
                status=inp.status, title=inp.title, articles=inp.articles, redirects=inp.redirects,
                substitute=inp.substitute,
                monthly={m: {"views": round(views[m]), "share": round(share[m], 4)} for m in hist})
    if inp.status != "ok":
        return SeriesResult(**base, verdict="no_data", trust=None, reasons=[{"code": inp.status, "level": "low"}],
                            metrics={}, spikes=[], seasonality={"status": "no_data"})
    spike_idx, typical = detect_spikes(inp.daily)
    views_clean = {m: 0.0 for m in hist} | monthly_sums(inp.days, cap_spikes(inp.daily, spike_idx, typical))
    share_clean = shares(views_clean, inp.project)
    primary, primary_clean = (share, share_clean) if measure == "share" else (views, views_clean)
    recent, previous = hist[-12:], hist[-24:-12]
    enough = len(hist) >= 24
    g_views = growth(views, recent, previous) if enough else None
    g_share = growth(share, recent, previous) if enough else None
    g = g_share if measure == "share" else g_views
    g_clean = growth(primary_clean, recent, previous) if enough else None
    up, down = months_up_down(primary, hist) if enough else (0, 0)
    level_views = mean(views[m] for m in recent)
    main_monthly = monthly_sums(inp.days, inp.main_daily)
    first_view = next((m for m in hist if main_monthly.get(m, 0) > 0), None)
    verdict = decide_verdict(g, up, down)
    spikes = _spikes(inp.days, inp.daily, typical, spike_idx)
    event_period = set(previous if verdict == "declining" else recent)
    top_spike = next((s["date"] for s in spikes if s["date"][:7] in event_period), None)
    reasons = trust_reasons(level_views=level_views, verdict=verdict, growth=g, growth_clean=g_clean, months_up=up,
                            months_down=down, first_view_month=first_view,
                            comparison_start=previous[0] if previous else hist[0],
                            substitute_title=inp.title if inp.substitute else None, top_spike=top_spike,
                            growth_views=g_views, growth_share=g_share)
    metrics = {"views": round(level_views), "share": round(mean(share[m] for m in recent), 2), "growth": g,
               "growth_views": g_views, "growth_share": g_share, "growth_clean": g_clean, "months_up": up,
               "months_down": down, "window_growth": window_growth(primary, window)}
    in_window = set(window)
    return SeriesResult(**base, verdict=verdict, trust=trust_level(reasons), reasons=reasons, metrics=metrics,
                        spikes=[s for s in spikes if s["date"][:7] in in_window][:5],
                        seasonality=seasonality(primary_clean, hist, level_views))


def _spikes(days: list[str], daily: list[float], typical: list[float], idx: list[int]) -> list[dict]:
    rows = [{"date": days[i], "views": round(daily[i]), "typical": round(typical[i], 1)} for i in idx]
    return sorted(rows, key=lambda r: r["views"] / r["typical"] if r["typical"] else float("inf"), reverse=True)


def rank_positions(values: list[float]) -> list[float]:
    """1-based ranks, highest value first; ties share the average rank."""
    order = sorted(range(len(values)), key=lambda i: -values[i])
    ranks = [0.0] * len(values)
    start = 0
    while start < len(order):
        end = start
        while end + 1 < len(order) and values[order[end + 1]] == values[order[start]]:
            end += 1
        for k in range(start, end + 1):
            ranks[order[k]] = (start + end) / 2 + 1
        start = end + 1
    return ranks


def rank_series(results: list[SeriesResult], priorities: dict[str, float] | None) -> list[dict]:
    ranked = [r for r in results if r.verdict != "no_data" and r.metrics.get("growth") is not None]
    if not priorities or len(ranked) < 2:
        return []
    n = len(ranked)
    positions = {crit: rank_positions([r.metrics[metric] for r in ranked]) for crit, metric in CRITERIA}
    rows = []
    for i, r in enumerate(ranked):
        score = sum(priorities[crit] * (n - positions[crit][i]) / (n - 1) for crit, _ in CRITERIA)
        rows.append({"key": r.key, "score": round(score, 3), "ranks": {crit: positions[crit][i] for crit, _ in CRITERIA},
                     "trust": r.trust, "growth": r.metrics["growth"]})
    rows.sort(key=lambda row: (-row["score"], -row["growth"]))
    for position, row in enumerate(rows, 1):
        row["position"] = position
        del row["growth"]
    ranked_keys = {r.key for r in ranked}
    rows += [{"key": r.key, "score": None, "ranks": {}, "trust": r.trust, "position": None}
             for r in results if r.key not in ranked_keys]
    return rows
```

- [ ] **Step 4: Тести проходять**

Run: `.venv/bin/python -m pytest tests/unit -q`
Очікувано: усі юніт-тести PASS (включно з 8 новими).

- [ ] **Step 5: Коміт**

```bash
git add scripts/witlib/analysis.py tests/unit/test_analysis_series.py
git commit -m "feat: per-series analysis with trust reasons and priority-weighted ranking" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 9: Пошук теми і статей (resolve) + запис справжніх відповідей

**Files:**
- Create: `scripts/witlib/resolve.py`, `tests/fixtures/record.py`, `tests/fixtures/http/*.json.gz` (записуються)
- Test: `tests/unit/test_resolve.py`

**Interfaces:**
- Consumes: `ApiClient.get_json`; `helpers.fixture_path`
- Produces: `WIKIDATA_API`, `META_TTL = 7 днів`, `wiki_api(lang) -> str`, `build_url(base, params) -> str` (додає `format=json&formatversion=2`), `Candidate(qid, label, description)`, `ResolveResult(qid, label, description, candidates, articles, disambiguation, substitutes, related, related_source)`, `search_entities(client, text, limit=3) -> list[Candidate]`, `get_entities(client, qids, langs, label_langs=("uk", "en")) -> dict[qid, {"labels", "descriptions", "sitelinks"}]`, `page_info(client, lang, titles) -> dict[title, {"exists", "title", "disambiguation", "qid", "redirects"}]`, `search_titles(client, lang, query, limit=3) -> list[str]`, `resolve_topic(client, text, langs, qid=None, with_related=True) -> ResolveResult`. Утиліта запису `tests/fixtures/record.py` зі списком `FLOWS`.

- [ ] **Step 1: Тести**

`tests/unit/test_resolve.py`:
```python
import re

from helpers import FakeTransport
from witlib.api import ApiClient, Response
from witlib.resolve import WIKIDATA_API, build_url, page_info, resolve_topic


def test_resolves_fasting_and_flags_missing_polish_article(client):
    res = resolve_topic(client, "інтервальне голодування", ["pl", "cs"])
    assert res.qid == "Q1666254" and res.label == "Інтервальне голодування"
    assert res.articles == {"pl": None, "cs": "Přerušovaný půst"}
    assert 1 <= len(res.substitutes["pl"]) <= 3
    assert "cs" not in res.substitutes and res.disambiguation == []


def test_related_topics_come_with_wikidata_ids(client):
    res = resolve_topic(client, "інтервальне голодування", ["pl", "cs"])
    assert res.related_source == "cs" and 1 <= len(res.related) <= 8
    for item in res.related:
        assert re.fullmatch(r"Q\d+", item["qid"]) and item["qid"] != "Q1666254"
        assert set(item["langs"]) <= {"pl", "cs"}


def test_disambiguation_page_is_detected(client):
    assert page_info(client, "de", ["Achtsamkeit"])["Achtsamkeit"]["disambiguation"] is True


def test_ambiguous_name_returns_several_candidates(client):
    assert len(resolve_topic(client, "Меркурій", ["de"]).candidates) >= 2


def test_nothing_found_returns_empty_result(tmp_path):
    url = build_url(WIKIDATA_API, {"action": "wbsearchentities", "search": "zzqxw", "language": "en", "uselang": "en", "type": "item", "limit": "3"})
    client = ApiClient(transport=FakeTransport({url: Response(200, '{"search": []}', {})}), cache_dir=tmp_path, sleep=lambda s: None)
    res = resolve_topic(client, "zzqxw", ["pl"])
    assert res.qid is None and res.articles == {"pl": None}
```

- [ ] **Step 2: Переконатися, що тести падають**

Run: `.venv/bin/python -m pytest tests/unit/test_resolve.py -q`
Очікувано: ERROR — `ModuleNotFoundError: No module named 'witlib.resolve'`.

- [ ] **Step 3: Реалізація**

`scripts/witlib/resolve.py`:
```python
"""Topic resolution: Wikidata item -> article per language, disambiguation, substitutes and related topics."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from urllib.parse import urlencode

from .api import ApiClient

WIKIDATA_API = "https://www.wikidata.org/w/api.php"
META_TTL = 7 * 24 * 3600
CYRILLIC = re.compile(r"[Ѐ-ӿ]")


def wiki_api(lang: str) -> str:
    return f"https://{lang}.wikipedia.org/w/api.php"


def build_url(base: str, params: dict[str, str]) -> str:
    return base + "?" + urlencode({**params, "format": "json", "formatversion": "2"})


@dataclass
class Candidate:
    qid: str
    label: str
    description: str


@dataclass
class ResolveResult:
    qid: str | None
    label: str
    description: str
    candidates: list[Candidate] = field(default_factory=list)
    articles: dict[str, str | None] = field(default_factory=dict)
    disambiguation: list[str] = field(default_factory=list)
    substitutes: dict[str, list[str]] = field(default_factory=dict)
    related: list[dict] = field(default_factory=list)
    related_source: str | None = None


def search_entities(client: ApiClient, text: str, limit: int = 3) -> list[Candidate]:
    first = "uk" if CYRILLIC.search(text) else "en"
    for lang in dict.fromkeys([first, "en"]):
        url = build_url(WIKIDATA_API, {"action": "wbsearchentities", "search": text, "language": lang,
                                       "uselang": lang, "type": "item", "limit": str(limit)})
        found = [Candidate(x["id"], x.get("label", ""), x.get("description", ""))
                 for x in client.get_json(url, ttl=META_TTL).get("search", [])]
        if found:
            return found
    return []


def get_entities(client: ApiClient, qids: list[str], langs: list[str], label_langs: tuple[str, ...] = ("uk", "en")) -> dict[str, dict]:
    if not qids:
        return {}
    url = build_url(WIKIDATA_API, {"action": "wbgetentities", "ids": "|".join(qids), "props": "labels|descriptions|sitelinks",
                                   "languages": "|".join(label_langs), "sitefilter": "|".join(f"{lang}wiki" for lang in langs)})
    entities = {}
    for qid, entity in client.get_json(url, ttl=META_TTL).get("entities", {}).items():
        if "missing" in entity:
            continue
        entities[qid] = {
            "labels": {k: v["value"] for k, v in entity.get("labels", {}).items()},
            "descriptions": {k: v["value"] for k, v in entity.get("descriptions", {}).items()},
            "sitelinks": {site[:-4]: link["title"] for site, link in entity.get("sitelinks", {}).items()},
        }
    return entities


def page_info(client: ApiClient, lang: str, titles: list[str]) -> dict[str, dict]:
    titles = list(dict.fromkeys(titles))
    url = build_url(wiki_api(lang), {"action": "query", "titles": "|".join(titles), "prop": "pageprops|redirects",
                                     "ppprop": "disambiguation|wikibase_item", "rdnamespace": "0", "rdlimit": "max",
                                     "redirects": "1"})
    query = client.get_json(url, ttl=META_TTL).get("query", {})
    normalized = {n["from"]: n["to"] for n in query.get("normalized", [])}
    redirected = {r["from"]: r["to"] for r in query.get("redirects", [])}
    pages = {p["title"]: p for p in query.get("pages", [])}
    info = {}
    for title in titles:
        name = normalized.get(title, title)
        name = redirected.get(name, name)
        page = pages.get(name)
        if page is None or page.get("missing") or page.get("invalid"):
            info[title] = {"exists": False, "title": name, "disambiguation": False, "qid": None, "redirects": []}
            continue
        props = page.get("pageprops", {})
        info[title] = {"exists": True, "title": page["title"], "disambiguation": "disambiguation" in props,
                       "qid": props.get("wikibase_item"), "redirects": [r["title"] for r in page.get("redirects", [])]}
    return info


def search_titles(client: ApiClient, lang: str, query: str, limit: int = 3) -> list[str]:
    url = build_url(wiki_api(lang), {"action": "query", "list": "search", "srsearch": query, "srnamespace": "0", "srlimit": str(limit)})
    return [x["title"] for x in client.get_json(url, ttl=META_TTL).get("query", {}).get("search", [])]


def resolve_topic(client: ApiClient, text: str, langs: list[str], qid: str | None = None, with_related: bool = True) -> ResolveResult:
    candidates = [] if qid else search_entities(client, text)
    chosen = qid or (candidates[0].qid if candidates else None)
    if chosen is None:
        return ResolveResult(qid=None, label=text, description="", articles={lang: None for lang in langs})
    prefer = ("uk", "en") if CYRILLIC.search(text) else ("en", "uk")
    entity = get_entities(client, [chosen], langs).get(chosen, {"labels": {}, "descriptions": {}, "sitelinks": {}})
    result = ResolveResult(
        qid=chosen,
        label=next((entity["labels"][lang] for lang in prefer if lang in entity["labels"]), text),
        description=next((entity["descriptions"][lang] for lang in prefer if lang in entity["descriptions"]), ""),
        candidates=candidates,
        articles={lang: entity["sitelinks"].get(lang) for lang in langs},
    )
    for lang, title in result.articles.items():
        if title and page_info(client, lang, [title])[title]["disambiguation"]:
            result.disambiguation.append(lang)
    english = entity["labels"].get("en")
    for lang, title in result.articles.items():
        if title is None:
            found: list[str] = []
            for query in dict.fromkeys(q for q in (english, text) if q):
                found += [t for t in search_titles(client, lang, query) if t not in found]
                if len(found) >= 3:
                    break
            result.substitutes[lang] = found[:3]
    if with_related:
        _add_related(client, result, langs)
    return result


def _add_related(client: ApiClient, result: ResolveResult, langs: list[str], limit: int = 8) -> None:
    source = next((lang for lang in langs if result.articles.get(lang) and lang not in result.disambiguation), None)
    if source is None:
        return
    titles = search_titles(client, source, f"morelike:{result.articles[source]}", limit=limit)
    if not titles:
        return
    infos = page_info(client, source, titles)
    picked: list[tuple[str, str]] = []
    for title in titles:
        item = infos[title]
        if item["exists"] and not item["disambiguation"] and item["qid"] and item["qid"] != result.qid \
                and item["qid"] not in [q for q, _ in picked]:
            picked.append((item["qid"], item["title"]))
    entities = get_entities(client, [q for q, _ in picked], langs)
    result.related_source = source
    result.related = [{"qid": q, "title": t, "langs": [lang for lang in langs if lang in entities.get(q, {}).get("sitelinks", {})]}
                      for q, t in picked]
```

- [ ] **Step 4: Утиліта запису відповідей**

`tests/fixtures/record.py`:
```python
"""Record complete real API responses for the offline tests. Test utility, run manually:

    .venv/bin/python tests/fixtures/record.py

Every URL that the recorded flows request is saved to tests/fixtures/http/ as gzip-compressed JSON.
"""
from __future__ import annotations

import gzip
import json
import sys
import tempfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "tests")]

from helpers import fixture_path  # noqa: E402
from witlib.api import ApiClient, requests_transport  # noqa: E402

AS_OF = date(2026, 9, 26)


def recording_transport(url, headers):
    reply = requests_transport(url, headers)
    path = fixture_path(url)
    path.parent.mkdir(parents=True, exist_ok=True)
    keep = {k: v for k, v in reply.headers.items() if k in ("content-type", "retry-after")}
    record = {"url": url, "status": reply.status, "body": reply.body, "headers": keep}
    path.write_bytes(gzip.compress(json.dumps(record, ensure_ascii=False).encode("utf-8"), mtime=0))
    return reply


def record_resolve(client):
    from witlib.resolve import page_info, resolve_topic

    resolve_topic(client, "інтервальне голодування", ["pl", "cs"])
    resolve_topic(client, "Меркурій", ["de"])
    page_info(client, "de", ["Achtsamkeit"])


FLOWS = [record_resolve]


def main():
    client = ApiClient(transport=recording_transport, cache_dir=Path(tempfile.mkdtemp()))
    for flow in FLOWS:
        flow(client)
    print(f"recorded {client.request_count} responses into {fixture_path('x').parent}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Записати відповіді (потрібен інтернет)**

Run: `.venv/bin/python tests/fixtures/record.py`
Очікувано: `recorded N responses into …/tests/fixtures/http`, де N приблизно 12–16.

- [ ] **Step 6: Тести проходять**

Run: `.venv/bin/python -m pytest tests/unit/test_resolve.py -q`
Очікувано: 5 passed. Якщо `test_ambiguous_name_returns_several_candidates` падає, бо Wikidata повернула одного кандидата, відкрий записану відповідь і заміни в тесті й у `record_resolve` слово на неоднозначніше («Меркурій» → «Mercury»), перезапиши відповіді й повтори.

- [ ] **Step 7: Коміт**

```bash
git add scripts/witlib/resolve.py tests/unit/test_resolve.py tests/fixtures/record.py tests/fixtures/http
git commit -m "feat: resolve topics via Wikidata with disambiguation, substitutes and related topics" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 10: Збір вхідних рядів для дослідження

**Files:**
- Modify: `scripts/witlib/series.py`, `tests/fixtures/record.py`
- Test: `tests/unit/test_collect_inputs.py`

**Interfaces:**
- Consumes: `get_entities`, `page_info` (Task 9); `Study`, `StudyError` (Task 2); функції Task 4.
- Produces: `series_key(topic_index, lang, n_topics, n_langs) -> str` (мова, якщо тема одна; `tN`, якщо тем кілька, а мова одна; інакше `tN.<мова>`), `collect_inputs(client, study, periods) -> tuple[list[SeriesInput], list[str]]` (статуси `ok`, `no_article`, `disambiguation`, `no_views`; другим елементом повертаються попередження).

- [ ] **Step 1: Тести**

`tests/unit/test_collect_inputs.py`:
```python
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
```

- [ ] **Step 2: Переконатися, що тести падають**

Run: `.venv/bin/python -m pytest tests/unit/test_collect_inputs.py -q`
Очікувано: ERROR — `ImportError: cannot import name 'collect_inputs' from 'witlib.series'`.

- [ ] **Step 3: Реалізація**

У `scripts/witlib/series.py` рядок `from .api import ApiClient` замінити на:
```python
from .api import ApiClient
from .resolve import get_entities, page_info
from .study import Study, StudyError
```

У кінець `scripts/witlib/series.py` додати:
```python


def series_key(topic_index: int, lang: str, n_topics: int, n_langs: int) -> str:
    if n_topics == 1:
        return lang
    if n_langs == 1:
        return f"t{topic_index}"
    return f"t{topic_index}.{lang}"


def collect_inputs(client: ApiClient, study: Study, periods: Periods) -> tuple[list[SeriesInput], list[str]]:
    """Find the articles of every topic x language, fetch their daily views and the language totals."""
    warnings: list[str] = []
    qids = list(dict.fromkeys([t.wikidata for t in study.topics] + [q for t in study.topics for q in t.related]))
    entities = get_entities(client, qids, study.languages)
    missing = [q for q in qids if q not in entities]
    if missing:
        raise StudyError([("topics", f"Wikidata item(s) {', '.join(missing)} not found", "Run scripts/wit resolve again and copy the id it prints")])
    start, end = periods.history_start, periods.end_day
    days = day_list(start, end)
    zeros = [0.0] * len(days)
    project = {lang: fetch_project_monthly(client, lang, start, end) for lang in study.languages}
    inputs: list[SeriesInput] = []
    for ti, topic in enumerate(study.topics, 1):
        for lang in study.languages:
            key = series_key(ti, lang, len(study.topics), len(study.languages))
            base = dict(key=key, topic_index=ti, topic_label=topic.label, lang=lang, days=days, project=project[lang])
            substitute = topic.substitutes.get(lang)
            main = substitute or entities[topic.wikidata]["sitelinks"].get(lang)
            if main is None:
                inputs.append(SeriesInput(**base, status="no_article", title=None, articles=[], redirects=0,
                                          substitute=False, daily=zeros, main_daily=zeros))
                continue
            related = [entities[q]["sitelinks"][lang] for q in topic.related if lang in entities[q]["sitelinks"]]
            related = [t for t in dict.fromkeys(related) if t != main]
            info = page_info(client, lang, [main] + related)
            main_info = info[main]
            if not main_info["exists"] or main_info["disambiguation"]:
                status = "disambiguation" if main_info["disambiguation"] else "no_article"
                what = "a disambiguation page" if status == "disambiguation" else "not an existing article"
                warnings.append(f"{key}: '{main}' is {what} in {lang}.wikipedia")
                inputs.append(SeriesInput(**base, status=status, title=main, articles=[], redirects=0,
                                          substitute=bool(substitute), daily=zeros, main_daily=zeros))
                continue
            redirects = main_info["redirects"]
            if len(redirects) > MAX_REDIRECTS:
                warnings.append(f"{key}: {len(redirects)} redirects to '{main_info['title']}', only the first {MAX_REDIRECTS} counted")
                redirects = redirects[:MAX_REDIRECTS]
            main_titles = [main_info["title"]] + redirects
            related_titles = [info[t]["title"] for t in related if info[t]["exists"] and not info[t]["disambiguation"]]
            main_daily = sum_daily([fetch_daily(client, lang, t, start, end) for t in main_titles], days)
            related_daily = sum_daily([fetch_daily(client, lang, t, start, end) for t in related_titles], days)
            daily = [a + b for a, b in zip(main_daily, related_daily)]
            inputs.append(SeriesInput(**base, status="ok" if any(daily) else "no_views", title=main_info["title"],
                                      articles=main_titles[:1] + related_titles, redirects=len(redirects),
                                      substitute=bool(substitute), daily=daily, main_daily=main_daily))
    return inputs, warnings
```

- [ ] **Step 4: Записати відповіді для сценаріїв запуску**

У `tests/fixtures/record.py` перед рядком `FLOWS = [record_resolve]` додати:
```python
def record_runs(client):
    from witlib.series import collect_inputs, compute_periods
    from witlib.study import parse_study

    studies = ROOT / "tests" / "acceptance" / "studies"
    for name in ("e1_fasting", "e2_astronomy", "e3_english"):
        form = json.loads((studies / f"{name}.json").read_text(encoding="utf-8"))
        forms = [form] + ([form | {"languages": form["languages"] + ["sk"]}] if name == "e1_fasting" else [])
        for variant in forms:
            study = parse_study(variant)
            collect_inputs(client, study, compute_periods(AS_OF, study.months))
```
і замінити `FLOWS = [record_resolve]` на `FLOWS = [record_resolve, record_runs]`.

Run: `.venv/bin/python tests/fixtures/record.py`
Очікувано: `recorded N responses …`, де N приблизно 90–130 (≈ 1–2 хв через паузи між запитами). Тека `tests/fixtures/http/` займає до ~3 МБ.

- [ ] **Step 5: Тести проходять**

Run: `.venv/bin/python -m pytest tests/unit -q`
Очікувано: усі юніт-тести PASS.

- [ ] **Step 6: Коміт**

```bash
git add scripts/witlib/series.py tests/unit/test_collect_inputs.py tests/fixtures
git commit -m "feat: collect articles, redirects and daily views for every study series" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---
### Task 11: Тексти звіту, плейсхолдери і запобіжник чисел

**Files:**
- Create: `scripts/witlib/narrative.py`
- Test: `tests/unit/test_narrative.py`

**Interfaces:**
- Consumes: `language_name` (Task 2); об'єкти з полями `SeriesResult` (Task 8); `Study` (Task 2).
- Produces: `METRICS`, `TEXTS` (`uk`/`en`), `NarrativeError`, `fmt_pct(x, lang="en")`, `fmt_int(x, lang)`, `fmt_share(x, lang)`, `fmt_months(up, lang)`, `series_label(result, n_topics, n_langs, lang) -> str`, `reason_text(reason, lang) -> str`, `placeholder_values(results, ranking, lang) -> dict["key.metric", str]`, `render(text, values) -> str`, `invented_numbers(text) -> list[str]`, `agent_texts(summary, steps, values) -> tuple[str | None, list[str] | None]`, `template_summary(results, ranking, labels, lang) -> str`, `template_steps(results, ranking, labels, lang) -> list[str]` (≤ 4, останній — перевірка готовності платити), `build_texts(study, results, ranking) -> {"labels", "values", "summary", "steps", "agent_text"}`.

- [ ] **Step 1: Тести**

`tests/unit/test_narrative.py`:
```python
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
```

- [ ] **Step 2: Переконатися, що тести падають**

Run: `.venv/bin/python -m pytest tests/unit/test_narrative.py -q`
Очікувано: ERROR — `ModuleNotFoundError: No module named 'witlib.narrative'`.

- [ ] **Step 3: Реалізація**

`scripts/witlib/narrative.py`:
```python
"""Report texts: localisation (uk/en), number formats, placeholders, the number guard and template texts."""
from __future__ import annotations

import re

from .languages import language_name

METRICS = ("growth", "growth_clean", "views", "share", "months_up", "trust", "verdict", "peak_month", "rank", "title")
PLACEHOLDER_RE = re.compile(r"\{([^{}]+)\}")
PERCENT_RE = re.compile(r"\d+(?:[.,]\d+)?\s*%")
NUMBER_RE = re.compile(r"\d{1,3}(?:[   ,.]\d{3})+|\d+")

MONTHS_UK = ["січень", "лютий", "березень", "квітень", "травень", "червень", "липень", "серпень", "вересень", "жовтень", "листопад", "грудень"]
MONTHS_UK_LOC = ["січні", "лютому", "березні", "квітні", "травні", "червні", "липні", "серпні", "вересні", "жовтні", "листопаді", "грудні"]
MONTHS_EN = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

TEXTS = {
    "uk": {
        "verdict": {"growing": "зростає", "declining": "падає", "no_clear_trend": "без чіткого тренду", "no_data": "немає даних"},
        "trust": {"high": "висока", "medium": "середня", "low": "низька", None: "—"},
        "months_nom": MONTHS_UK, "months_loc": MONTHS_UK_LOC, "of": "з", "na": "н/д", "none": "немає",
        "no_peak": "немає стабільного піку",
        "reasons": {
            "low_volume": "мало переглядів ({views}/міс.)",
            "moderate_volume": "помірний обсяг ({views}/міс.)",
            "inconsistent_up": "ріст лише у {months} з 12 місяців",
            "inconsistent_down": "спад лише у {months} з 12 місяців",
            "event_driven_up": "ріст пояснюється сплеском{date}",
            "event_driven_down": "падіння пояснюється сплеском у попередньому році{date}",
            "new_article": "стаття з'явилася нещодавно ({month})",
            "substitute": "використано замінник «{title}»",
            "divergence": "перегляди {growth_views}, частка {growth_share}: змінюється весь мовний розділ",
            "no_article": "статті немає",
            "disambiguation": "це сторінка неоднозначності",
            "no_views": "немає переглядів",
        },
        "sum": {
            "growing": "{label}: зростає — {growth} за рік, ріст у {up} з 12 місяців; довіра {trust}{reason}.",
            "declining": "{label}: падає — {growth} за рік, спад у {down} з 12 місяців; довіра {trust}{reason}.",
            "no_clear_trend": "{label}: без чіткого тренду ({growth} за рік, ріст у {up} з 12 місяців); довіра {trust}{reason}.",
            "no_data": "{label}: даних немає — {reason}.",
            "more": "Решта — у таблиці.",
            "season": "Сезонність ({label}): пік у {month} — у {years} з {cycles} років.",
            "rank": "За вашими пріоритетами на першому місці — {label}.",
        },
        "steps": {
            "no_article": "Немає статті: {labels}. Задайте замінника (substitutes) або розгляньте це як незаповнену нішу контенту.",
            "low_volume": "Замало переглядів: {labels}. Додайте пов'язані статті (related) або подовжте період.",
            "event": "Ріст через сплеск: {labels}. Перевірте тренд ще раз через 3–6 місяців.",
            "season": "Плануйте запуск за 1–2 місяці до піку інтересу ({month}).",
            "rank": "Наступна аудиторія для дослідження: {label}.",
            "validate": "Перевірте готовність платити напряму (опитування, тестова реклама): перегляди Wikipedia показують інтерес, а не попит.",
        },
        "headings": {"summary": "Головне", "steps": "Що робити далі", "side": "Сезонність і рейтинг", "rules": "Правила аналізу",
                     "assumptions": "Припущення", "limits": "Обмеження", "source": "Джерело"},
        "table": ["Тема · мова", "Стаття", "Перегл./міс.", "На млн", "Ріст р/р", "Міс. з ростом", "Довіра"],
        "measure": {"share": "частка переглядів на мільйон", "views": "кількість переглядів"},
        "meta": "Період: {start} – {end} ({months} міс.) · мірка: {measure} · дані на {as_of}",
        "trend_title": "Динаміка інтересу (індекс: перші 12 міс. = 100, ковзне середнє 3 міс.)",
        "growth_title": "Ріст за рік: останні 12 міс. проти попередніх 12",
        "side_season": "{label}: пік у {month} ({years} з {cycles} років)",
        "side_no_season": "Стабільної сезонності не виявлено.",
        "side_rank": "{position}. {label} — бал {score}",
        "rules_text": "лише перегляди людей (боти й автоматичний трафік відкинуто); лише повні місяці; додано перегляди редиректів (до 10 на статтю); дні без даних = 0; частка = перегляди / усі перегляди мовного розділу × 1 000 000; ріст = останні 12 міс. проти попередніх 12; сплеск = день, у 5+ разів вищий за типовий.",
        "assumptions_text": "мірка: {measure}; замінники: {substitutes}; пов'язані статті: {related}; пріоритети: {priorities}.",
        "limits_text": "мова ≠ країна; перегляди Wikipedia показують інтерес, а не готовність платити; автоматичний трафік відфільтровано не повністю; замінники й пов'язані статті — непрямі показники.",
        "source_text": "Wikimedia Pageviews API (agent=user), Wikidata; звіт згенеровано {as_of} навичкою wiki-interest-trends.",
        "priority_names": {"growth": "ріст", "interest": "інтерес", "reach": "охоплення"},
    },
    "en": {
        "verdict": {"growing": "growing", "declining": "declining", "no_clear_trend": "no clear trend", "no_data": "no data"},
        "trust": {"high": "high", "medium": "medium", "low": "low", None: "—"},
        "months_nom": MONTHS_EN, "months_loc": MONTHS_EN, "of": "of", "na": "n/a", "none": "none",
        "no_peak": "no stable peak",
        "reasons": {
            "low_volume": "low traffic ({views}/month)",
            "moderate_volume": "moderate traffic ({views}/month)",
            "inconsistent_up": "growth in only {months} of 12 months",
            "inconsistent_down": "decline in only {months} of 12 months",
            "event_driven_up": "growth explained by a spike{date}",
            "event_driven_down": "decline explained by a spike in the previous year{date}",
            "new_article": "the article is new ({month})",
            "substitute": "substitute article \"{title}\" used",
            "divergence": "views {growth_views}, share {growth_share}: the whole language edition is changing",
            "no_article": "no article",
            "disambiguation": "the title is a disambiguation page",
            "no_views": "no views",
        },
        "sum": {
            "growing": "{label}: growing — {growth} a year, up in {up} of 12 months; trust {trust}{reason}.",
            "declining": "{label}: declining — {growth} a year, down in {down} of 12 months; trust {trust}{reason}.",
            "no_clear_trend": "{label}: no clear trend ({growth} a year, up in {up} of 12 months); trust {trust}{reason}.",
            "no_data": "{label}: no data — {reason}.",
            "more": "Other series are in the table.",
            "season": "Seasonality ({label}): peaks in {month} — in {years} of {cycles} years.",
            "rank": "By your priorities, {label} ranks first.",
        },
        "steps": {
            "no_article": "No article: {labels}. Set a substitute or treat it as a content gap.",
            "low_volume": "Too little traffic: {labels}. Add related articles or use a longer period.",
            "event": "Growth driven by a spike: {labels}. Re-check the trend in 3–6 months.",
            "season": "Plan the launch 1–2 months before the peak ({month}).",
            "rank": "Next audience to research: {label}.",
            "validate": "Validate willingness to pay directly (survey, test ads): Wikipedia pageviews show interest, not demand.",
        },
        "headings": {"summary": "Key findings", "steps": "Next steps", "side": "Seasonality and ranking", "rules": "Method",
                     "assumptions": "Assumptions", "limits": "Limitations", "source": "Source"},
        "table": ["Topic · language", "Article", "Views/mo", "Per M", "YoY", "Months up", "Trust"],
        "measure": {"share": "share of views per million", "views": "views"},
        "meta": "Period: {start} – {end} ({months} mo) · measure: {measure} · data as of {as_of}",
        "trend_title": "Interest over time (index: first 12 months = 100, 3-month average)",
        "growth_title": "Year-over-year growth: last 12 months vs previous 12",
        "side_season": "{label}: peak in {month} ({years} of {cycles} years)",
        "side_no_season": "No stable seasonality found.",
        "side_rank": "{position}. {label} — score {score}",
        "rules_text": "human views only (bots and automated traffic excluded); complete months only; redirect views added (up to 10 per article); missing days = 0; share = views / all views of the language edition × 1,000,000; growth = last 12 months vs previous 12; spike = a day 5+ times above typical.",
        "assumptions_text": "measure: {measure}; substitutes: {substitutes}; related articles: {related}; priorities: {priorities}.",
        "limits_text": "language ≠ country; Wikipedia pageviews show interest, not willingness to pay; automated traffic is not fully filtered; substitutes and related articles are indirect measures.",
        "source_text": "Wikimedia Pageviews API (agent=user), Wikidata; generated {as_of} by the wiki-interest-trends skill.",
        "priority_names": {"growth": "growth", "interest": "interest", "reach": "reach"},
    },
}


class NarrativeError(ValueError):
    """The agent's report text is invalid: an unknown placeholder or a number typed without a placeholder."""


def fmt_pct(x: float | None, lang: str = "en") -> str:
    if x is None:
        return TEXTS[lang]["na"]
    points = round(x * 100)
    return f"{points:+d}%" if points else "0%"


def fmt_int(x: float, lang: str) -> str:
    text = f"{round(x):,}"
    return text.replace(",", " ") if lang == "uk" else text


def fmt_share(x: float, lang: str) -> str:
    text = f"{x:.2f}"
    return text.replace(".", ",") if lang == "uk" else text


def fmt_months(up: int, lang: str) -> str:
    return f"{up} {TEXTS[lang]['of']} 12"


def series_label(result, n_topics: int, n_langs: int, lang: str) -> str:
    if n_topics == 1:
        name = language_name(result.lang, lang)
    elif n_langs == 1:
        name = result.topic_label
    else:
        name = f"{result.topic_label} · {language_name(result.lang, lang)}"
    return name[:1].upper() + name[1:]


def reason_text(reason: dict, lang: str) -> str:
    code = reason["code"]
    if code in ("inconsistent", "event_driven"):
        code = f"{code}_{reason.get('direction', 'up')}"
    params = dict(reason)
    if "views" in params:
        params["views"] = fmt_int(params["views"], lang)
    params["date"] = f" ({reason['date']})" if reason.get("date") else ""
    for key in ("growth_views", "growth_share"):
        if key in params:
            params[key] = fmt_pct(params[key], lang)
    return TEXTS[lang]["reasons"][code].format(**params)


def placeholder_values(results, ranking: list[dict], lang: str) -> dict[str, str]:
    t = TEXTS[lang]
    positions = {row["key"]: row["position"] for row in ranking if row.get("position")}
    values: dict[str, str] = {}
    for r in results:
        m, s = r.metrics, r.seasonality
        entries = {
            "title": r.title or "—",
            "verdict": t["verdict"][r.verdict],
            "trust": t["trust"][r.trust],
            "growth": fmt_pct(m.get("growth"), lang),
            "growth_clean": fmt_pct(m.get("growth_clean"), lang),
            "views": fmt_int(m["views"], lang) if "views" in m else t["na"],
            "share": fmt_share(m["share"], lang) if "share" in m else t["na"],
            "months_up": fmt_months(m["months_up"], lang) if "months_up" in m else t["na"],
            "peak_month": t["months_nom"][s["peak_month"] - 1] if s.get("status") == "stable_peak" else t["no_peak"],
            "rank": str(positions[r.key]) if r.key in positions else "—",
        }
        values.update({f"{r.key}.{name}": value for name, value in entries.items()})
    return values


def render(text: str, values: dict[str, str]) -> str:
    unknown = [p for p in PLACEHOLDER_RE.findall(text) if p not in values]
    if unknown:
        keys = sorted({k.rsplit(".", 1)[0] for k in values})
        listed = ", ".join("{" + u + "}" for u in unknown)
        raise NarrativeError(f"unknown placeholder(s) {listed}. FIX: use keys {', '.join(keys)} with metrics "
                             f"{', '.join(METRICS)}, e.g. {{{keys[0]}.growth}}")
    return PLACEHOLDER_RE.sub(lambda match: values[match.group(1)], text)


def invented_numbers(text: str) -> list[str]:
    """Percentages and numbers >= 100 typed without placeholders (years 2000-2099 are allowed)."""
    bare = PLACEHOLDER_RE.sub(" ", text)
    found = [p.strip() for p in PERCENT_RE.findall(bare)]
    for token in NUMBER_RE.findall(PERCENT_RE.sub(" ", bare)):
        value = int(re.sub(r"\D", "", token))
        if value >= 100 and not (len(token) == 4 and 2000 <= value <= 2099):
            found.append(token)
    return found


def agent_texts(summary: str | None, steps: list[str] | None, values: dict[str, str]) -> tuple[str | None, list[str] | None]:
    labelled = ([("summary", summary)] if summary else []) + [(f"next_steps[{i}]", s) for i, s in enumerate(steps or [], 1)]
    problems = [f"{where} contains {', '.join(repr(n) for n in bad)}" for where, text in labelled if (bad := invented_numbers(text))]
    if problems:
        example = next((k for k in values if k.endswith(".growth")), "cs.growth")
        raise NarrativeError("; ".join(problems) + " — numbers must come from the results. "
                             f"FIX: replace them with placeholders such as {{{example}}}")
    return (render(summary, values) if summary else None, [render(s, values) for s in steps] if steps else None)


def template_summary(results, ranking: list[dict], labels: dict[str, str], lang: str) -> str:
    t = TEXTS[lang]
    parts = []
    for r in results[:4]:
        if r.verdict == "no_data":
            parts.append(t["sum"]["no_data"].format(label=labels[r.key], reason=reason_text(r.reasons[0], lang)))
            continue
        m = r.metrics
        reason = f": {reason_text(r.reasons[0], lang)}" if r.trust != "high" and r.reasons else ""
        parts.append(t["sum"][r.verdict].format(label=labels[r.key], growth=fmt_pct(m["growth"], lang), up=m["months_up"],
                                                down=m["months_down"], trust=t["trust"][r.trust], reason=reason))
    if len(results) > 4:
        parts.append(t["sum"]["more"])
    for r in [r for r in results if r.seasonality.get("status") == "stable_peak"][:2]:
        s = r.seasonality
        parts.append(t["sum"]["season"].format(label=labels[r.key], month=t["months_loc"][s["peak_month"] - 1],
                                               years=s["peak_years"], cycles=s["cycles"]))
    top = next((row for row in ranking if row.get("position") == 1), None)
    if top:
        parts.append(t["sum"]["rank"].format(label=labels[top["key"]]))
    return " ".join(parts)


def template_steps(results, ranking: list[dict], labels: dict[str, str], lang: str) -> list[str]:
    t = TEXTS[lang]

    def names(predicate) -> str:
        return ", ".join(labels[r.key] for r in results if predicate(r))

    steps = []
    if missing := names(lambda r: r.status in ("no_article", "disambiguation")):
        steps.append(t["steps"]["no_article"].format(labels=missing))
    if low := names(lambda r: any(x["code"] == "low_volume" for x in r.reasons)):
        steps.append(t["steps"]["low_volume"].format(labels=low))
    if events := names(lambda r: any(x["code"] == "event_driven" for x in r.reasons)):
        steps.append(t["steps"]["event"].format(labels=events))
    seasonal = next((r for r in results if r.seasonality.get("status") == "stable_peak"), None)
    if seasonal:
        steps.append(t["steps"]["season"].format(month=t["months_nom"][seasonal.seasonality["peak_month"] - 1]))
    top = next((row for row in ranking if row.get("position") == 1), None)
    if top:
        steps.append(t["steps"]["rank"].format(label=labels[top["key"]]))
    return steps[:3] + [t["steps"]["validate"]]


def build_texts(study, results, ranking: list[dict]) -> dict:
    lang = study.report_language
    labels = {r.key: series_label(r, len(study.topics), len(study.languages), lang) for r in results}
    values = placeholder_values(results, ranking, lang)
    summary, steps = agent_texts(study.summary, study.next_steps, values)
    return {"labels": labels, "values": values,
            "summary": summary or template_summary(results, ranking, labels, lang),
            "steps": steps or template_steps(results, ranking, labels, lang),
            "agent_text": bool(summary or steps)}
```

- [ ] **Step 4: Тести проходять**

Run: `.venv/bin/python -m pytest tests/unit/test_narrative.py -q`
Очікувано: 14 passed.

- [ ] **Step 5: Коміт**

```bash
git add scripts/witlib/narrative.py tests/unit/test_narrative.py
git commit -m "feat: localised report texts with placeholders and a guard against invented numbers" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 12: Графіки

**Files:**
- Create: `scripts/witlib/charts.py`
- Test: `tests/unit/test_charts.py`

**Interfaces:**
- Consumes: —
- Produces: `TREND_SIZE = (7.3, 2.4)`, `GROWTH_SIZE = (4.4, 1.9)` (дюйми, 200 dpi), `rolling_mean(values, window=3)`, `index_series(values) -> list[float] | None`, `trend_chart(path, months, series=[{"label", "values", "spike_months"}], title) -> Path`, `growth_chart(path, bars=[{"label", "growth", "months_up", "trust"}], title, na_label) -> Path`.

- [ ] **Step 1: Тести**

`tests/unit/test_charts.py`:
```python
from witlib.charts import growth_chart, index_series, rolling_mean, trend_chart

MONTHS = [f"2025-{m:02d}" for m in range(1, 13)] + [f"2026-{m:02d}" for m in range(1, 13)]
PNG = b"\x89PNG"


def test_rolling_mean_and_index():
    assert rolling_mean([3.0, 6.0, 9.0, 12.0]) == [3.0, 4.5, 6.0, 9.0]
    assert index_series([0.0] * 24) is None
    assert index_series([10.0] * 24) == [100.0] * 24


def test_trend_chart_draws_many_series_and_skips_empty_ones(tmp_path):
    series = [{"label": f"L{i}", "values": [float(i + 1)] * 24, "spike_months": ["2026-03"]} for i in range(7)]
    series.append({"label": "empty", "values": [0.0] * 24, "spike_months": []})
    assert trend_chart(tmp_path / "trend.png", MONTHS, series, "Динаміка інтересу").read_bytes()[:4] == PNG


def test_growth_chart_handles_missing_data(tmp_path):
    bars = [{"label": "Чеська", "growth": 0.12, "months_up": 9, "trust": "medium"},
            {"label": "Польська", "growth": None, "months_up": None, "trust": None},
            {"label": "Словацька", "growth": -0.3, "months_up": 2, "trust": "low"}]
    assert growth_chart(tmp_path / "growth.png", bars, "Ріст за рік", "н/д").read_bytes()[:4] == PNG
```

- [ ] **Step 2: Переконатися, що тести падають**

Run: `.venv/bin/python -m pytest tests/unit/test_charts.py -q`
Очікувано: ERROR — `ModuleNotFoundError: No module named 'witlib.charts'`.

- [ ] **Step 3: Реалізація**

`scripts/witlib/charts.py`:
```python
"""Charts for the report (matplotlib, headless)."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

PALETTE = ["#0072B2", "#E69F00", "#009E73", "#CC79A7", "#56B4E9", "#D55E00", "#F0E442", "#000000"]
TRUST_COLORS = {"high": "#009E73", "medium": "#E69F00", "low": "#D55E00"}
NO_DATA_COLOR = "#9E9E9E"
TREND_SIZE = (7.3, 2.4)
GROWTH_SIZE = (4.4, 1.9)


def rolling_mean(values: list[float], window: int = 3) -> list[float]:
    out = []
    for i in range(len(values)):
        chunk = values[max(0, i - window + 1): i + 1]
        out.append(sum(chunk) / len(chunk))
    return out


def index_series(values: list[float]) -> list[float] | None:
    """3-month average indexed to 100 = mean of the first 12 months (first half when shorter than 24)."""
    base_len = 12 if len(values) >= 24 else max(1, len(values) // 2)
    base = sum(values[:base_len]) / base_len
    if base == 0:
        return None
    return [v / base * 100 for v in rolling_mean(values)]


def trend_chart(path: Path, months: list[str], series: list[dict], title: str) -> Path:
    fig, ax = plt.subplots(figsize=TREND_SIZE, dpi=200)
    x = list(range(len(months)))
    for i, item in enumerate(series):
        indexed = index_series(item["values"])
        if indexed is None:
            continue
        color = PALETTE[i % len(PALETTE)]
        ax.plot(x, indexed, color=color, linewidth=1.4, label=item["label"])
        marks = [months.index(m) for m in item.get("spike_months", []) if m in months]
        ax.scatter(marks, [indexed[j] for j in marks], color=color, s=12, zorder=3)
    ax.axhline(100, color="#999999", linewidth=0.6, linestyle="--")
    step = max(1, len(months) // 8)
    ax.set_xticks(x[::step], [months[i] for i in x[::step]], fontsize=6)
    ax.tick_params(axis="y", labelsize=6)
    ax.set_title(title, fontsize=7.5, loc="left")
    ax.spines[["top", "right"]].set_visible(False)
    if ax.get_legend_handles_labels()[0]:
        ax.legend(fontsize=6, frameon=False, ncol=4, loc="upper left")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return Path(path)


def growth_chart(path: Path, bars: list[dict], title: str, na_label: str) -> Path:
    fig, ax = plt.subplots(figsize=GROWTH_SIZE, dpi=200)
    y = list(range(len(bars)))[::-1]
    for yi, bar in zip(y, bars):
        if bar["growth"] is None:
            ax.barh(yi, 0, color=NO_DATA_COLOR)
            ax.text(0, yi, f" {na_label}", va="center", fontsize=6, color="#555555")
            continue
        value = bar["growth"] * 100
        ax.barh(yi, value, color=TRUST_COLORS.get(bar["trust"], NO_DATA_COLOR), height=0.6)
        label = f" {round(value):+d}% · {bar['months_up']}/12 " if bar.get("months_up") is not None else f" {round(value):+d}% "
        ax.text(value, yi, label, va="center", ha="left" if value >= 0 else "right", fontsize=6)
    ax.set_yticks(y, [b["label"] for b in bars], fontsize=6)
    ax.axvline(0, color="#555555", linewidth=0.6)
    ax.tick_params(axis="x", labelsize=6)
    ax.set_title(title, fontsize=7.5, loc="left")
    ax.spines[["top", "right"]].set_visible(False)
    ax.margins(x=0.25)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return Path(path)
```

- [ ] **Step 4: Тести проходять**

Run: `.venv/bin/python -m pytest tests/unit/test_charts.py -q`
Очікувано: 3 passed.

- [ ] **Step 5: Візуальна перевірка (виняток TDD: вигляд)**

Відкрий `trend.png` і `growth.png` з тимчасової теки тесту або згенеруй їх ще раз у `/tmp` і переглянь: підписи читаються, кирилиця на місці, легенда не перекриває лінії.

- [ ] **Step 6: Коміт**

```bash
git add scripts/witlib/charts.py tests/unit/test_charts.py
git commit -m "feat: trend and growth charts for the report" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 13: PDF на одну сторінку

**Files:**
- Create: `scripts/witlib/report.py`
- Test: `tests/unit/test_report.py`

**Interfaces:**
- Consumes: `trend_chart`, `growth_chart`, `TREND_SIZE`, `GROWTH_SIZE` (Task 12); `TEXTS`, `fmt_int`, `fmt_pct`, `fmt_share` (Task 11); `Study`, `Periods`, `SeriesResult`.
- Produces: `FONT_SIZES`, `FONT_FLOORS`, `SCALES`, `font_size(role, scale) -> float` (основний текст ≥ 7 pt, дрібний друк ≥ 5,5 pt), `ReportContent(title, question, meta, summary_heading, summary, trend_png, growth_png, side_heading, side_lines, table_header, table_rows, steps_heading, steps, footer)`, `clip(text, limit)`, `render_pdf(content, path) -> int` (кількість сторінок; зменшує масштаб 1.0 → 0.92 → 0.85 → 0.78, доки не вміститься), `compose(study, periods, results, ranking, texts, trend_png, growth_png) -> ReportContent`, `build_report(folder, study, periods, results, ranking, texts) -> {"report", "trend", "growth": Path}`.

- [ ] **Step 1: Тести**

`tests/unit/test_report.py`:
```python
from datetime import date

from pypdf import PdfReader

from helpers import make_result
from witlib.charts import growth_chart, trend_chart
from witlib.narrative import build_texts
from witlib.report import SCALES, ReportContent, build_report, font_size, render_pdf
from witlib.series import compute_periods
from witlib.study import parse_study

PERIODS = compute_periods(date(2026, 9, 26), 24)


def content(tmp_path, rows=2, text_len=200, steps=3):
    months = PERIODS.analysis_months
    trend = trend_chart(tmp_path / "t.png", months, [{"label": "Чеська", "values": [1.0] * len(months), "spike_months": []}], "Trend")
    growth = growth_chart(tmp_path / "g.png", [{"label": "Чеська", "growth": 0.1, "months_up": 9, "trust": "high"}], "Growth", "n/a")
    table = [["Чеська", "Přerušovaný půst", "110", "1,10", "+8%", "7/12", "низька"]] * (rows - 1)
    table.append(["Українська", "Астрономія", "300", "2,00", "+20%", "10/12", "середня"])
    return ReportContent(
        title="Інтервальне голодування — pl, cs", question="Порівняй зростання інтересу до інтервального голодування",
        meta="Період: 2024-09 – 2026-08", summary_heading="Головне", summary="Висновок. " * (text_len // 10),
        trend_png=trend, growth_png=growth, side_heading="Сезонність і рейтинг", side_lines=["Чеська: пік у січні"],
        table_header=["Тема · мова", "Стаття", "Перегл./міс.", "На млн", "Ріст р/р", "Міс. з ростом", "Довіра"],
        table_rows=table, steps_heading="Що робити далі", steps=["Крок " + "x" * 200] * steps,
        footer=[("Правила аналізу", "лише перегляди людей " * 12), ("Обмеження", "мова ≠ країна " * 10)])


def page_text(path):
    reader = PdfReader(str(path))
    return len(reader.pages), reader.pages[0].extract_text()


def test_typical_report_is_one_page_with_unicode_text(tmp_path):
    path = tmp_path / "report.pdf"
    render_pdf(content(tmp_path), path)
    pages, text = page_text(path)
    assert pages == 1
    assert "Порівняй зростання інтересу" in text and "Přerušovaný půst" in text and "Астрономія" in text


def test_worst_case_still_fits_one_page(tmp_path):
    path = tmp_path / "report.pdf"
    assert render_pdf(content(tmp_path, rows=8, text_len=700, steps=5), path) == 1
    assert page_text(path)[0] == 1


def test_body_text_never_shrinks_below_7pt_and_small_print_below_5_5pt():
    smallest = min(SCALES)
    assert font_size("summary", smallest) >= 7 and font_size("steps", smallest) >= 7
    assert min(font_size(role, smallest) for role in ("table", "side", "footer")) >= 5.5


def test_build_report_writes_charts_and_pdf(tmp_path):
    study = parse_study({"question": "Порівняй інтерес", "topics": [{"label": "Т", "wikidata": "Q1"}], "languages": ["cs", "pl"]})
    results = [make_result("cs", months=PERIODS.history_months), make_result("pl", verdict="no_data", status="no_article")]
    files = build_report(tmp_path, study, PERIODS, results, [], build_texts(study, results, []))
    assert {p.name for p in files.values()} == {"report.pdf", "chart_trend.png", "chart_growth.png"}
    assert page_text(files["report"])[0] == 1
```

- [ ] **Step 2: Переконатися, що тести падають**

Run: `.venv/bin/python -m pytest tests/unit/test_report.py -q`
Очікувано: ERROR — `ModuleNotFoundError: No module named 'witlib.report'`.

- [ ] **Step 3: Реалізація**

`scripts/witlib/report.py`:
```python
"""One-page PDF report (fpdf2) with DejaVu fonts shipped with matplotlib (Cyrillic, Czech and Polish letters)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib
from fpdf import FPDF

from .charts import GROWTH_SIZE, growth_chart, trend_chart
from .narrative import TEXTS, fmt_int, fmt_pct, fmt_share

FONT_DIR = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
PAGE_W, MARGIN = 210, 12
USABLE_W = PAGE_W - 2 * MARGIN
SCALES = (1.0, 0.92, 0.85, 0.78)
COLUMNS = (34, 44, 20, 16, 18, 22, 32)
FONT_SIZES = {"title": 14, "question": 9, "meta": 7.5, "heading": 10.5, "summary": 9, "steps": 8.5,
              "side_heading": 8.5, "side": 7.5, "table": 7.2, "footer": 6.3}
FONT_FLOORS = {"summary": 7.0, "steps": 7.0, "side": 5.5, "table": 5.5, "footer": 5.5}


def font_size(role: str, scale: float) -> float:
    """Point size of a text role at a layout scale: body text never below 7 pt, small print never below 5.5 pt."""
    return max(FONT_SIZES[role] * scale, FONT_FLOORS.get(role, 0.0))


@dataclass
class ReportContent:
    title: str
    question: str
    meta: str
    summary_heading: str
    summary: str
    trend_png: Path
    growth_png: Path
    side_heading: str
    side_lines: list[str]
    table_header: list[str]
    table_rows: list[list[str]]
    steps_heading: str
    steps: list[str]
    footer: list[tuple[str, str]]


def clip(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def render_pdf(content: ReportContent, path: Path) -> int:
    """Write the report, shrinking fonts and images until it fits one page; return the page count."""
    for scale in SCALES:
        pdf = _draw(content, scale)
        if pdf.page_no() == 1:
            break
    pdf.output(str(path))
    return pdf.page_no()


def _draw(c: ReportContent, s: float) -> FPDF:
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_margins(MARGIN, MARGIN, MARGIN)
    pdf.set_auto_page_break(auto=True, margin=MARGIN)
    for style, file in (("", "DejaVuSans.ttf"), ("B", "DejaVuSans-Bold.ttf"), ("I", "DejaVuSans-Oblique.ttf")):
        pdf.add_font("DejaVu", style, str(FONT_DIR / file))
    pdf.add_page()

    def text(role: str, value: str, style: str = "", color: int = 0) -> None:
        size = font_size(role, s)
        pdf.set_font("DejaVu", style, size)
        pdf.set_text_color(color)
        pdf.multi_cell(0, size * 0.45, value, new_x="LMARGIN", new_y="NEXT")

    text("title", c.title, "B")
    text("question", c.question, "I", 60)
    text("meta", c.meta, "", 90)
    pdf.ln(1.5 * s)
    text("heading", c.summary_heading, "B")
    text("summary", clip(c.summary, 700))
    pdf.ln(1.5 * s)
    pdf.image(str(c.trend_png), x=MARGIN, w=USABLE_W * s)
    pdf.ln(1 * s)
    top = pdf.get_y()
    growth_w = 110 * s
    pdf.image(str(c.growth_png), x=MARGIN, y=top, w=growth_w)
    side_x = MARGIN + growth_w + 4
    side_w = PAGE_W - MARGIN - side_x
    pdf.set_xy(side_x, top + 1)
    pdf.set_font("DejaVu", "B", font_size("side_heading", s))
    pdf.set_text_color(0)
    pdf.multi_cell(side_w, font_size("side_heading", s) * 0.47, c.side_heading, new_x="LEFT", new_y="NEXT")
    pdf.set_font("DejaVu", "", font_size("side", s))
    for line in c.side_lines[:6]:
        pdf.set_x(side_x)
        pdf.multi_cell(side_w, font_size("side", s) * 0.45, clip(line, 90), new_x="LEFT", new_y="NEXT")
    pdf.set_xy(MARGIN, max(top + growth_w * GROWTH_SIZE[1] / GROWTH_SIZE[0], pdf.get_y()) + 2 * s)
    _table(pdf, c, s)
    pdf.ln(2 * s)
    text("heading", c.steps_heading, "B")
    for step in c.steps[:5]:
        text("steps", "• " + clip(step, 220))
    pdf.ln(2 * s)
    pdf.set_font("DejaVu", "", font_size("footer", s))
    pdf.set_text_color(100)
    for heading, body in c.footer:
        pdf.multi_cell(0, font_size("footer", s) * 0.44, f"**{heading}:** {body}", markdown=True, new_x="LMARGIN", new_y="NEXT")
    return pdf


def _table(pdf: FPDF, c: ReportContent, s: float) -> None:
    size = font_size("table", s)
    row_h = size * 0.64
    pdf.set_font("DejaVu", "B", size)
    pdf.set_text_color(0)
    pdf.set_fill_color(235, 238, 242)
    for width, head in zip(COLUMNS, c.table_header):
        pdf.cell(width, row_h, _fit(pdf, head, width), border="B", fill=True)
    pdf.ln(row_h)
    pdf.set_font("DejaVu", "", size)
    for row in c.table_rows[:8]:
        for width, value in zip(COLUMNS, row):
            pdf.cell(width, row_h, _fit(pdf, value, width))
        pdf.ln(row_h)


def _fit(pdf: FPDF, value: str, width: float) -> str:
    value = str(value)
    if pdf.get_string_width(value) <= width - 1.5:
        return value
    while value and pdf.get_string_width(value + "…") > width - 1.5:
        value = value[:-1]
    return value + "…"


def compose(study, periods, results, ranking: list[dict], texts: dict, trend_png: Path, growth_png: Path) -> ReportContent:
    lang = study.report_language
    t = TEXTS[lang]
    labels = texts["labels"]
    months = periods.analysis_months
    side = [t["side_season"].format(label=labels[r.key], month=t["months_nom"][r.seasonality["peak_month"] - 1],
                                    years=r.seasonality["peak_years"], cycles=r.seasonality["cycles"])
            for r in results if r.seasonality.get("status") == "stable_peak"] or [t["side_no_season"]]
    side += [t["side_rank"].format(position=row["position"], label=labels[row["key"]], score=fmt_share(row["score"], lang))
             for row in ranking if row.get("position")][:3]
    rows = []
    for r in results:
        title = (r.title or "—") + (" *" if r.substitute else "")
        if r.verdict == "no_data":
            rows.append([labels[r.key], title, t["na"], t["na"], t["na"], t["na"], t["verdict"]["no_data"]])
            continue
        m = r.metrics
        rows.append([labels[r.key], title, fmt_int(m["views"], lang), fmt_share(m["share"], lang),
                     fmt_pct(m["growth"], lang), f"{m['months_up']}/12", t["trust"][r.trust]])
    substitutes = "; ".join(f"{code}: {title}" for topic in study.topics for code, title in topic.substitutes.items()) or t["none"]
    related = ", ".join(q for topic in study.topics for q in topic.related) or t["none"]
    priorities = (", ".join(f"{t['priority_names'][k]} {v:.0%}" for k, v in study.priorities.items())
                  if study.priorities else t["none"])
    as_of = periods.as_of.isoformat()
    return ReportContent(
        title=" · ".join(topic.label for topic in study.topics) + " — " + ", ".join(study.languages),
        question=study.question,
        meta=t["meta"].format(start=months[0], end=months[-1], months=len(months), measure=t["measure"][study.measure], as_of=as_of),
        summary_heading=t["headings"]["summary"], summary=texts["summary"],
        trend_png=trend_png, growth_png=growth_png,
        side_heading=t["headings"]["side"], side_lines=side,
        table_header=list(t["table"]), table_rows=rows,
        steps_heading=t["headings"]["steps"], steps=texts["steps"],
        footer=[(t["headings"]["rules"], t["rules_text"]),
                (t["headings"]["assumptions"], t["assumptions_text"].format(measure=t["measure"][study.measure],
                                                                           substitutes=substitutes, related=related,
                                                                           priorities=priorities)),
                (t["headings"]["limits"], t["limits_text"]),
                (t["headings"]["source"], t["source_text"].format(as_of=as_of))])


def build_report(folder: Path, study, periods, results, ranking: list[dict], texts: dict) -> dict[str, Path]:
    t = TEXTS[study.report_language]
    labels = texts["labels"]
    months = periods.analysis_months
    folder = Path(folder)
    trend = trend_chart(folder / "chart_trend.png", months,
                        [{"label": labels[r.key], "values": [r.monthly[m][study.measure] for m in months],
                          "spike_months": sorted({s["date"][:7] for s in r.spikes})}
                         for r in results if r.verdict != "no_data"], t["trend_title"])
    growth = growth_chart(folder / "chart_growth.png",
                          [{"label": labels[r.key], "growth": r.metrics.get("growth"), "months_up": r.metrics.get("months_up"),
                            "trust": r.trust} for r in results], t["growth_title"], t["na"])
    report = folder / "report.pdf"
    render_pdf(compose(study, periods, results, ranking, texts, trend, growth), report)
    return {"report": report, "trend": trend, "growth": growth}
```

- [ ] **Step 4: Тести проходять**

Run: `.venv/bin/python -m pytest tests/unit/test_report.py -q`
Очікувано: 4 passed.

- [ ] **Step 5: Візуальна перевірка (виняток TDD: вигляд)**

Згенеруй звіт із `test_build_report_writes_charts_and_pdf` у `/tmp`, відкрий PDF і переглянь: блоки не накладаються, таблиця читається, футер дрібний, але розбірливий.

- [ ] **Step 6: Коміт**

```bash
git add scripts/witlib/report.py tests/unit/test_report.py
git commit -m "feat: one-page PDF report with charts, table, next steps and assumptions" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 14: Команди CLI, обгортка і зелені приймальні тести

**Files:**
- Create: `scripts/witlib/cli.py`, `scripts/wit.py`, `scripts/wit`
- Test: `tests/unit/test_cli.py` (+ приймальні тести з Task 1)

**Interfaces:**
- Consumes: усе попереднє.
- Produces: `main(argv=None, *, client=None, out=None, err=None) -> int`; команди `resolve <text> --langs … [--qid] [--question] [--save]` і `run <folder|study.json> [--as-of YYYY-MM-DD] [--refresh]`; вижимка з рядками `STUDY`, по рядку на кожен ряд, `RANKING` (якщо є), `WARNINGS`, `FILES`, `KEYS`, `NEXT`; `findings.json` з ключами `meta`, `series`, `ranking`, `warnings`, `placeholders`.

- [ ] **Step 1: Тести**

`tests/unit/test_cli.py`:
```python
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
```

- [ ] **Step 2: Переконатися, що тести падають**

Run: `.venv/bin/python -m pytest tests/unit/test_cli.py tests/acceptance -q`
Очікувано: FAIL/ERROR — `ModuleNotFoundError: No module named 'witlib.cli'`.

- [ ] **Step 3: Реалізація `cli.py`**

`scripts/witlib/cli.py`:
```python
"""Command line: `wit resolve` finds the topic and its articles; `wit run` executes a study."""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import TextIO

from . import __version__
from .analysis import analyze, rank_series
from .api import ApiClient, WitBudgetError, WitNetworkError
from .languages import normalize_language
from .narrative import METRICS, TEXTS, NarrativeError, build_texts, fmt_pct, reason_text
from .report import build_report
from .resolve import resolve_topic
from .series import collect_inputs, compute_periods
from .study import StudyError, load_study

MONTHS_EN = TEXTS["en"]["months_nom"]
SEASON = {"no_stable_pattern": "no stable peak", "low_volume": "too little traffic",
          "insufficient_history": "history too short", "no_data": "no data"}


def main(argv: list[str] | None = None, *, client: ApiClient | None = None, out: TextIO | None = None,
         err: TextIO | None = None) -> int:
    out, err = out or sys.stdout, err or sys.stderr
    args = _parser().parse_args(argv)
    refresh = getattr(args, "refresh", False)
    if client is None:
        client = ApiClient(refresh=refresh, progress=lambda message: print(message, file=err))
    else:
        client.refresh = refresh
    try:
        return _resolve(args, client, out) if args.command == "resolve" else _run(args, client, out)
    except StudyError as exc:
        print(exc.format(), file=out)
        return 2
    except NarrativeError as exc:
        print(f"ERROR: {exc}", file=out)
        return 2
    except WitBudgetError as exc:
        print(f"ERROR: {exc}\nFIX: use fewer languages or related articles, or split the study", file=out)
        return 2
    except WitNetworkError as exc:
        print(f"ERROR: Wikimedia API unavailable: {exc}\nFIX: wait a minute and run the same command again; "
              "data already downloaded is cached", file=out)
        return 3


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="wit", description="Wikipedia interest trends for product decisions.")
    parser.add_argument("--version", action="version", version=f"wit {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)
    resolve = sub.add_parser("resolve", help="find the Wikidata topic and its article in each language")
    resolve.add_argument("text", help="topic in the user's words")
    resolve.add_argument("--langs", required=True, help="comma-separated Wikipedia codes, e.g. pl,cs")
    resolve.add_argument("--qid", help="use this Wikidata id instead of searching")
    resolve.add_argument("--question", help="the user's question, stored in the saved form")
    resolve.add_argument("--save", help="folder where study.json is written")
    run = sub.add_parser("run", help="run a study folder (or a study.json file)")
    run.add_argument("path")
    run.add_argument("--as-of", help="analyse as of this date (YYYY-MM-DD) for a reproducible report")
    run.add_argument("--refresh", action="store_true", help="ignore cached API responses")
    return parser


def _resolve(args, client: ApiClient, out: TextIO) -> int:
    try:
        langs = list(dict.fromkeys(normalize_language(x) for x in args.langs.split(",") if x.strip()))
    except ValueError as exc:
        print(f"ERROR: --langs: {exc}\nFIX: use Wikipedia codes such as pl,cs,uk", file=out)
        return 2
    res = resolve_topic(client, args.text, langs, qid=args.qid)
    if res.qid is None:
        print(f"ERROR: nothing found in Wikidata for {args.text!r}\nFIX: try the English name of the topic or a more specific phrase", file=out)
        return 2
    print(f"TOPIC     {res.qid}  {res.label} — {res.description or 'no description'}", file=out)
    others = [c for c in res.candidates if c.qid != res.qid][:2]
    listed = " | ".join(f"{c.qid} {c.label} — {c.description}" for c in others) if others else "(none)"
    print(f"          other candidates: {listed}", file=out)
    for i, lang in enumerate(langs):
        title = res.articles.get(lang)
        if title and lang in res.disambiguation:
            line = f'{lang}  {title}  (disambiguation page: put a precise article into "substitutes")'
        elif title:
            line = f"{lang}  {title}"
        else:
            candidates = " | ".join(res.substitutes.get(lang, [])) or "none found"
            line = f"{lang}  — no article. Substitute candidates (check they are the same subject): {candidates}"
        print(("ARTICLES  " if i == 0 else "          ") + line, file=out)
    if res.related:
        items = " | ".join(f"{r['qid']} {r['title']} [{','.join(r['langs'])}]" for r in res.related)
        print(f"RELATED   (from {res.related_source}) {items}", file=out)
    form = {"question": args.question or "", "topics": [{"label": res.label, "wikidata": res.qid}],
            "languages": langs, "months": 24, "measure": "share"}
    if args.save:
        folder = Path(args.save)
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "study.json").write_text(json.dumps(form, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        note = "" if args.question else ' (add the user\'s question to "question")'
        print(f"FORM      saved to {folder / 'study.json'}{note}", file=out)
        print(f"NEXT      add substitutes/related if needed, then: scripts/wit run {folder}", file=out)
    else:
        print("FORM      " + json.dumps(form, ensure_ascii=False), file=out)
        print("NEXT      save it as <folder>/study.json (or rerun with --save <folder>), then: scripts/wit run <folder>", file=out)
    return 0


def _run(args, client: ApiClient, out: TextIO) -> int:
    study, folder = load_study(args.path)
    as_of = date.fromisoformat(args.as_of) if args.as_of else datetime.now(timezone.utc).date()
    periods = compute_periods(as_of, study.months)
    inputs, warnings = collect_inputs(client, study, periods)
    warnings = study.warnings + warnings
    results = [analyze(inp, periods, study.measure) for inp in inputs]
    ranking = rank_series(results, study.priorities)
    texts = build_texts(study, results, ranking)
    if all(r.verdict == "no_data" for r in results):
        for line in _summary(study, periods, results, ranking, warnings, None, texts):
            print(line, file=out)
        print("ERROR: no data for any series\nFIX: set substitutes for languages without an article, "
              "or tell the user the topic has no coverage there", file=out)
        return 4
    build_report(folder, study, periods, results, ranking, texts)
    findings = {"meta": {"version": __version__, "as_of": as_of.isoformat(),
                         "analysis": [periods.analysis_months[0], periods.analysis_months[-1]],
                         "history": [periods.history_months[0], periods.history_months[-1]], "measure": study.measure,
                         "requests": client.request_count, "cache_hits": client.cache_hits,
                         "agent_text": texts["agent_text"]},
                "series": [asdict(r) for r in results], "ranking": ranking, "warnings": warnings,
                "placeholders": texts["values"]}
    (folder / "findings.json").write_text(json.dumps(findings, ensure_ascii=False, indent=1), encoding="utf-8")
    for line in _summary(study, periods, results, ranking, warnings, folder, texts):
        print(line, file=out)
    return 0


def _summary(study, periods, results, ranking, warnings, folder, texts) -> list[str]:
    months = periods.analysis_months
    lines = [f"STUDY    {' + '.join(t.label for t in study.topics)} · {', '.join(study.languages)} · "
             f"{months[0]}..{months[-1]} ({len(months)} months) · measure={study.measure} · as of {periods.as_of}"]
    for r in results:
        if r.verdict == "no_data":
            hint = ' — set "substitutes" or report it as a content gap' if r.status in ("no_article", "disambiguation") else ""
            lines.append(f"  {r.key:<5} NO DATA: {reason_text(r.reasons[0], 'en')}{hint}")
            continue
        m, s = r.metrics, r.seasonality
        why = f" ({reason_text(r.reasons[0], 'en')})" if r.trust != "high" and r.reasons else ""
        season = (f"peak {MONTHS_EN[s['peak_month'] - 1]} ({s['peak_years']}/{s['cycles']} years)"
                  if s["status"] == "stable_peak" else SEASON[s["status"]])
        lines.append(f"  {r.key:<5} {r.title}{' [substitute]' if r.substitute else ''} · {m['views']}/month · "
                     f"{m['share']:.2f} per M · YoY {fmt_pct(m['growth'])} (without spikes {fmt_pct(m['growth_clean'])}) · "
                     f"up {m['months_up']}/12 · {r.verdict} · trust {r.trust}{why} · season: {season}")
    if ranking:
        lines.append("RANKING  " + " > ".join(f"{row['position']}. {row['key']} ({row['score']:.2f})" for row in ranking if row["position"]))
    joined = "; ".join(warnings)
    lines.append("WARNINGS " + ((joined[:297] + "...") if len(joined) > 300 else joined or "none"))
    if folder is not None:
        lines.append(f"FILES    {Path(folder) / 'report.pdf'} (+ findings.json, chart_trend.png, chart_growth.png)")
    keys = sorted({k.rsplit('.', 1)[0] for k in texts["values"]})
    lines.append(f"KEYS     {', '.join(keys)} · METRICS {' '.join(METRICS)}")
    if texts["agent_text"]:
        lines.append("NEXT     report updated with your summary/next_steps")
    else:
        lines.append("NEXT     answer: verdict, growth, trust + reason, one limitation, report path; copy numbers exactly. "
                     "Optional: add summary/next_steps with {key.metric} placeholders and run again")
    return lines
```

- [ ] **Step 4: Точка входу і обгортка (виняток TDD: конфігурація, перевіряється запуском)**

`scripts/wit.py`:
```python
#!/usr/bin/env python3
"""Entry point of the skill CLI. Normally started through scripts/wit, which prepares the environment."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from witlib.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
```

`scripts/wit`:
```bash
#!/usr/bin/env bash
# Runs the skill CLI with pinned dependencies: through uv when available, otherwise in a cached virtualenv.
set -euo pipefail
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REQ="$SKILL_DIR/requirements.txt"
if command -v uv >/dev/null 2>&1; then
  exec uv run --quiet --no-project --with-requirements "$REQ" python "$SKILL_DIR/scripts/wit.py" "$@"
fi
PY="${WIT_PYTHON:-python3}"
if ! "$PY" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)' 2>/dev/null; then
  echo "ERROR: Python 3.12+ is required (found: $("$PY" --version 2>&1 || echo none))." >&2
  echo "FIX: install Python 3.12+ or set WIT_PYTHON to its path." >&2
  exit 5
fi
HASH="$({ shasum -a 256 "$REQ" 2>/dev/null || sha256sum "$REQ"; } | cut -c1-12)"
VENV="${WIT_HOME:-$HOME/.cache/wiki-interest-trends}/venv-$HASH"
if [ ! -f "$VENV/.ready" ]; then
  echo "First run: preparing the Python environment in $VENV (about a minute)..." >&2
  rm -rf "$VENV"
  "$PY" -m venv "$VENV"
  "$VENV/bin/python" -m pip install --quiet --disable-pip-version-check -r "$REQ" >&2
  touch "$VENV/.ready"
fi
exec "$VENV/bin/python" "$SKILL_DIR/scripts/wit.py" "$@"
```

```bash
chmod +x scripts/wit scripts/wit.py
```

- [ ] **Step 5: Юніт-тести CLI і приймальні тести зелені**

Run: `.venv/bin/python -m pytest -q`
Очікувано: усі тести PASS, зокрема 5 приймальних із Task 1. Якщо `test_e2_counts_related_article` падає на назві «Сонячна система», подивись справжню назву в записаній відповіді `wbgetentities` для Q544 і виправ очікування в тесті.

- [ ] **Step 6: Обгортка працює на чистій машині**

Run: `scripts/wit --version`
Очікувано: перший запуск друкує в stderr `First run: preparing the Python environment …`, далі `wit 1.0.0`. Повторний запуск одразу друкує `wit 1.0.0`.

Run: `scripts/wit resolve "інтервальне голодування" --langs pl,cs`
Очікувано: рядки `TOPIC`, `ARTICLES` (pl — no article, cs — Přerušovaný půst), `RELATED`, `FORM`, `NEXT`.

- [ ] **Step 7: Коміт**

```bash
git add scripts/witlib/cli.py scripts/wit.py scripts/wit tests/unit/test_cli.py
git commit -m "feat: resolve/run CLI with compact summary, findings.json and environment wrapper" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---
### Task 15: Довідкові матеріали, шаблон бланку, README

**Files:**
- Create: `references/methodology.md`, `references/study-fields.md`, `references/roadmap.md`, `assets/study-template.json`, `README.md`, `LICENSE`
- Test: `tests/unit/test_assets.py`

**Interfaces:**
- Consumes: `parse_study` (Task 2).
- Produces: файли, на які посилається SKILL.md (Task 18).

- [ ] **Step 1: Тести**

`tests/unit/test_assets.py`:
```python
import json
from pathlib import Path

from witlib.study import parse_study

ROOT = Path(__file__).resolve().parents[2]
FIELDS = ("question", "topics", "label", "wikidata", "related", "substitutes", "languages", "months", "measure",
          "priorities", "report_language", "summary", "next_steps")


def test_study_template_is_a_valid_form():
    study = parse_study(json.loads((ROOT / "assets" / "study-template.json").read_text(encoding="utf-8")))
    assert study.languages == ["pl", "cs"]


def test_field_reference_covers_every_form_field():
    text = (ROOT / "references" / "study-fields.md").read_text(encoding="utf-8")
    assert [name for name in FIELDS if f"`{name}`" not in text] == []


def test_methodology_documents_every_trust_rule():
    text = (ROOT / "references" / "methodology.md").read_text(encoding="utf-8")
    assert [rule for rule in ("R1", "R2", "R3", "R4", "R5", "N1") if rule not in text] == []


def test_roadmap_and_readme_exist():
    assert "v2" in (ROOT / "references" / "roadmap.md").read_text(encoding="utf-8")
    assert "scripts/wit" in (ROOT / "README.md").read_text(encoding="utf-8")
```

- [ ] **Step 2: Переконатися, що тести падають**

Run: `.venv/bin/python -m pytest tests/unit/test_assets.py -q`
Очікувано: 4 failed — `FileNotFoundError` для `assets/study-template.json`, `references/*.md`, `README.md`.

- [ ] **Step 3: Файли**

`assets/study-template.json`:
```json
{
  "question": "<the user's question, verbatim>",
  "topics": [{"label": "<short topic name>", "wikidata": "Q1666254", "related": [], "substitutes": {}}],
  "languages": ["pl", "cs"],
  "months": 24,
  "measure": "share"
}
```

`references/methodology.md`:
````markdown
# Methodology

How `scripts/wit run` turns pageviews into verdicts. The code computes everything below; the agent only explains it.

## Data
- Source: Wikimedia Pageviews API with `agent=user` (spiders and automated traffic excluded) and `access=all-access`.
- Articles for a topic in a language: the Wikidata sitelink (or the `substitutes` title), the articles of `related` items that exist in that language, and up to 10 redirects to the main article. Wikimedia does not count views of redirects towards the target article, so they are added explicitly.
- Daily views for the last 60 complete months, never earlier than 2015-07. Days without data count as zero (the API omits them).
- Complete months only. On the 1st–2nd day of a month the previous month is skipped because it may not be loaded yet. `--as-of` fixes the date for reproducible reports.
- Language-edition totals (`aggregate`, `agent=user`) are used for normalisation.

## Measures
- `views`: average views per month over the last 12 months.
- `share`: views per million views of the whole language edition. It removes the effect of a growing or shrinking Wikipedia and makes small and large editions comparable. This is the default measure.

## Growth
- Year-over-year growth = mean of the last 12 months / mean of the previous 12 months − 1. It is computed for both measures; the verdict uses `measure`. Comparing whole years cancels seasonality.
- For `months` ≥ 36 the report also gives annualised growth between the first and the last 12 months of the window.
- Months up (down): in how many of the last 12 months the value is above (below) the same month a year earlier.

## Spikes
A day is a spike when it has at least 20 views and more than max(5 × median, median + 10 × MAD) of the previous 28 days. `growth_clean` is the growth recomputed with spike days replaced by that median.

## Verdict
| verdict | rule |
|---|---|
| growing | growth ≥ +10% and up in at least 7 of 12 months |
| declining | growth ≤ −10% and down in at least 7 of 12 months |
| no clear trend | otherwise |
| no data | no article, a disambiguation page, or zero views |

## Trust
Trust starts at high. Each rule can lower it and adds its reason to the summary and the report.

| rule | condition | effect |
|---|---|---|
| R1 volume | under 100 views a month / 100–499 | low / at most medium |
| R2 consistency | growing or declining in only 7–8 of 12 months | at most medium |
| R3 event | without spike days the growth drops under 10% or under half (for a decline: mirrored) | low |
| R4 new article | the first month with views falls inside the two compared years | low |
| R5 substitute | a substitute article is used | at most medium |
| N1 divergence | views and share move in opposite directions, both by at least 5% | note only |

## Seasonality
Computed on spike-free data of up to five yearly cycles (at least three, and at least 100 views a month). Each cycle is divided by its own mean and the month-of-year profile is averaged. The peak is stable when it is the top month in at least 60% of cycles and at least 20% above the yearly mean.

## Ranking
Only when `priorities` are given. For growth, interest (share) and reach (views) every series gets a rank; score = Σ weight × (n − rank) / (n − 1). Trust is shown next to the score but is not part of it.

## Limitations
- A language edition is not a country: it is read in many countries, and people also read other editions.
- Pageviews measure interest, not willingness to pay.
- Automated traffic is filtered by Wikimedia heuristics, not perfectly.
- A topic is measured through a few articles; substitutes and related articles are indirect measures.
````

`references/study-fields.md`:
````markdown
# study.json fields

| field | type | default | meaning |
|---|---|---|---|
| `question` | text, ≤ 500 characters | required | the user's question, verbatim; printed on the report |
| `topics` | 1–3 objects | required | what to compare |
| `label` | text, ≤ 80 characters | required | topic name used in the report |
| `wikidata` | `Q…` | required | Wikidata id printed by `resolve` |
| `related` | list of `Q…`, ≤ 10 | `[]` | extra articles for broad topics, counted where they exist |
| `substitutes` | `{language: article title}` | `{}` | article to use where the topic has no article; flagged as a substitute |
| `languages` | 1–8 codes | required | Wikipedia editions such as `pl`, `cs`, `uk`; names like "Polish" are accepted |
| `months` | 12–120 | 24 | analysis window in complete months |
| `measure` | `share` or `views` | `share` | measure used for verdicts and charts |
| `priorities` | weights for `growth`, `interest`, `reach` | none | turns on the ranking of audiences |
| `report_language` | `uk` or `en` | from the question | language of the PDF |
| `summary` | text, ≤ 600 characters | template | your summary; numbers only as `{key.metric}` |
| `next_steps` | ≤ 5 texts, ≤ 200 characters each | template | your recommendations; same rule |

Limit: topics × languages ≤ 8.

## Placeholders
`{key.metric}`. The key is the language code when there is one topic (`cs`), `t1`…`t3` when there are several topics and one language, otherwise `t1.cs`. Metrics: `growth`, `growth_clean`, `views`, `share`, `months_up`, `trust`, `verdict`, `peak_month`, `rank`, `title`. `run` prints the valid keys. Percentages and numbers of 100 or more typed without a placeholder are rejected.

## Follow-up edits
| the user says | edit |
|---|---|
| "add Slovak" | append `"sk"` to `languages` |
| "last five years" | `"months": 60` |
| "growth matters more" | raise `priorities.growth` |
| "absolute numbers" | `"measure": "views"` |
| "use article X for Polish" | `"substitutes": {"pl": "X"}` |

## Examples
```json
{"question": "Порівняй зростання інтересу до інтервального голодування в польськомовній та чеськомовній Wikipedia за останні два роки.",
 "topics": [{"label": "Інтервальне голодування", "wikidata": "Q1666254"}], "languages": ["pl", "cs"], "months": 24}
```
```json
{"question": "Порівняй інтерес до вивчення англійської в pl, cs, uk, tr, id: які аудиторії дослідити наступними?",
 "topics": [{"label": "Вивчення англійської", "wikidata": "Q1860", "related": ["Q490396", "Q487425", "Q130192"]}],
 "languages": ["pl", "cs", "uk", "tr", "id"], "priorities": {"growth": 0.4, "interest": 0.3, "reach": 0.3}}
```
````

`references/roadmap.md`:
````markdown
# Roadmap

## v1 — this version
One to three topics in up to eight language editions; growth, trust with reasons, seasonality, ranking by the user's priorities; one-page PDF; follow-ups by editing `study.json` with cached data. Verified by unit and acceptance tests on recorded API responses and by scenarios run on Claude Haiku 4.5.

## v2 — more precise answers
- Suggest related articles automatically and rank them by traffic (today: `morelike` suggestions confirmed by the user).
- Bot filter: compare mobile and desktop trends; desktop-only surges are a typical automated-traffic signature.
- Follow page moves (MediaWiki `logevents`) so renamed articles keep their history.
- Forecast with a prediction interval for the next 6–12 months.

## v3 — more data
- Replace per-article API calls with the bulk pageview dumps (`dumps.wikimedia.org/other/pageview_complete`, about 5 GB per month) loaded into a local DuckDB/Parquet store with incremental monthly updates: hundreds of articles × all languages without API limits.
- Discovery mode: "what is rising in language X or around topic Y", with SPARQL over Wikidata to group articles into topics.
- A persistent SQLite cache shared between studies; parallel fetching within Wikimedia's limit of three concurrent requests.

## v4 — countries and outside signals
- The differentially private country × page dataset (`analytics.wikimedia.org/published/datasets/country_project_page`, daily since 2023-02) to measure interest by country, not only by language.
- The official Google Trends API as a second signal once it leaves the application-only alpha (announced 2025-07). The unofficial `pytrends` library is archived and not suitable.
- Edit activity as a signal of content freshness. Not as "controversy": on popular topics most reverts are vandalism clean-up.

## How the skill grows safely
- Every new rule starts as a failing test on synthetic data; every new kind of request becomes a scenario in `evals/scenarios.json` that must pass on a cheap model before release.
- Recorded API responses keep reports reproducible in regression tests.
````

`README.md`:
````markdown
# wiki-interest-trends

An [Agent Skill](https://agentskills.io/specification) that helps B2C founders decide which topics to build and which languages to launch in, using Wikipedia pageviews. The agent turns a question into a small study form; the skill's Python code downloads the data, computes growth and how far to trust it, finds seasonality, ranks audiences by your priorities and produces charts plus a one-page PDF.

Designed and tested for a cheap, fast model (Claude Haiku 4.5): the agent makes one decision (the form) and writes the conclusion; every number comes from the code.

## Install
Requires Python 3.12+ and internet access.

```bash
git clone <this repository> ~/.claude/skills/wiki-interest-trends
```
or clone into `<project>/.claude/skills/`. On first use `scripts/wit` either runs through `uv` or creates a pinned virtualenv in `~/.cache/wiki-interest-trends/` (about a minute). Optional: `export WIT_CONTACT=<your email or URL>` for the Wikimedia User-Agent.

## Try it
Ask your agent, for example:
- «Порівняй зростання інтересу до інтервального голодування в польськомовній та чеськомовній Wikipedia за останні два роки.»
- «Ми думаємо додати курс з астрономії. Чи зростає інтерес до цієї теми в україномовній Wikipedia, і наскільки цьому зростанню можна довіряти?»
- «Порівняй інтерес до вивчення англійської в польській, чеській, українській, турецькій та індонезійській Wikipedia: які аудиторії варто дослідити наступними й чому?»

Or run it yourself:
```bash
scripts/wit resolve "intermittent fasting" --langs pl,cs --question "Compare interest in pl and cs" --save wiki-studies/fasting
scripts/wit run wiki-studies/fasting
```

## How it works
```
question → agent → scripts/wit resolve  (Wikidata topic, article per language, substitutes, related topics)
                 → study.json            (the assumptions, editable for follow-ups)
                 → scripts/wit run       (data → growth, trust, seasonality, ranking → charts → report.pdf)
                 → answer                (numbers copied from the run summary)
```
Details: [references/methodology.md](references/methodology.md) · decisions: [docs/adr/0001-architecture.md](docs/adr/0001-architecture.md) · spec: [docs/specs/](docs/specs/) · roadmap: [references/roadmap.md](references/roadmap.md).

## How it was verified
- Unit and acceptance tests written before the code, on synthetic series and on recorded real API responses: `.venv/bin/python -m pytest`.
- Live checks against the real API: `.venv/bin/python -m pytest -m live`.
- The case scenarios run end to end on Claude Haiku 4.5: `evals/`.
- Independent cross-check of numbers and notes on how AI tools were used: [docs/verification.md](docs/verification.md).

## Development
```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest
```

## License
MIT — see [LICENSE](LICENSE).
````

`LICENSE`:
```
MIT License

Copyright (c) 2026 Vitalii

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

- [ ] **Step 4: Тести проходять**

Run: `.venv/bin/python -m pytest tests/unit/test_assets.py -q`
Очікувано: 4 passed.

- [ ] **Step 5: Коміт**

```bash
git add assets references README.md LICENSE tests/unit/test_assets.py
git commit -m "docs: methodology, form reference, roadmap, README and study template" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 16: Живі перевірки і незалежна звірка чисел

**Files:**
- Create: `tests/live/test_live_api.py`, `tests/live/crosscheck.py`, `docs/verification.md`

**Interfaces:**
- Consumes: `ApiClient`, `fetch_daily`, `PAGEVIEWS`, `get_entities`.
- Produces: `docs/verification.md` (розділи 1–3; розділ 4 заповнюється в Task 18).

- [ ] **Step 1: Живі тести**

`tests/live/test_live_api.py`:
```python
from datetime import date

import pytest

pytestmark = pytest.mark.live


def test_daily_views_add_up_to_the_apis_monthly_total(tmp_path):
    from witlib.api import ApiClient
    from witlib.series import PAGEVIEWS, fetch_daily

    client = ApiClient(cache_dir=tmp_path)
    daily = fetch_daily(client, "cs", "Přerušovaný půst", date(2026, 8, 1), date(2026, 8, 31))
    monthly = client.get_json(f"{PAGEVIEWS}/per-article/cs.wikipedia.org/all-access/user/"
                              "P%C5%99eru%C5%A1ovan%C3%BD_p%C5%AFst/monthly/2026080100/2026083100")
    assert sum(daily.values()) == monthly["items"][0]["views"]


def test_polish_article_on_intermittent_fasting_is_still_missing(tmp_path):
    from witlib.api import ApiClient
    from witlib.resolve import get_entities

    entity = get_entities(ApiClient(cache_dir=tmp_path), ["Q1666254"], ["pl", "cs"])["Q1666254"]
    assert "pl" not in entity["sitelinks"] and entity["sitelinks"]["cs"] == "Přerušovaný půst"
```

Run: `.venv/bin/python -m pytest -m live -q`
Очікувано: 2 passed. Спершу запусти без реалізації змін — тести перевіряють уже написаний код на справжніх даних; якщо падають, це дефект або змінилися дані: з'ясуй причину, не підганяй тест.

- [ ] **Step 2: Скрипт звірки**

`tests/live/crosscheck.py`:
```python
"""Cross-check our daily sums against the API's own monthly totals and print links for a manual check."""
import sys
from datetime import date
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from witlib.api import ApiClient  # noqa: E402
from witlib.series import PAGEVIEWS, fetch_daily  # noqa: E402

CASES = [("cs", "Přerušovaný půst"), ("uk", "Астрономія"), ("pl", "Język angielski")]
START, END = date(2025, 9, 1), date(2026, 8, 31)


def main():
    client = ApiClient()
    print("| article | our sum of daily views | API monthly total | match | manual check |")
    print("|---|---|---|---|---|")
    for lang, title in CASES:
        ours = sum(fetch_daily(client, lang, title, START, END).values())
        encoded = quote(title.replace(" ", "_"), safe="")
        url = f"{PAGEVIEWS}/per-article/{lang}.wikipedia.org/all-access/user/{encoded}/monthly/{START:%Y%m%d}00/{END:%Y%m%d}00"
        theirs = sum(item["views"] for item in client.get_json(url)["items"])
        link = (f"https://pageviews.wmcloud.org/?project={lang}.wikipedia.org&platform=all-access&agent=user"
                f"&redirects=0&start={START}&end={END}&pages={encoded}")
        print(f"| {lang}: {title} | {ours} | {theirs} | {'yes' if ours == theirs else 'NO'} | [pageviews.wmcloud.org]({link}) |")


if __name__ == "__main__":
    main()
```

Run: `.venv/bin/python tests/live/crosscheck.py`
Очікувано: таблиця з трьох рядків, у колонці `match` скрізь `yes`.

- [ ] **Step 3: Ручна звірка з незалежним інструментом**

Відкрий у браузері посилання з першого рядка таблиці (pageviews.wmcloud.org, той самий період, `agent=user`, без редиректів) і порівняй загальну суму переглядів із колонкою «our sum». Запиши результат.

- [ ] **Step 4: `docs/verification.md`**

````markdown
# Verification

How the results of this skill, and of the AI tools used to build it, were checked.

## 1. Design claims checked against live data (2026-09-24…26)
- The first case example hides a trap: Wikidata Q1666254 (intermittent fasting) has cs/uk/en/de articles but no Polish one. The skill reports the gap instead of comparing different things.
- A monthly request ending mid-month returns a partial last month (end=2025-04-01 gave April = 732 views vs ~20,000 in other months), so the skill uses complete months only.
- The API omits zero-view days and answers 404 for "zero or not loaded"; the skill fills zeros.
- Views of redirects are not counted in the target article; the skill adds up to 10 redirects.
- Rate limits (2026): 10 requests/min without an identifying User-Agent, 200/min with one, at most 3 concurrent; the skill sends sequential requests with a contact User-Agent and caches responses.
- An alternative architecture was evaluated against data before rejecting it (Wikidata SPARQL "subclass of" suggestions, edit-war index, `pytrends`, WeasyPrint): see [ADR-001](adr/0001-architecture.md).

## 2. Tests written before code
Every module was built test-first (red → green → refactor), see the commit history. Unit tests use synthetic series with known answers for every rule and threshold (for example 99 vs 100 views). Acceptance tests run the three case scenarios end to end on recorded, complete API responses (`tests/fixtures/http/`).

```bash
.venv/bin/python -m pytest          # offline suite
.venv/bin/python -m pytest -m live  # against the real API
```

## 3. Independent cross-check of numbers
Output of `tests/live/crosscheck.py` (daily sums used by the skill vs the API's own monthly totals):

<paste the printed table here>

Manual check on pageviews.wmcloud.org for the first row: <result of Step 3>.

## 4. Full scenario on Claude Haiku 4.5
Filled in after the eval runs (Task 18).

## 5. How AI tools were used
- Claude (Opus) was used for brainstorming, the architecture decision, the specification, the plan and the code, following test-driven development.
- Every factual claim about external APIs was verified with live requests before it shaped the design; claims that failed (for example, that Wikidata "subclass of" yields reader-relevant related topics) were dropped.
- Every rule is covered by a test that was seen failing first; generated PDFs and charts were reviewed visually.
- The agent-facing part (SKILL.md) was checked by running the case scenarios on a cheap model and comparing the answers with the computed findings.
````

Заміни рядки `<paste the printed table here>` і `<result of Step 3>` фактичним виводом кроку 2 і результатом кроку 3; це дані вимірювань, а не заготовки.

- [ ] **Step 5: Коміт**

```bash
git add tests/live docs/verification.md
git commit -m "test: live API checks, independent cross-check and verification notes" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 17: Сценарії для Haiku і скрипт перевірки (базовий прогін без навички — червоний)

**Files:**
- Create: `evals/scenarios.json`, `evals/check.py`, `evals/run_evals.py`, `evals/subagent_prompt.md`, `evals/results/*.md`
- Test: `tests/unit/test_eval_check.py`

**Interfaces:**
- Consumes: `pypdf`; файли `wiki-studies/*/{study.json,findings.json,report.pdf}` і `answer.md` у робочій теці сценарію.
- Produces: `percents_in(text) -> set[int]`, `allowed_percents(findings, study) -> set[int]`, `check_scenario(scenario, workdir) -> list[str]` (порожній список означає PASS); `python evals/check.py [workdir]` друкує таблицю; `python evals/run_evals.py [--model] [--no-skill] [--only E1,F1]` запускає Claude Code без участі людини й пише `evals/results/<час>-<мітка>.md`.

- [ ] **Step 1: Тести скрипта перевірки**

`tests/unit/test_eval_check.py`:
```python
import json
import sys
from pathlib import Path

from fpdf import FPDF

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "evals"))
from check import allowed_percents, check_scenario, percents_in  # noqa: E402

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
```

Run: `.venv/bin/python -m pytest tests/unit/test_eval_check.py -q`
Очікувано: ERROR — `ModuleNotFoundError: No module named 'check'`.

- [ ] **Step 2: Сценарії**

`evals/scenarios.json`:
```json
[
  {"id": "E1", "prompt": "Порівняй зростання інтересу до інтервального голодування в польськомовній та чеськомовній Wikipedia за останні два роки."},
  {"id": "E2", "prompt": "Ми думаємо додати курс з астрономії до освітнього застосунку. Чи зростає інтерес до цієї теми в україномовній Wikipedia, і наскільки цьому зростанню можна довіряти?"},
  {"id": "E3", "prompt": "Ми створюємо застосунок для вивчення мов. Порівняй інтерес до вивчення англійської у вибраних нами мовних розділах — польському, чеському, українському, турецькому та індонезійському — та підготуй короткий звіт: які аудиторії варто дослідити наступними й чому?"},
  {"id": "F1", "after": "E1", "prompt": "Додай словацьку."},
  {"id": "F2", "after": "E3", "prompt": "Для нас ріст важливіший за розмір аудиторії. Перерахуй."},
  {"id": "T1", "clarification_ok": true, "prompt": "Чи зростає інтерес до Меркурія в німецькій Wikipedia?"},
  {"id": "T2", "prompt": "Чи зростає інтерес до сонячних затемнень в іспаномовній Wikipedia?"}
]
```

- [ ] **Step 3: Скрипт перевірки**

`evals/check.py`:
```python
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
```

Run: `.venv/bin/python -m pytest tests/unit/test_eval_check.py -q`
Очікувано: 6 passed.

- [ ] **Step 4: Запуск сценаріїв без участі людини (варіант A, CLI Claude Code)**

`evals/run_evals.py`:
```python
"""Run the eval scenarios with Claude Code in headless mode on a cheap model and check the results.

Usage (from the skill root):
    python evals/run_evals.py                  # with the skill installed (GREEN run)
    python evals/run_evals.py --no-skill       # baseline without the skill (RED run)
    python evals/run_evals.py --only E1,F1
Requires the `claude` CLI (Claude Code) installed and logged in.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
sys.path.insert(0, str(HERE))

from check import check_scenario  # noqa: E402

IGNORE = shutil.ignore_patterns(".git", ".venv", "evals", "tests", "docs", "__pycache__", ".pytest_cache", "wiki-studies")
TOOLS = ["Bash", "Read", "Write", "Edit", "Glob", "Grep"]


def ask(prompt: str, cwd: Path, model: str, resume: str | None) -> dict:
    command = ["claude", "-p", prompt, "--model", model, "--output-format", "json", "--max-turns", "40", "--allowedTools", *TOOLS]
    if resume:
        command += ["--resume", resume]
    started = time.time()
    proc = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=1500)
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        data = {"result": proc.stdout + proc.stderr}
    data["seconds"] = round(time.time() - started)
    return data


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="claude-haiku-4-5-20251001")
    parser.add_argument("--no-skill", action="store_true")
    parser.add_argument("--only", default="")
    args = parser.parse_args()
    only = set(filter(None, args.only.split(",")))
    root = HERE / "workdir"
    sessions: dict[str, tuple[str | None, Path]] = {}
    rows = []
    for scenario in json.loads((HERE / "scenarios.json").read_text(encoding="utf-8")):
        sid = scenario["id"]
        if only and sid not in only:
            continue
        workdir = root / sid
        if workdir.exists():
            shutil.rmtree(workdir)
        if "after" in scenario:
            if scenario["after"] not in sessions:
                rows.append((sid, "SKIP", f"run {scenario['after']} first", 0, None))
                continue
            session, parent_dir = sessions[scenario["after"]]
            data = ask(scenario["prompt"], parent_dir, args.model, session)
            shutil.copytree(parent_dir, workdir, ignore=shutil.ignore_patterns(".claude"))
        else:
            (workdir / ".claude" / "skills").mkdir(parents=True)
            if not args.no_skill:
                shutil.copytree(SKILL, workdir / ".claude" / "skills" / SKILL.name, ignore=IGNORE)
            data = ask(scenario["prompt"], workdir, args.model, None)
            sessions[sid] = (data.get("session_id"), workdir)
        (workdir / "answer.md").write_text(data.get("result", ""), encoding="utf-8")
        failures = check_scenario(scenario, workdir)
        rows.append((sid, "FAIL" if failures else "PASS", "; ".join(failures), data["seconds"], data.get("total_cost_usd")))
    label = "baseline-no-skill" if args.no_skill else "with-skill"
    stamp = datetime.now().strftime("%Y%m%d-%H%M")
    lines = [f"# Eval run {stamp} · {label} · model {args.model}", "",
             "| scenario | result | seconds | cost, $ | details |", "|---|---|---|---|---|"]
    lines += [f"| {sid} | {res} | {sec} | {cost if cost is not None else '—'} | {details} |" for sid, res, details, sec, cost in rows]
    out = HERE / "results" / f"{stamp}-{label}.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0 if rows and all(r[1] == "PASS" for r in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 5: Запуск сценаріїв через субагента (варіант B, без встановлення CLI)**

`evals/subagent_prompt.md`:
```markdown
You are an AI assistant helping the founder of a B2C product. Work only inside this folder: {workdir}
(create it if needed and run every command from it).

An Agent Skill is installed at {skill_dir}:
  name: wiki-interest-trends
  description: {description}

If the request matches the description, read {skill_dir}/SKILL.md first and follow it exactly.
When you are done, write your final answer to the user, in the user's language, into {workdir}/answer.md
and also return it as your final message.

User request: {prompt}
```

Процедура для оркестратора (сесія Claude Code, у якій виконується план):
1. Для кожного сценарію без `after` запусти субагента з `model: "haiku"` із промптом вище: `{workdir}` = `evals/workdir/<id>` (абсолютний шлях), `{skill_dir}` = абсолютний шлях до навички, `{description}` — поле `description` з SKILL.md, `{prompt}` — зі `scenarios.json`. Для базового прогону (RED) прибери з промпту блок про навичку.
2. Для `F1`/`F2` продовж того самого субагента (SendMessage) повідомленням `User follow-up: <prompt>. Update {workdir}/answer.md.`, а потім скопіюй теку батьківського сценарію в `evals/workdir/<id>/`.
3. Після кожного сценарію запусти `.venv/bin/python evals/check.py evals/workdir` і збережи таблицю в `evals/results/<YYYYMMDD-HHMM>-<baseline-no-skill|with-skill>-subagent.md` із заголовком «model haiku (subagent)».

- [ ] **Step 6: Базовий прогін без навички (RED)**

SKILL.md ще немає, тому агент не має навички. Запусти обраний варіант:
- A: `python3 evals/run_evals.py --no-skill`
- B: процедура з кроку 5 без блоку про навичку.

Очікувано: більшість сценаріїв FAIL. Типові причини: `no wiki-studies/*/study.json was created`, `report.pdf missing`, вигадані відсотки. Файл `evals/results/*-baseline-no-skill*.md` фіксує, що без навички модель не справляється. Це і є «червоний» стан для SKILL.md.

- [ ] **Step 7: Коміт**

```bash
git add evals tests/unit/test_eval_check.py
git commit -m "test: eval scenarios, answer checker and failing baseline without the skill" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 18: SKILL.md і зелений прогін на Haiku

**Files:**
- Create: `SKILL.md`
- Modify: `docs/verification.md` (розділ 4), `README.md` (результат прогону)
- Test: `tests/unit/test_skill_md.py`, `evals/`

**Interfaces:**
- Consumes: команди `scripts/wit resolve|run` (Task 14), `references/*.md` (Task 15), сценарії й перевірка (Task 17).
- Produces: SKILL.md, валідний за специфікацією Agent Skills.

- [ ] **Step 1: Тест відповідності специфікації Agent Skills**

`tests/unit/test_skill_md.py`:
```python
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def frontmatter(text):
    assert text.startswith("---\n"), "SKILL.md must start with YAML frontmatter"
    head, body = text[4:].split("\n---\n", 1)
    fields = {}
    for line in head.splitlines():
        if re.match(r"^[a-z-]+:", line):
            key, _, value = line.partition(":")
            fields[key] = value.strip()
    return fields, body


def test_skill_md_follows_the_agent_skills_spec():
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    fields, _body = frontmatter(text)
    assert fields["name"] == ROOT.name == "wiki-interest-trends"
    assert re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", fields["name"]) and len(fields["name"]) <= 64
    assert 1 <= len(fields["description"]) <= 1024
    assert len(fields.get("compatibility", "")) <= 500
    assert len(text.splitlines()) < 500


def test_skill_md_links_point_to_existing_files():
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert [link for link in re.findall(r"\]\(([^)#]+)\)", text) if not (ROOT / link).exists()] == []
```

Run: `.venv/bin/python -m pytest tests/unit/test_skill_md.py -q`
Очікувано: 2 failed — `FileNotFoundError: … SKILL.md`.

- [ ] **Step 2: SKILL.md**

`SKILL.md`:
````markdown
---
name: wiki-interest-trends
description: Analyses Wikipedia pageview trends across language editions to help product teams decide which topics to build and which languages or markets to launch in. Compares interest between languages or topics, tells whether growth is real and how far to trust it, finds seasonality (when to launch), ranks audiences by the user's priorities, and produces charts plus a shareable one-page PDF report. Use when the user asks about interest in a topic on Wikipedia, compares languages or markets, plans localization, chooses a course or content topic, asks about growth trends or seasonality, or wants a short data-backed report.
license: MIT
compatibility: Requires Python 3.12+ and internet access to Wikimedia APIs. Uses uv when available, otherwise creates a virtualenv on first run (about a minute).
metadata:
  version: "1.0.0"
---

# Wikipedia interest trends

You turn a product question into a small study form (`study.json`), run the engine and explain its output.
**The engine computes every number. Never calculate, estimate or invent numbers yourself, and never write your own analysis code or scrape the web for this task.**

`<skill>` below is the absolute path of this skill's folder. Give every command a 10-minute timeout: the first run prepares Python and downloads data; later runs use the cache and take seconds.

## Workflow

### 1. Find the topic
```bash
<skill>/scripts/wit resolve "<topic in the user's words>" --langs pl,cs --question "<the user's question, verbatim>" --save wiki-studies/<short-name>
```
Read the output:
- `TOPIC`: check that this is the meaning the user wants. If `other candidates` show a different plausible meaning (e.g. Mercury the planet vs the element), ask the user which one, then rerun with `--qid Q…`.
- `ARTICLES`: a language marked `no article` has no article on this topic. Tell the user. If a substitute candidate is clearly the same subject, you may add it to `substitutes` and say so; otherwise leave it, because the gap itself is a finding.
- `RELATED`: neighbouring topics with Wikidata ids. For a broad topic ("astronomy", "learning English") add 2–4 of them that exist in all requested languages to `related` and tell the user you did. For a narrow topic, only mention them.

### 2. Adjust the form
Edit `wiki-studies/<short-name>/study.json`. Keep only what the user asked for.
- The user wants to choose audiences, or gives priorities → `"priorities": {"growth": 0.4, "interest": 0.3, "reach": 0.3}` (weights follow their words).
- "last five years" → `"months": 60`; absolute numbers → `"measure": "views"`.
Field reference: [references/study-fields.md](references/study-fields.md)

### 3. Run
```bash
<skill>/scripts/wit run wiki-studies/<short-name>
```
If it prints `ERROR` and `FIX`, apply the FIX and run again. The summary has one line per series: views per month, share per million views, YoY growth and growth without spikes, months up out of 12, verdict, trust with its main reason, seasonality. Then come `RANKING`, `WARNINGS`, `FILES` and the placeholder `KEYS`.

### 4. Answer the user
Answer in the user's language, briefly:
1. The answer to the question: the verdict per language or topic, with the YoY growth figure.
2. Trust: the level (high, medium or low) and its reason. Low trust means the signal is weak; say so and do not build a recommendation on it alone.
3. The seasonal peak month and the ranking, if present.
4. At least one limitation: a Wikipedia language is not a country; pageviews show interest, not willingness to pay; substitutes and related articles are indirect measures.
5. The path to `report.pdf`.

Copy numbers exactly as printed.

### 5. Optional: your own report text
Add `"summary"` (≤ 600 characters) and `"next_steps"` (≤ 5 items) to the form and write every number as a placeholder `{key.metric}`, e.g. `{cs.growth}`, `{cs.trust}`, `{cs.peak_month}`, `{pl.rank}`. The keys and metrics are listed in the run summary. Run again. The engine rejects percentages and numbers ≥ 100 typed without placeholders.

## Follow-up requests
Edit the same `study.json` and run again; cached data makes it fast.
- Add a language: append its code to `languages`.
- Change the period: `months`.
- "Growth matters more": raise `priorities.growth`.

Start a new folder only for a new question.

## Examples
Polish vs Czech interest in intermittent fasting. Polish has no article, so the gap is reported:
```json
{"question": "Порівняй зростання інтересу до інтервального голодування в польськомовній та чеськомовній Wikipedia за останні два роки.",
 "topics": [{"label": "Інтервальне голодування", "wikidata": "Q1666254"}], "languages": ["pl", "cs"], "months": 24}
```

Growth of interest in astronomy in Ukrainian Wikipedia and how far to trust it. It is a broad topic, so a related article is added:
```json
{"question": "Чи зростає інтерес до астрономії в україномовній Wikipedia і наскільки цьому можна довіряти?",
 "topics": [{"label": "Астрономія", "wikidata": "Q333", "related": ["Q544"]}], "languages": ["uk"]}
```

Which audiences to research next for an English-learning app. This uses an indirect topic plus a ranking:
```json
{"question": "Порівняй інтерес до вивчення англійської в pl, cs, uk, tr, id: які аудиторії дослідити наступними?",
 "topics": [{"label": "Вивчення англійської", "wikidata": "Q1860", "related": ["Q490396", "Q487425", "Q130192"]}],
 "languages": ["pl", "cs", "uk", "tr", "id"], "priorities": {"growth": 0.4, "interest": 0.3, "reach": 0.3}}
```
Tell the user that "English language" articles are an indirect measure of interest in learning English.

## Troubleshooting
| message | what to do |
|---|---|
| `languages: unknown language 'polish'; did you mean 'pl'?` | use the code |
| `topics[1].wikidata: … is not a Wikidata id` | run `resolve` and copy the `Q…` id |
| `summary contains '15%'` | replace the number with a placeholder such as `{cs.growth}` |
| exit code 3 (network) | wait a minute and rerun; downloaded data is cached |
| exit code 4 (no data) | the topic has no article in any requested language: set `substitutes` or report the gap |
| exit code 5 (environment) | Python 3.12+ is missing: tell the user |

How growth, trust, seasonality and ranking are computed: [references/methodology.md](references/methodology.md). What comes next: [references/roadmap.md](references/roadmap.md).
````

Run: `.venv/bin/python -m pytest tests/unit/test_skill_md.py -q`
Очікувано: 2 passed.

- [ ] **Step 3: Прогін сценаріїв із навичкою (GREEN)**

- A: `python3 evals/run_evals.py`
- B: процедура з Task 17, крок 5, з блоком про навичку.

Очікувано: усі 7 сценаріїв PASS; результат у `evals/results/*-with-skill*.md`.

- [ ] **Step 4: Цикл «рефакторингу» SKILL.md (до 3 ітерацій)**

Для кожного FAIL прочитай `evals/workdir/<id>/answer.md` і з'ясуй причину:
- **Хибна тривога перевірки** (наприклад, слово-маркер обмеження, якого немає в списку): спершу додай у `tests/unit/test_eval_check.py` тест, який відтворює випадок і падає, потім виправ `evals/check.py`.
- **Поведінка агента** (пропустив довіру, вигадав число, не перепитав про Меркурій): додай у SKILL.md одне конкретне правило або приклад, що закриває цю лазівку.

Перезапусти лише проблемні сценарії (`--only`). Зупинись, коли все PASS, або після 3 ітерацій. Невирішені випадки задокументуй у `docs/verification.md` з причиною.

- [ ] **Step 5: Задокументувати результат**

У `docs/verification.md` заміни розділ 4 на:
````markdown
## 4. Full scenario on Claude Haiku 4.5
Seven scenarios from `evals/scenarios.json`: the three case examples (E1–E3), two follow-ups (F1 "add Slovak", F2 "growth matters more") and two traps (T1 ambiguous "Mercury", T2 eclipse spikes). An automatic checker (`evals/check.py`, itself unit-tested) verifies the form, the one-page PDF, that trust and a limitation are stated, and that every percentage in the answer exists in `findings.json`.

| run | result |
|---|---|
| baseline without the skill | [evals/results/…-baseline-no-skill.md](../evals/results/) |
| with the skill | [evals/results/…-with-skill.md](../evals/results/) |
````
і впиши у два рядки таблиці точні назви файлів результатів та кількість PASS із них. У `README.md` у розділі «How it was verified» додай рядок із підсумком прогону з навичкою (скільки сценаріїв PASS).

- [ ] **Step 6: Коміт**

```bash
git add SKILL.md tests/unit/test_skill_md.py evals/results docs/verification.md README.md
git commit -m "feat: SKILL.md for cheap models, verified on Claude Haiku 4.5 eval scenarios" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 19: Фінальна перевірка

**Files:**
- Modify: лише те, що виявить перевірка.

- [ ] **Step 1: Увесь набір тестів**

Run: `.venv/bin/python -m pytest -q && .venv/bin/python -m pytest -m live -q`
Очікувано: 0 failed, 0 errors, без попереджень у виводі.

- [ ] **Step 2: Чисте середовище**

Run: `WIT_HOME="$(mktemp -d)" scripts/wit --version`
Очікувано: створюється нове середовище з `requirements.txt`, потім `wit 1.0.0`.

- [ ] **Step 3: Навичка як тека**

Run: `git ls-files | grep -vE '^(tests/fixtures/http/|evals/results/)' | head -80`
Переконайся, що все власне лежить у теці навички, немає скомпільованих файлів, `.venv/` і `wiki-studies/` не в git.

- [ ] **Step 4: Покриття специфікації**

Пройди розділи 1–17 специфікації і для кожного знайди завдання, яке його реалізує (див. таблицю покриття нижче). Прогалини — окремим комітом із тестом.

- [ ] **Step 5: Коміт і позначка версії**

```bash
git status --short
git tag v1.0.0
```

---

## Покриття специфікації

| Розділ специфікації | Завдання |
|---|---|
| §1 Мета, межі v1 | T1–T18 |
| §2 Сценарії прийняття E1–E3, F1–F2, T1–T2 | T1 (офлайн E1–E3, F1, запобіжник), T17–T18 (Haiku, усі 7) |
| §3 Архітектура, модулі | T2–T14 |
| §4 Бланк і перевірка | T2, T15 (шаблон, довідка) |
| §5 `resolve` | T9, T14 |
| §6 `run`, періоди, статті, редиректи, файли, вижимка, коди виходу | T4, T10, T14 |
| §7 Методика: ріст, сталість, сплески, вердикт, довіра, сезонність, рейтинг | T5, T6, T7, T8 |
| §8 Тексти, плейсхолдери, запобіжник | T11, T1 (приймальний тест запобіжника) |
| §9 Графіки і PDF | T12, T13 |
| §10 API: UA, пауза, повтори, 404, кеш, бюджет, прогрес | T3, T4 |
| §11 SKILL.md | T18 |
| §12 Середовище, обгортка, код 5 | T1, T14, T19 |
| §13 Тестування (TDD, рівні, фікстури, evals, ручна звірка) | T1, T9, T10, T16, T17, T18 |
| §14 Структура | T1–T18 |
| §15 План розвитку | T15 |
| §16 Скорочення обсягу | порядок: T9 (`morelike` в `_add_related`) і T7 (сезонність) можна вимкнути без зміни інших модулів |
| §17 Відкриті питання | вирішуються перед T3 (контакт `DEFAULT_CONTACT`) і T17 (варіант A або B) |
