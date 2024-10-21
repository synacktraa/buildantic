from __future__ import annotations

from typing import Any, Dict

import pytest

from buildantic.descriptor.openapi import OperationDescriptor
from buildantic.descriptor.openapi.types import (
    EncodingMeta,
    Operation,
    RequestModel,
)
from buildantic.descriptor.openapi.utils import format_path, format_query


def create_operation(
    path: str,
    method: str,
    path_meta: Dict[str, Any] | None = None,
    query_meta: Dict[str, Any] | None = None,
    header_meta: Dict[str, Any] | None = None,
    cookie_meta: Dict[str, Any] | None = None,
    body_meta: Dict[str, Any] | None = None,
    body_required: bool = False,
):
    return Operation(
        id="test_operation",
        path=path,
        method=method,
        description="Test operation",
        path_meta={"schema_": path_meta} if path_meta else None,
        query_meta={"schema_": query_meta} if query_meta else None,
        header_meta={"schema_": header_meta} if header_meta else None,
        cookie_meta={"schema_": cookie_meta} if cookie_meta else None,
        body_meta={"schema_": body_meta} if body_meta else None,
        body_required=body_required,
    )


# Test OperationDescriptor


def test_operation_descriptor_schema_generation_all_params():
    operation = create_operation(
        path="/users/{userId}",
        method="post",
        path_meta={"properties": {"userId": {"type": "integer"}}},
        query_meta={"properties": {"filter": {"type": "string"}}},
        header_meta={"properties": {"X-API-Key": {"type": "string"}}},
        cookie_meta={"properties": {"session": {"type": "string"}}},
        body_meta={"properties": {"name": {"type": "string"}, "age": {"type": "integer"}}},
        body_required=True,
    )
    descriptor = OperationDescriptor(operation)

    assert descriptor.schema == {
        "type": "object",
        "properties": {
            "userId": {"type": "integer"},
            "filter": {"type": "string"},
            "X-API-Key": {"type": "string"},
            "session": {"type": "string"},
            "requestBody": {
                "type": "object",
                "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
            },
        },
        "required": ["requestBody"],
        "description": "Test operation",
    }


def test_operation_descriptor_validation_all_params():
    operation = create_operation(
        path="/users/{userId}",
        method="post",
        path_meta={"properties": {"userId": {"type": "integer"}}},
        query_meta={"properties": {"filter": {"type": "string"}}},
        header_meta={"properties": {"X-API-Key": {"type": "string"}}},
        cookie_meta={"properties": {"session": {"type": "string"}}},
        body_meta={"properties": {"name": {"type": "string"}, "age": {"type": "integer"}}},
        body_required=True,
    )
    descriptor = OperationDescriptor(operation)

    input_data = {
        "userId": 123,
        "filter": "active",
        "X-API-Key": "secret-key",
        "session": "user-session",
        "requestBody": {"name": "John Doe", "age": 30},
    }

    request_model = descriptor.validate_python(input_data)
    assert isinstance(request_model, RequestModel)
    assert request_model.path == "/users/123"
    assert request_model.queries == {"filter": "active"}
    assert request_model.headers == {"X-API-Key": "secret-key"}
    assert request_model.cookies == {"session": "user-session"}
    assert request_model.body == {"name": "John Doe", "age": 30}


def test_operation_descriptor_validation_missing_required_body():
    operation = create_operation(
        path="/users",
        method="post",
        body_meta={"properties": {"name": {"type": "string"}}},
        body_required=True,
    )
    descriptor = OperationDescriptor(operation)

    from jsonschema.exceptions import ValidationError

    with pytest.raises(
        ValidationError
    ):  # Replace with the specific exception your validator raises
        descriptor.validate_python({})


def test_operation_descriptor_validation_json():
    operation = create_operation(
        path="/users/{userId}",
        method="get",
        path_meta={"properties": {"userId": {"type": "integer"}}},
        query_meta={"properties": {"filter": {"type": "string"}}},
    )
    descriptor = OperationDescriptor(operation)

    json_data = '{"userId": 123, "filter": "active"}'
    request_model = descriptor.validate_json(json_data)
    assert request_model.path == "/users/123"
    assert request_model.queries == {"filter": "active"}


# Test format_path


def test_format_path_simple():
    path = "/users/{userId}/posts/{postId}"
    params = {"userId": 123, "postId": 456}
    encodings = {
        "userId": EncodingMeta(style="simple", explode=False),
        "postId": EncodingMeta(style="simple", explode=False),
    }

    formatted_path = format_path(path, params, encodings)
    assert formatted_path == "/users/123/posts/456"


def test_format_path_label():
    path = "/users/{userId}/posts/{postId}"
    params = {"userId": 123, "postId": 456}
    encodings = {
        "userId": EncodingMeta(style="label", explode=False),
        "postId": EncodingMeta(style="label", explode=False),
    }

    formatted_path = format_path(path, params, encodings)
    assert formatted_path == "/users/.123/posts/.456"


def test_format_path_matrix():
    path = "/users/{userId}/posts/{postId}"
    params = {"userId": 123, "postId": 456}
    encodings = {
        "userId": EncodingMeta(style="matrix", explode=False),
        "postId": EncodingMeta(style="matrix", explode=False),
    }

    formatted_path = format_path(path, params, encodings)
    assert formatted_path == "/users/;userId=123/posts/;postId=456"


