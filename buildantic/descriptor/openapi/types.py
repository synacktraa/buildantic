from __future__ import annotations

import typing as t

from pydantic import BaseModel

Method = t.Literal["get", "post", "put", "delete", "patch", "head", "options"]
"""Supported request methods."""

PathEncodingStyle = t.Literal["simple", "label", "matrix"]
"""Path encoding style. Default to `simple`."""

QueryEncodingStyle = t.Literal["form", "pipeDelimited", "spaceDelimited", "deepObject"]
"""
Query encoding style. Default to `form`.
`pipeDelimited` and `spaceDelimited` doesn't support primitive and object types.
`deepObject` only support object type when explode is True.
"""

EncodingStyleT = t.TypeVar("EncodingStyleT")


class EncodingMeta(BaseModel, t.Generic[EncodingStyleT]):
    style: EncodingStyleT
    explode: bool


class InputMeta(BaseModel):
    schema_: t.Dict[str, t.Any]


class EncodableInputMeta(InputMeta, t.Generic[EncodingStyleT]):
    encodings: t.Dict[str, EncodingMeta[EncodingStyleT]] = {}


class Operation(BaseModel):
    id: str  # 'operationId' key
    path: str
    method: Method
    description: str | None  # 'description' or 'summary' key
    path_meta: EncodableInputMeta[PathEncodingStyle] | None
    query_meta: EncodableInputMeta[QueryEncodingStyle] | None
    header_meta: InputMeta | None
    cookie_meta: InputMeta | None
    body_meta: InputMeta | None
    body_required: bool = False


class RequestModel(BaseModel):
    """
    Request Model returned by `OperationDescriptor` after validation.

    :param path: Formatted and encoded path.
    :param queries: Raw query mapping.
    :param encoded_query: Formatted and encoded query.
    :param headers: Raw header mapping.
    :param cookies: Raw cookie mapping.
    :param body: Raw body mapping.
    """

    path: str
    method: Method
    queries: t.Dict[str, t.Any] | None = None
    encoded_query: str | None = None
    headers: t.Dict[str, t.Any] | None = None
    cookies: t.Dict[str, t.Any] | None = None
    body: t.Dict[str, t.Any] | None = None

    @property
    def path_with_query(self) -> str:
        """Return path with query"""
        if not self.encoded_query:
            return self.path
        return f"{self.path}?{self.encoded_query}"
