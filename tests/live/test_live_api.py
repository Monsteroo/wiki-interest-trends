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
