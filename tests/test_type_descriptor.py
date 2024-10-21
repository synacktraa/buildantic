from __future__ import annotations

import typing as t
from enum import Enum

import pytest
from pydantic import BaseModel, Field, ValidationError
from pydantic.functional_validators import AfterValidator
from typing_extensions import TypedDict

from buildantic.descriptor.python import TypeDescriptor


def test_type_descriptor_init():
    descriptor = TypeDescriptor(int)
    assert descriptor.ref is int
    assert descriptor.id == "int"


def test_type_descriptor_init_with_callable():
    def custom_type():
        pass

    descriptor = TypeDescriptor(custom_type)
    assert descriptor.ref is custom_type
    assert descriptor.id == "custom_type"


def test_type_descriptor_schema():
    descriptor = TypeDescriptor(int)
    schema = descriptor.schema
    assert isinstance(schema, dict)
    assert "type" in schema


def test_type_descriptor_validate_python_success():
    descriptor = TypeDescriptor(int)
    result = descriptor.validate_python(42)
    assert result == 42


def test_type_descriptor_validate_python_failure():
    descriptor = TypeDescriptor(int)
    with pytest.raises(ValidationError):
        descriptor.validate_python("not an int")


def test_type_descriptor_validate_json_success():
    descriptor = TypeDescriptor(int)
    result = descriptor.validate_json("42")
    assert result == 42


def test_type_descriptor_validate_json_failure():
    descriptor = TypeDescriptor(int)
    with pytest.raises(ValidationError):
        descriptor.validate_json('"not an int"')


# Test with a more complex type


class ComplexTuple(t.NamedTuple):
    name: str
    age: int


class ComplexDict(TypedDict):
    value: ComplexTuple


def test_complex_type_descriptor():
    descriptor = TypeDescriptor(ComplexDict)

    # Test schema
    schema = descriptor.schema
    assert "properties" in schema
    assert "value" in schema["properties"]

    # Test validation
    valid_data = ComplexDict(value=ComplexTuple("Alice", 30))
    invalid_data = ComplexDict(value="not a ComplexTuple")

    assert isinstance(descriptor.validate_python(valid_data), dict)
    with pytest.raises(ValidationError):
        descriptor.validate_python(invalid_data)


# Test edge cases


def test_type_descriptor_with_union():
    descriptor = TypeDescriptor(t.Union[int, str])
    assert descriptor.validate_python(42) == 42
    assert descriptor.validate_python("hello") == "hello"
    with pytest.raises(ValidationError):
        descriptor.validate_python([])


def test_type_descriptor_with_optional():
    descriptor = TypeDescriptor(t.Optional[int])
    assert descriptor.validate_python(42) == 42
    assert descriptor.validate_python(None) is None
    with pytest.raises(ValidationError):
        descriptor.validate_python("not an int")


def test_type_descriptor_with_list():
    descriptor = TypeDescriptor(t.List[int])
    assert descriptor.validate_python([1, 2, 3]) == [1, 2, 3]
    with pytest.raises(ValidationError):
        descriptor.validate_python([1, "f", 3])


def test_type_descriptor_with_dict():
    descriptor = TypeDescriptor(t.Dict[str, int])
    assert descriptor.validate_python({"a": 1, "b": 2}) == {"a": 1, "b": 2}
    with pytest.raises(ValidationError):
        descriptor.validate_python({"a": 1, "b": "two"})


def test_type_descriptor_with_nested_types():
    NestedType = t.List[t.Dict[str, t.Union[int, str]]]
    descriptor = TypeDescriptor(NestedType)
    valid_data = [{"a": 1, "b": "hello"}, {"c": 2, "d": "world"}]
    assert descriptor.validate_python(valid_data) == valid_data
    with pytest.raises(ValidationError):
        descriptor.validate_python([{"a": 1, "b": []}])


# Test error messages


def test_validation_error_messages():
    descriptor = TypeDescriptor(t.Dict[str, int])
    with pytest.raises(ValidationError) as exc_info:
        descriptor.validate_python({"a": 1, "b": "not an int"})
    assert "b" in str(exc_info.value)
    assert "int" in str(exc_info.value)


# Test with custom validation logic


def test_type_descriptor_with_custom_validation():
    def check_even(v: int):
        assert v % 2 == 0
        return v

    descriptor = TypeDescriptor[int](t.Annotated[int, AfterValidator(check_even)])
    assert descriptor.validate_python(2) == 2
    assert descriptor.validate_python(4) == 4
    with pytest.raises(ValidationError):
        descriptor.validate_python(3)
    with pytest.raises(ValidationError):
        descriptor.validate_python("two")


# Test performance with large data


def test_type_descriptor_performance_large_list():
    descriptor = TypeDescriptor(t.List[int])
    large_list = list(range(10000))
    result = descriptor.validate_python(large_list)
    assert len(result) == 10000
    assert result == large_list


def test_type_descriptor_performance_large_nested_dict():
    NestedDict = t.Dict[str, t.Dict[str, int]]
    descriptor = TypeDescriptor(NestedDict)
    large_dict = {f"key{i}": {"nested": i} for i in range(1000)}
    result = descriptor.validate_python(large_dict)
    assert len(result) == 1000
    assert result == large_dict


