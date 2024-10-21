from __future__ import annotations

from urllib.parse import quote, unquote

import pytest

from buildantic.descriptor.openapi.utils import encode_query_parameter


@pytest.mark.parametrize(
    "name, value, style, explode, expected",
    [
        # Form style
        ("id", 5, "form", True, "id=5"),
        ("id", 5, "form", False, "id=5"),
        ("id", [3, 4, 5], "form", True, "id=3&id=4&id=5"),
        ("id", [3, 4, 5], "form", False, "id=3,4,5"),
        ("id", {"role": "admin", "firstName": "Alex"}, "form", True, "role=admin&firstName=Alex"),
        (
            "id",
            {"role": "admin", "firstName": "Alex"},
            "form",
            False,
            "id=role,admin,firstName,Alex",
        ),
        # Space Delimited style
        ("id", [3, 4, 5], "spaceDelimited", True, "id=3&id=4&id=5"),
        ("id", [3, 4, 5], "spaceDelimited", False, "id=3%204%205"),
        # Pipe Delimited style
        ("id", [3, 4, 5], "pipeDelimited", True, "id=3&id=4&id=5"),
        ("id", [3, 4, 5], "pipeDelimited", False, "id=3|4|5"),
        # Deep Object style
        (
            "id",
            {"role": "admin", "firstName": "Alex"},
            "deepObject",
            True,
            "id[role]=admin&id[firstName]=Alex",
        ),
    ],
)
def test_encode_query_parameter(name, value, style, explode, expected):
    result = encode_query_parameter(name, value, style, explode)
    assert result == expected


def test_default_values():
    assert encode_query_parameter("id", 5) == "id=5"
    assert encode_query_parameter("id", [1, 2, 3]) == "id=1&id=2&id=3"
    assert encode_query_parameter("id", {"a": 1, "b": 2}) == "a=1&b=2"


def test_unsupported_style():
    with pytest.raises(ValueError):
        encode_query_parameter("id", 5, "unsupported_style")


def test_invalid_combinations():
    with pytest.raises(ValueError):
        encode_query_parameter("id", 5, "spaceDelimited", True)
    with pytest.raises(ValueError):
        encode_query_parameter("id", 5, "pipeDelimited", False)
    with pytest.raises(ValueError):
        encode_query_parameter("id", [1, 2], "deepObject", True)
    with pytest.raises(ValueError):
        encode_query_parameter("id", {"a": 1}, "deepObject", False)


@pytest.mark.parametrize("style", [None, "form", "spaceDelimited", "pipeDelimited", "deepObject"])
@pytest.mark.parametrize("explode", [None, True, False])
def test_all_valid_combinations(style, explode):
    if style == "form":
        encode_query_parameter("id", 5, style, explode)
    if style != "deepObject":
        encode_query_parameter("id", [1, 2, 3], style, explode)
    if style in [None, "form", "deepObject"]:
        if style == "deepObject" and explode is False:
            with pytest.raises(ValueError):
                encode_query_parameter("id", {"a": 1, "b": 2}, style, explode)
        else:
            encode_query_parameter("id", {"a": 1, "b": 2}, style, explode)


def test_special_characters():
    assert encode_query_parameter("q", "hello world") == "q=hello%20world"
    assert encode_query_parameter("q", "a+b=c&d") == "q=a%2Bb%3Dc%26d"


def test_unicode_characters():
    assert encode_query_parameter("q", "こんにちは") == quote("q=こんにちは", safe="=")
    assert encode_query_parameter("q", ["🌟", "🌈"]) == quote("q=🌟&q=🌈", safe="=&")


def test_empty_values():
    assert encode_query_parameter("id", "") == "id="
    assert encode_query_parameter("id", []) == ""
    assert encode_query_parameter("id", {}) == ""


def test_none_value():
    assert encode_query_parameter("id", None) == "id=None"


def test_boolean_values():
    assert encode_query_parameter("flag", True) == "flag=True"
    assert encode_query_parameter("flag", False) == "flag=False"


def test_nested_structures():
    nested = {"a": [1, 2], "b": {"c": 3}}
    assert unquote(encode_query_parameter("id", nested, "form", True)) == "a=[1, 2]&b={'c': 3}"
    assert unquote(encode_query_parameter("id", nested, "form", False)) == "id=a,[1, 2],b,{'c': 3}"


def test_large_inputs():
    large_list = list(range(1000))
    large_dict = {f"key{i}": i for i in range(1000)}

    # These should not raise exceptions
    encode_query_parameter("id", large_list, "form", True)
    encode_query_parameter("id", large_dict, "form", True)
