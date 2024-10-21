from __future__ import annotations

import typing as t
from collections import defaultdict

from ...validator import SchemaValidator
from ..base import BaseDescriptor
from .types import EncodableInputMeta, InputMeta, Operation, RequestModel
from .utils import format_path, format_query

__all__ = ("OperationDescriptor",)


class OperationDescriptor(BaseDescriptor[RequestModel]):
    """
    Descriptor interface for schema generation from and data validation against given operation
    """

    def __init__(self, __operation: Operation) -> None:
        self._id = __operation.id
        self.ref = __operation
        self.__metas: t.Dict[str, InputMeta | EncodableInputMeta | None] = {
            # Reserved keys - if detected in meta properties, it will be transformed in to a nested object
            "requestPath": self.ref.path_meta,
            "requestQuery": self.ref.query_meta,
            "requestHeader": self.ref.header_meta,
            "requestCookie": self.ref.cookie_meta,
            "requestBody": self.ref.body_meta,
        }
        self.__key_to_loc: t.Dict[str, str] = {}
        self.__schema: t.Dict[str, t.Any] | None = None
        self.__validator: SchemaValidator | None = None

    @property
    def id(self) -> str:
        """Identifier for the descripted operation."""
        return self._id

    @property
    def schema(self) -> t.Dict[str, t.Any]:
        """
        Get the JSON schema for the operation.

        The schema is generated on first access and cached for subsequent calls.
        """
        if self.__schema is None:
            self.__key_to_loc, properties, required = self._analyze_metas()

            schema = {"type": "object", "properties": properties}
            if desc := self.ref.description:
                schema["description"] = desc
            if required:
                schema["required"] = required
            self.__schema = schema
        return self.__schema

    def _analyze_metas(self) -> tuple[dict, dict, list]:  # noqa: C901
        key_to_loc: t.Dict[str, str] = {}
        properties: t.Dict[str, t.Any] = {}
        required: t.List[str] = []
        nested_locs: t.Set[str] = set()

        def add_properties(props: t.Dict[str, t.Any], loc: str) -> bool:
            if loc == "requestBody":
                # Always nest requestBody
                properties[loc] = {"type": "object", "properties": props}
                nested_locs.add(loc)
                return True

            for key, value in props.items():
                if key in self.__metas:
                    nested_locs.add(loc)
                    return False
                if key in properties:
                    if key_to_loc[key] != loc:
                        nested_locs.add(loc)
                        return False
                else:
                    properties[key] = value
                    key_to_loc[key] = loc
            return True

        for loc, meta in self.__metas.items():
            if meta and meta.schema_:
                props = meta.schema_.get("properties", {})
                if not add_properties(props, loc):
                    properties[loc] = meta.schema_
                    required.append(loc)
                    continue
                if loc == "requestBody":
                    required.append(loc)
                else:
                    required.extend(meta.schema_.get("required", []))

        # Handle nested locations
        for loc in nested_locs:
            meta = self.__metas[loc]
            if loc == "requestBody" or meta is None:  # Skip requestBody as it's already handled
                continue
            if loc not in properties:
                properties[loc] = meta.schema_
                required.append(loc)
            keys_to_remove = [k for k, v in key_to_loc.items() if v == loc]
            for key in keys_to_remove:
                del properties[key]
                del key_to_loc[key]

        return key_to_loc, properties, required

    def _build_request_model(self, validated_obj: t.Dict[str, t.Any]) -> RequestModel:
        """Build request model from validated object"""
        params = defaultdict(dict)  # type: ignore[var-annotated]

        for key, value in validated_obj.items():
            if key in self.__metas:
                params[key].update(value)
            else:
                loc = self.__key_to_loc.get(key)
                if loc:
                    params[loc][key] = value

        path = self.ref.path
        if path_params := params["requestPath"]:
            path = format_path(
                path, path_params, self.ref.path_meta.encodings if self.ref.path_meta else {}
            )

        encoded_query = None
        if query_params := params["requestQuery"]:
            encoded_query = format_query(
                query_params, self.ref.query_meta.encodings if self.ref.query_meta else {}
            )

        return RequestModel(
            path=path,
            method=self.ref.method,
            queries=params["requestQuery"] if params["requestQuery"] else None,
            encoded_query=encoded_query,
            headers=params["requestHeader"] if params["requestHeader"] else None,
            cookies=params["requestCookie"] if params["requestCookie"] else None,
            body=params["requestBody"] if params["requestBody"] else None,
        )

    def _validate_python(self, obj: t.Any, **kwargs: t.Any) -> RequestModel:
        """
        Validate a Python object against the operation schema.

        :param obj: Python object to validate
        :raises ValidationError: If validation fails
        :return: The request model.
        """
        if self.__validator is None:
            self.__validator = SchemaValidator(self.schema)
        validated_obj = self.__validator.validate_python(obj)
        return self._build_request_model(validated_obj)
