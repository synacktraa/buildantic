import typing as t

from ..descriptor.base import BaseDescriptor

T_Retval = t.TypeVar("T_Retval")
T_Descriptor = t.TypeVar("T_Descriptor", bound=BaseDescriptor)


class BaseRegistry(t.Generic[T_Descriptor, T_Retval]):
    """Base class to be inherited for creating new registry."""

    @property
    def descriptor_map(self) -> t.Dict[str, T_Descriptor]:
        """ID mapped descriptors"""
        raise NotImplementedError("Inherited class must implemented this property")

    def __contains__(self, __id: str) -> bool:
        """If an ID exists in the registry"""
        return __id in self.descriptor_map

    def __getitem__(self, __id: str) -> T_Descriptor:
        """Get descriptor from given ID."""
        return self.descriptor_map[__id]

    @property
    def ids(self) -> t.List[str]:
        """IDs available in the registry"""
        return list(self.descriptor_map.keys())

    @property
    def schema(self) -> t.List[t.Dict[str, t.Any]]:
        """Get the JSON schema list of registered descriptors."""
        return [descriptor.schema for descriptor in self.descriptor_map.values()]

    @property
    def openai_schema(self) -> t.List[t.Dict[str, t.Any]]:
        """Get the schema list in openai function calling format."""
        return [descriptor.openai_schema for descriptor in self.descriptor_map.values()]

    @property
    def anthropic_schema(self) -> t.List[t.Dict[str, t.Any]]:
        """Get the schema list in anthropic function calling format."""
        return [descriptor.anthropic_schema for descriptor in self.descriptor_map.values()]

    @property
    def gemini_schema(self) -> t.List[t.Dict[str, t.Any]]:
        """Get the schema list in gemini function calling format."""
        return [descriptor.gemini_schema for descriptor in self.descriptor_map.values()]

    def validate_python(self, id: str, obj: t.Any, **kwargs: t.Any) -> T_Retval:
        """
        Validate a Python object against the descripted object.

        :param id: ID or name associated with registered descriptor.
        :param obj: Python object to validate
        :param kwargs: Extra keyword arguments
        :raises ValidationError: If validation fails
        :return: The validated object
        """
        return self.descriptor_map[id].validate_python(obj, **kwargs)  # type: ignore[no-any-return]

    def validate_json(
        self, id: str, data: t.Union[str, bytes, bytearray], **kwargs: t.Any
    ) -> T_Retval:
        """
        Validate JSON data against the descripted object.

        :param id: ID or name associated with registered descriptor.
        :param data: JSON data to validate
        :param kwargs: Extra keyword arguments
        :raises ValidationError: If validation fails
        :return: The validated object
        """
        return self.descriptor_map[id].validate_json(data, **kwargs)  # type: ignore[no-any-return]
