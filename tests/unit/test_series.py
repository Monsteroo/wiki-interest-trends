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