# Test with all schema formats


def test_all_schema_formats():
    class TestType(TypedDict):
        name: str
        age: int

    descriptor = TypeDescriptor(TestType)

    base_schema = descriptor.schema
    openai_schema = descriptor.openai_schema
    anthropic_schema = descriptor.anthropic_schema
    gemini_schema = descriptor.gemini_schema

    assert all(
        isinstance(schema, dict)
        for schema in [base_schema, openai_schema, anthropic_schema, gemini_schema]
    )
    assert all("parameters" in schema for schema in (openai_schema, gemini_schema))
    assert "input_schema" in anthropic_schema
    assert "properties" in base_schema


# Test with Enum types


def test_enum_type():
    class Color(Enum):
        RED = "red"
        GREEN = "green"
        BLUE = "blue"

    descriptor = TypeDescriptor(Color)
    schema = descriptor.schema

    assert "enum" in schema
    assert set(schema["enum"]) == {"red", "green", "blue"}

    assert descriptor.validate_python(Color.RED) == Color.RED
    with pytest.raises(ValidationError):
        descriptor.validate_python("yellow")


# Test with Literal types


def test_literal_type():
    from typing_extensions import Literal

    descriptor = TypeDescriptor(Literal["foo", "bar", 42])
    schema = descriptor.schema

    assert "enum" in schema
    assert set(schema["enum"]) == {"foo", "bar", 42}

    assert descriptor.validate_python("foo") == "foo"
    assert descriptor.validate_python(42) == 42
    with pytest.raises(ValidationError):
        descriptor.validate_python("baz")


# Test with generic types


T = t.TypeVar("T")


class GenericType(BaseModel, t.Generic[T]):
    value: T


def test_generic_type():
    IntGenericType = GenericType[int]
    descriptor = TypeDescriptor(IntGenericType)

    schema = descriptor.schema
    assert "properties" in schema
    assert "value" in schema["properties"]
    assert schema["properties"]["value"]["type"] == "integer"

    valid_data = IntGenericType(value=42)
    assert isinstance(descriptor.validate_python(valid_data), GenericType)
    with pytest.raises(ValidationError):
        descriptor.validate_python(IntGenericType(value="not an int"))


# Test with complex JSON schemas


def test_complex_json_schema():
    class ComplexType(TypedDict):
        simple_field: str
        list_field: t.List[int]
        dict_field: t.Dict[str, int | str]
        nested_field: t.List[dict] | None

    descriptor = TypeDescriptor(ComplexType)
    schema = descriptor.schema

    assert "properties" in schema
    assert set(schema["properties"].keys()) == {
        "simple_field",
        "list_field",
        "dict_field",
        "nested_field",
    }

    assert schema["properties"]["simple_field"]["type"] == "string"
    assert schema["properties"]["list_field"]["type"] == "array"
    assert schema["properties"]["list_field"]["items"]["type"] == "integer"
    assert schema["properties"]["dict_field"]["type"] == "object"
    assert "anyOf" in schema["properties"]["dict_field"]["additionalProperties"]
    assert "anyOf" in schema["properties"]["nested_field"]
    for inner_schema in schema["properties"]["nested_field"]["anyOf"]:
        assert "type" in inner_schema
        assert inner_schema["type"] in ("array", "null")

    valid_data = ComplexType(
        simple_field="test",
        list_field=[1, 2, 3],
        dict_field={"a": 1, "b": "test"},
        nested_field=[{"x": 1, "y": "test"}, {"z": True}],
    )
    assert isinstance(descriptor.validate_python(valid_data), dict)


# Test error handling and custom error messages


def test_custom_error_messages():
    class CustomErrorType(BaseModel):
        value: int = Field(..., ge=0, le=100, description="Must be between 0 and 100")

    descriptor = TypeDescriptor(CustomErrorType)

    with pytest.raises(ValidationError) as exc_info:
        descriptor.validate_python(CustomErrorType(value=101))

    error_message = str(exc_info.value)
    assert "0" in error_message


def test_fc_serialization_and_validation_of_simple_type():
    descriptor = TypeDescriptor[t.List[str]](
        t.Annotated[t.List[str], Field(description="list of string", alias="strings")]
    )
    oa_schema = descriptor.openai_schema

    # Name and description are extracted from Field info.
    assert oa_schema["name"] == "strings"
    assert oa_schema["description"] == "list of string"

    # If descripted type is not object, then it is transformed into one with `input` being the property key
    assert "input" in oa_schema["parameters"]["properties"]

    # Both will work, as in function calling schema the input is added as a property key
    assert descriptor.validate_python(obj={"input": ["name", "age", "role"]}) == [
        "name",
        "age",
        "role",
    ]
    assert descriptor.validate_python(obj=["name", "age", "role"]) == ["name", "age", "role"]

    assert descriptor.validate_json(data='{"input": ["name", "age", "role"]}') == [
        "name",
        "age",
        "role",
    ]
    assert descriptor.validate_json(data='["name", "age", "role"]') == ["name", "age", "role"]
