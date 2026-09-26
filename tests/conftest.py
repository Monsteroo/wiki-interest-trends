import pytest

from helpers import FakeTransport


@pytest.fixture
def fake_transport():
    return FakeTransport()


@pytest.fixture
def client(tmp_path, fake_transport):
    from witlib.api import ApiClient

    return ApiClient(transport=fake_transport, cache_dir=tmp_path / "cache", sleep=lambda s: None)
