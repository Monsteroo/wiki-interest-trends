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
