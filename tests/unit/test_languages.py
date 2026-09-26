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
