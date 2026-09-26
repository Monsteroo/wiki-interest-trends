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
    pages = render_pdf(compose(study, periods, results, ranking, texts, trend, growth), report)
    return {"report": report, "trend": trend, "growth": growth, "pages": pages}
