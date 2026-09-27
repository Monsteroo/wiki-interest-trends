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
WRAPPER = Path(__file__).resolve().parents[1] / "wit"


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
    run.add_argument("--as-of", type=date.fromisoformat, help="analyse as of this date (YYYY-MM-DD) for a reproducible report")
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
        print(f"NEXT      add substitutes/related if needed, then: {WRAPPER} run {folder}", file=out)
    else:
        print("FORM      " + json.dumps(form, ensure_ascii=False), file=out)
        print(f"NEXT      save it as <folder>/study.json (or rerun with --save <folder>), then: {WRAPPER} run <folder>", file=out)
    return 0


def _run(args, client: ApiClient, out: TextIO) -> int:
    study, folder = load_study(args.path)
    as_of = args.as_of or datetime.now(timezone.utc).date()
    periods = compute_periods(as_of, study.months)
    inputs, warnings = collect_inputs(client, study, periods)
    warnings = study.warnings + warnings
    results = [analyze(inp, periods, study.measure) for inp in inputs]
    ranking = rank_series(results, study.priorities)
    texts = build_texts(study, results, ranking, periods)
    if all(r.verdict == "no_data" for r in results):
        for line in _summary(study, periods, results, ranking, warnings, None, texts):
            print(line, file=out)
        print("ERROR: no data for any series\nFIX: set substitutes for languages without an article, "
              "or tell the user the topic has no coverage there", file=out)
        return 4
    files = build_report(folder, study, periods, results, ranking, texts)
    findings = {"meta": {"version": __version__, "as_of": as_of.isoformat(),
                         "analysis": [periods.analysis_months[0], periods.analysis_months[-1]],
                         "history": [periods.history_months[0], periods.history_months[-1]], "measure": study.measure,
                         "requests": client.request_count, "cache_hits": client.cache_hits,
                         "agent_text": texts["agent_text"], "report_pages": files["pages"]},
                "series": [asdict(r) for r in results], "ranking": ranking, "warnings": warnings,
                "placeholders": texts["values"]}
    (folder / "findings.json").write_text(json.dumps(findings, ensure_ascii=False, indent=1), encoding="utf-8")
    for line in _summary(study, periods, results, ranking, warnings, folder, texts, pages=files["pages"]):
        print(line, file=out)
    return 0


def _summary(study, periods, results, ranking, warnings, folder, texts, pages: int = 1) -> list[str]:
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
        season = (f"peak {MONTHS_EN[s['peak_month'] - 1]} {fmt_pct(s['uplift'])} ({s['peak_years']}/{s['cycles']} years)"
                  if s["status"] == "stable_peak" else SEASON[s["status"]])
        window_note = ""
        if m.get("window_growth") is not None:
            years = len(months) // 12
            window_note = f" · {years}y avg {fmt_pct(m['window_growth'])}/yr"
        line = (f"  {r.key:<5} {r.title}{' [substitute]' if r.substitute else ''} · {m['views']}/month · "
                f"{m['share']:.2f} per M · YoY {fmt_pct(m['growth'])} (without spikes {fmt_pct(m['growth_clean'])}) · "
                f"up {m['months_up']}/12{window_note} · {r.verdict} · trust {r.trust}{why} · season: {season}")
        if r.spikes:
            top = sorted(r.spikes, key=lambda sp: sp["views"], reverse=True)
            dates = ", ".join(sp["date"] for sp in top[:3])
            extra = f" (+{len(top) - 3} more)" if len(top) > 3 else ""
            line += f" · spikes: {dates}{extra}"
        lines.append(line)
    if ranking:
        lines.append("RANKING  " + " > ".join(f"{row['position']}. {row['key']} ({row['score']:.2f})" for row in ranking if row["position"]))
    joined = "; ".join(warnings)
    lines.append("WARNINGS " + ((joined[:297] + "...") if len(joined) > 300 else joined or "none"))
    if folder is not None:
        note = f" — {pages} pages: the content did not fit on one page" if pages > 1 else ""
        lines.append(f"FILES    {Path(folder) / 'report.pdf'}{note} (+ findings.json, chart_trend.png, chart_growth.png)")
    keys = sorted({k.rsplit('.', 1)[0] for k in texts["values"]})
    lines.append(f"KEYS     {', '.join(keys)} · METRICS {' '.join(METRICS)}")
    if texts["agent_text"]:
        lines.append("NEXT     report updated with your summary/next_steps")
    else:
        lines.append("NEXT     answer: verdict, growth, trust + reason, spikes if listed, one limitation, report path; "
                     "copy numbers exactly. Optional: add summary/next_steps with {key.metric} placeholders and run again")
    return lines
