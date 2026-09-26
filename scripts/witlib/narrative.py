"""Report texts: localisation (uk/en), number formats, placeholders, the number guard and template texts."""
from __future__ import annotations

import re

from .languages import language_name

METRICS = ("growth", "growth_clean", "views", "share", "months_up", "trust", "verdict", "peak_month", "rank", "title")
PLACEHOLDER_RE = re.compile(r"\{([^{}]+)\}")
PERCENT_RE = re.compile(r"\d+(?:[.,]\d+)?\s*%")
NUMBER_RE = re.compile(r"\d{1,3}(?:[   ,.]\d{3})+|\d+")

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
