from __future__ import annotations

from typing import Any

import pytest

from buildantic.descriptor.openapi.utils import encode_path_parameter


@pytest.mark.parametrize(
    "name, value, style, explode, expected",
    [
        # Primitive values
        ("id", 5, "simple", False, "5"),
        ("id", 5, "label", False, ".5"),
        ("id", 5, "matrix", False, ";id=5"),
        ("id", "test", "simple", False, "test"),
        ("id", "test", "label", False, ".test"),
        ("id", "test", "matrix", False, ";id=test"),
        # Arrays
        ("id", [3, 4, 5], "simple", False, "3,4,5"),
        ("id", [3, 4, 5], "simple", True, "3,4,5"),
        ("id", [3, 4, 5], "label", False, ".3,4,5"),
        ("id", [3, 4, 5], "label", True, ".3.4.5"),
        ("id", [3, 4, 5], "matrix", False, ";id=3,4,5"),
        ("id", [3, 4, 5], "matrix", True, ";id=3;id=4;id=5"),
        # Objects
        (
            "id",
            {"role": "admin", "firstName": "Alex"},
            "simple",
            False,
            "role,admin,firstName,Alex",
        ),
        ("id", {"role": "admin", "firstName": "Alex"}, "simple", True, "role=admin,firstName=Alex"),
        (
            "id",
            {"role": "admin", "firstName": "Alex"},
            "label",
            False,
            ".role,admin,firstName,Alex",
        ),
        ("id", {"role": "admin", "firstName": "Alex"}, "label", True, ".role=admin.firstName=Alex"),
        (
            "id",
            {"role": "admin", "firstName": "Alex"},
            "matrix",
            False,
            ";id=role,admin,firstName,Alex",
        ),
        (
            "id",
            {"role": "admin", "firstName": "Alex"},
            "matrix",
            True,
            ";role=admin;firstName=Alex",
        ),
        # Edge cases
        ("id", [], "simple", False, ""),
        ("id", {}, "simple", False, ""),
        ("id", None, "simple", False, "None"),
        ("id", True, "simple", False, "True"),
        ("id", False, "simple", False, "False"),
        ("id", 0, "simple", False, "0"),
        ("id", "", "simple", False, ""),
        ("id", " ", "simple", False, " "),
        # Special characters
        ("id", "hello world", "simple", False, "hello world"),
        ("id", "hello/world", "simple", False, "hello/world"),
        ("id", "hello?world", "simple", False, "hello?world"),
        # Mixed types in arrays
        ("id", [1, "two", 3.0], "simple", False, "1,two,3.0"),
        # Nested structures
        ("id", {"a": [1, 2], "b": {"c": 3}}, "simple", False, 'a,[1,2],b,{"c":3}'),
        ("id", {"a": [1, 2], "b": {"c": 3}}, "simple", True, 'a=[1,2],b={"c":3}'),
    ],
)
def test_encode_path_parameter(name: str, value: Any, style: str, explode: bool, expected: str):
    assert encode_path_parameter(name, value, style, explode) == expected


def test_unsupported_style():
    with pytest.raises(ValueError):
        encode_path_parameter("id", 5, "unsupported_style")


def test_default_values():
    assert encode_path_parameter("id", 5) == "5"
    assert encode_path_parameter("id", [1, 2, 3]) == "1,2,3"
    assert encode_path_parameter("id", {"a": 1, "b": 2}) == "a,1,b,2"


@pytest.mark.parametrize("style", [None, "simple", "label", "matrix"])
@pytest.mark.parametrize("explode", [None, True, False])
def test_all_combinations(style, explode):
    # Test that the function doesn't raise exceptions for all valid combinations
    encode_path_parameter("id", 5, style, explode)
    encode_path_parameter("id", [1, 2, 3], style, explode)
    encode_path_parameter("id", {"a": 1, "b": 2}, style, explode)


# Test with very large inputs
def test_large_inputs():
    large_list = list(range(1000))
    large_dict = {f"key{i}": i for i in range(1000)}

    # These should not raise exceptions
    encode_path_parameter("id", large_list, "simple", False)
    encode_path_parameter("id", large_dict, "simple", False)


# Test with unicode characters
def test_unicode():
    assert encode_path_parameter("id", "こんにちは", "simple", False) == "こんにちは"
    assert encode_path_parameter("id", ["🌟", "🌈"], "simple", False) == "🌟,🌈"
    assert encode_path_parameter("id", {"🔑": "🗝️"}, "simple", True) == "🔑=🗝️"
