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


def test_overflowing_report_spills_onto_a_second_page_without_clipping(tmp_path):
    long = content(tmp_path, rows=8, text_len=700, steps=5)
    long.footer = long.footer + [("Припущення", "довгий текст " * 500 + "КІНЕЦЬ")]
    path = tmp_path / "report.pdf"
    assert render_pdf(long, path) == 2
    reader = PdfReader(str(path))
    assert len(reader.pages) == 2 and "КІНЕЦЬ" in reader.pages[1].extract_text()


def test_body_text_never_shrinks_below_7pt_and_small_print_below_5_5pt():
    smallest = min(SCALES)
    assert font_size("summary", smallest) >= 7 and font_size("steps", smallest) >= 7
    assert min(font_size(role, smallest) for role in ("table", "side", "footer")) >= 5.5


def test_build_report_writes_charts_and_pdf(tmp_path):
    study = parse_study({"question": "Порівняй інтерес", "topics": [{"label": "Т", "wikidata": "Q1"}], "languages": ["cs", "pl"]})
    results = [make_result("cs", months=PERIODS.history_months), make_result("pl", verdict="no_data", status="no_article")]
    files = build_report(tmp_path, study, PERIODS, results, [], build_texts(study, results, []))
    assert {files[k].name for k in ("report", "trend", "growth")} == {"report.pdf", "chart_trend.png", "chart_growth.png"}
    assert files["pages"] == 1 and page_text(files["report"])[0] == 1
