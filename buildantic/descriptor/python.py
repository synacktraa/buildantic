from __future__ import annotations

import typing as t

from jsonref import replace_refs  # type: ignore[import-untyped]

from ..utils import generate_random_suffix, update_schema
from .base import BaseDescriptor

__all__ = ("TypeDescriptor",)


T_Retval = t.TypeVar("T_Retval")


class TypeDescriptor(BaseDescriptor[T_Retval]):
    """
    Descriptor interface for schema generation from and data validation against given type.

    A wrapper around Pydantic `TypeAdapter` to populate docstring from object type into schema.
    """

    @t.overload
    def __init__(self, __type: type[T_Retval]) -> None:
        """Descript a type"""

    @t.overload
    def __init__(self, __type: t.Callable[..., T_Retval]) -> None:
        """Descript a function"""

    def __init__(self, __type: type[T_Retval] | t.Callable[..., T_Retval]) -> None:
        from pydantic.fields import FieldInfo
        from pydantic.type_adapter import TypeAdapter

        self.__id = None
        if t.get_origin(__type) is t.Annotated:
            if len(args := t.get_args(__type)) < 2:
                raise TypeError("Annotated types must have more than 1 argument.")
            if isinstance(field := args[1], FieldInfo) and field.alias:
                self.__id = field.alias

        if self.__id is None:
            self.__id = getattr(__type, "__name__", f"id_{generate_random_suffix()}")

        self.ref = __type
        self.__adapter = TypeAdapter[T_Retval](type=self.ref)
        self.__schema: t.Dict[str, t.Any] | None = None

    @property
    def id(self) -> str:
        """Identifier for the descripted type."""
        return self.__id  # type: ignore[return-value]

    @property
    def schema(self) -> t.Dict[str, t.Any]:
        """
        Get the JSON schema for the type.

        The schema is generated on first access and cached for subsequent calls.
        """
        if self.__schema is None:
            base_schema = self.__adapter.json_schema()
            if "$defs" in base_schema:
                base_schema = replace_refs(base_schema, lazy_load=False)
                _ = base_schema.pop("$defs", None)
            self.__schema = update_schema(self.ref, base_schema)  # type: ignore[arg-type]
        return self.__schema

    def _validate_python(self, obj: t.Any, **kwargs: t.Any) -> T_Retval:
        """
        Validate a Python object against the specified type.

        :param obj: Python object to validate
        :raises ValidationError: If validation fails
        :return: The validated object
        """
        return self.__adapter.validate_python(obj, **kwargs)


@t.overload
def descript(__type: type[T_Retval]) -> TypeDescriptor[T_Retval]: ...
@t.overload
def descript(__type: t.Callable[..., T_Retval]) -> TypeDescriptor[T_Retval]: ...


def descript(__type: t.Any) -> TypeDescriptor:
    """Alias for `TypeDescriptor` to be used as decorator"""
    return TypeDescriptor(__type)
