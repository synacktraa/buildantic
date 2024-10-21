from __future__ import annotations

import typing as t
from io import BytesIO
from pathlib import Path

from jsonref import replace_refs  # type: ignore[import-untyped]

from ..descriptor.openapi import OperationDescriptor
from ..descriptor.openapi.types import InputMeta, Method, Operation, RequestModel
from .base import BaseRegistry

__all__ = ("OpenAPIRegistry", "OperationDescriptor")

METHODS = t.get_args(Method)


class OpenAPIRegistry(BaseRegistry[OperationDescriptor, RequestModel]):
    """Registry to store openapi operations as descriptors."""

    def __init__(
        self,
        __spec: t.Dict[str, t.Any],
        include_headers: bool = False,
        include_cookies: bool = False,
    ) -> None:
        spec = replace_refs(__spec, lazy_load=False)
        if "openapi" not in spec or "paths" not in spec:
            raise ValueError("OpenAPI specfication is invalid.")
        if not spec["openapi"].startswith("3."):
            raise ValueError("Only v3 is supported.")

        self.__spec: t.Dict[str, t.Any] = spec
        self._include_headers = include_headers
        self._include_cookies = include_cookies
        self.__descriptor_map = self._load_descriptors()

    @classmethod
    def from_file(cls, __file: str | Path | BytesIO) -> OpenAPIRegistry:
        """
        Create an openapi object from file path or object.
        JsON and Yaml formats are supported.

        :param __file: File path or object
        """
        if isinstance(__file, BytesIO):
            content = __file.read().decode("utf-8")
        else:
            if not (path := Path(__file)).is_file():
                raise FileNotFoundError(f"{str(path)!r} specification file not found.")

            content = path.read_text(encoding="utf-8")

        if content.strip().startswith("{"):  # Assuming it's in json format
            from pydantic_core import from_json

            return cls(from_json(content))

        from yaml import safe_load  # type: ignore[import-untyped]

        return cls(safe_load(content))

    @classmethod
    def from_url(cls, __url: str) -> OpenAPIRegistry:
        """
        Create an openapi tool from URL.

        :param __url: URL to fetch content
        """
        from urllib.request import urlopen

        with urlopen(__url) as response:  # noqa: S310
            content = response.read()
        return cls.from_file(BytesIO(content))

    @property
    def descriptor_map(self) -> t.Dict[str, OperationDescriptor]:
        return self.__descriptor_map

    def _load_descriptors(self) -> t.Dict[str, OperationDescriptor]:
        descriptor_map = {}
        for path, path_item in self.__spec["paths"].items():
            for method, op_dict in path_item.items():
                if method not in METHODS:
                    continue

                operation_id = op_dict.get("operationId")
                if operation_id is None:
                    continue
                metas = self._process_parameters(op_dict.get("parameters", []))
                body_meta, body_required = self._process_request_body(
                    op_dict.get("requestBody", {})
                )

                operation = Operation(
                    id=operation_id.replace(" ", "_"),
                    method=method,
                    path=path,
                    description=op_dict.get("summary") or op_dict.get("description", ""),
                    path_meta=metas["path"],
                    query_meta=metas["query"],
                    header_meta=metas["header"],
                    cookie_meta=metas["cookie"],
                    body_meta=body_meta,
                    body_required=body_required,
                )
                descriptor_map[operation_id] = OperationDescriptor(operation)

        return descriptor_map

    def _process_parameters(self, parameters: list) -> dict:
        param_types: dict = {
            "path": {"props": {}, "encoding": {}, "required": []},
            "query": {"props": {}, "encoding": {}, "required": []},
            "header": {"props": {}, "required": []},
            "cookie": {"props": {}, "required": []},
        }

        for param in parameters:
            loc = param["in"]
            if (loc == "header" and not self._include_headers) or (
                loc == "cookie" and not self._include_cookies
            ):
                continue

            self._process_parameter(param, param_types[loc])

        return {
            "path": self._create_meta(param_types["path"], include_encoding=True),
            "query": self._create_meta(param_types["query"], include_encoding=True),
            "header": self._create_meta(param_types["header"]) if self._include_headers else None,
            "cookie": self._create_meta(param_types["cookie"]) if self._include_cookies else None,
        }

    def _process_parameter(self, param: dict, param_type: dict) -> None:
        schema = param.pop("schema", {"type": "any"})
        if "description" in param:
            schema["description"] = param.pop("description")
        param_type["props"][param["name"]] = schema

        if "encoding" in param_type:
            param_type["encoding"][param["name"]] = {
                "style": param.pop("style", "simple" if param["in"] == "path" else "form"),
                "explode": param.pop("explode", False),
            }

        if param.pop("required", False):
            param_type["required"].append(param["name"])

    def _create_meta(self, param_type: dict, include_encoding: bool = False) -> dict | None:
        if not param_type["props"]:
            return None

        meta = {"schema_": {"type": "object", "properties": param_type["props"]}}
        if param_type["required"]:
            meta["schema_"]["required"] = param_type["required"]
        if include_encoding:
            meta["encodings"] = param_type["encoding"]

        return meta

    def _process_request_body(self, request_body: dict) -> tuple[InputMeta | None, bool]:
        if not request_body:
            return None, False

        content: dict = next(iter(request_body.get("content", {}).values()), {})
        schema = content.pop("schema", {"type": "object", "additionalProperties": True})
        if "description" in request_body:
            schema["description"] = request_body.pop("description")
        body_meta = {"schema_": schema}
        body_required = request_body.pop("required", False)

        return body_meta, body_required  # type: ignore[return-value]
