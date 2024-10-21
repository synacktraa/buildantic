import typing as t

from ..descriptor.python import T_Retval, TypeDescriptor
from .base import BaseRegistry

__all__ = ("Registry",)


FunctionType = t.TypeVar("FunctionType", bound=t.Callable)


class Registry(BaseRegistry[TypeDescriptor, t.Any]):
    """Registry to store python types and functions as descriptors."""

    def __init__(self) -> None:
        """Registry instance"""
        self.__descriptor_map: t.Dict[str, TypeDescriptor] = {}

    @property
    def descriptor_map(self) -> t.Dict[str, TypeDescriptor]:
        return self.__descriptor_map

    @t.overload
    def register(self, __type: t.Type[T_Retval]) -> t.Type[T_Retval]:
        """
        Register a python type

        :param __type: The type to register
        :returns: The same type after registering
        """

    @t.overload
    def register(self, __type: FunctionType) -> FunctionType:
        """
        Register a function

        :param __type: The function to register
        :returns: The same function after registering
        """

    def register(self, __type: t.Any) -> t.Any:
        id = __type.__name__
        if id in self.__descriptor_map and self.__descriptor_map[id].ref is not __type:
            raise ValueError(f"Type with id {id!r} already registered.")

        descriptor = TypeDescriptor(__type)
        self.__descriptor_map[descriptor.id] = descriptor
        return __type
