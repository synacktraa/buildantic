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
    description: t.Optional[str]  # 'description' or 'summary' key
    path_meta: t.Optional[EncodableInputMeta[PathEncodingStyle]]
    query_meta: t.Optional[EncodableInputMeta[QueryEncodingStyle]]
    header_meta: t.Optional[InputMeta]
    cookie_meta: t.Optional[InputMeta]
    body_meta: t.Optional[InputMeta]
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
    queries: t.Optional[t.Dict[str, t.Any]] = None
    encoded_query: t.Optional[str] = None
    headers: t.Optional[t.Dict[str, t.Any]] = None
    cookies: t.Optional[t.Dict[str, t.Any]] = None
    body: t.Optional[t.Dict[str, t.Any]] = None

    @property
    def path_with_query(self) -> str:
        """Return path with query"""
        if not self.encoded_query:
            return self.path
        return f"{self.path}?{self.encoded_query}"