def test_format_path_mixed_styles():
    path = "/users/{userId}/posts/{postId}"
    params = {"userId": 123, "postId": 456}
    encodings = {
        "userId": EncodingMeta(style="simple", explode=False),
        "postId": EncodingMeta(style="label", explode=False),
    }

    formatted_path = format_path(path, params, encodings)
    assert formatted_path == "/users/123/posts/.456"


def test_format_path_array():
    path = "/users/{userIds}"
    params = {"userIds": [1, 2, 3]}
    encodings = {"userIds": EncodingMeta(style="simple", explode=False)}

    formatted_path = format_path(path, params, encodings)
    assert formatted_path == "/users/1,2,3"


def test_format_path_object():
    path = "/users/{user}"
    params = {"user": {"id": 123, "name": "John"}}
    encodings = {"user": EncodingMeta(style="simple", explode=True)}

    formatted_path = format_path(path, params, encodings)
    assert formatted_path == "/users/id=123,name=John"


# Test format_query


def test_format_query_form_style():
    params = {"filter": "active", "sort": "name", "page": 1}
    encodings = {
        "filter": EncodingMeta(style="form", explode=True),
        "sort": EncodingMeta(style="form", explode=True),
        "page": EncodingMeta(style="form", explode=True),
    }

    formatted_query = format_query(params, encodings)
    assert "filter=active" in formatted_query
    assert "sort=name" in formatted_query
    assert "page=1" in formatted_query


def test_format_query_space_delimited_array():
    params = {"tags": ["python", "testing", "pytest"]}
    encodings = {"tags": EncodingMeta(style="spaceDelimited", explode=False)}

    formatted_query = format_query(params, encodings)
    assert formatted_query == "tags=python%20testing%20pytest"


def test_format_query_pipe_delimited_array():
    params = {"tags": ["python", "testing", "pytest"]}
    encodings = {"tags": EncodingMeta(style="pipeDelimited", explode=False)}

    formatted_query = format_query(params, encodings)
    assert formatted_query == "tags=python|testing|pytest"


def test_format_query_deep_object():
    params = {"filter": {"name": "John Doe", "age": 30}}
    encodings = {"filter": EncodingMeta(style="deepObject", explode=True)}

    formatted_query = format_query(params, encodings)
    assert "filter[name]=John%20Doe" in formatted_query
    assert "filter[age]=30" in formatted_query


def test_format_query_mixed_styles():
    params = {
        "filter": "active",
        "tags": ["python", "testing"],
        "sort": {"field": "name", "order": "asc"},
    }
    encodings = {
        "filter": EncodingMeta(style="form", explode=True),
        "tags": EncodingMeta(style="pipeDelimited", explode=False),
        "sort": EncodingMeta(style="deepObject", explode=True),
    }

    formatted_query = format_query(params, encodings)
    assert "filter=active" in formatted_query
    assert "tags=python|testing" in formatted_query
    assert "sort[field]=name" in formatted_query
    assert "sort[order]=asc" in formatted_query


def test_format_query_empty_params():
    params = {}
    encodings = {}

    formatted_query = format_query(params, encodings)
    assert formatted_query == ""


def test_format_query_special_characters():
    params = {"search": "test&query+with spaces"}
    encodings = {"search": EncodingMeta(style="form", explode=True)}

    formatted_query = format_query(params, encodings)
    assert formatted_query == "search=test%26query%2Bwith%20spaces"


# Edge cases and error handling


def test_operation_descriptor_empty_operation():
    operation = create_operation(path="/", method="get")
    descriptor = OperationDescriptor(operation)

    assert descriptor.schema == {
        "type": "object",
        "properties": {},
        "description": "Test operation",
    }


def test_operation_descriptor_nested_objects():
    operation = create_operation(
        path="/",
        method="post",
        body_meta={
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "address": {
                            "type": "object",
                            "properties": {
                                "street": {"type": "string"},
                                "city": {"type": "string"},
                            },
                        },
                    },
                }
            }
        },
    )
    descriptor = OperationDescriptor(operation)

    input_data = {
        "requestBody": {
            "user": {"name": "John Doe", "address": {"street": "123 Main St", "city": "Anytown"}}
        }
    }

    request_model = descriptor.validate_python(input_data)
    assert request_model.body == {
        "user": {"name": "John Doe", "address": {"street": "123 Main St", "city": "Anytown"}}
    }


def test_format_path_missing_parameter():
    path = "/users/{userId}/posts/{postId}"
    params = {"userId": 123}
    encodings = {
        "userId": EncodingMeta(style="simple", explode=False),
        "postId": EncodingMeta(style="simple", explode=False),
    }

    with pytest.raises(KeyError):
        format_path(path, params, encodings)


def test_format_query_unsupported_style():
    params = {"tags": ["python", "testing"]}
    encodings = {"tags": EncodingMeta(style="unsupportedStyle", explode=False)}

    with pytest.raises(ValueError):
        format_query(params, encodings)


# Add more tests as needed to cover additional edge cases and scenarios
