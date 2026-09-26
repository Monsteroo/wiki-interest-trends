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
