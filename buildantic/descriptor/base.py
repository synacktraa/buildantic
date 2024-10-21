import typing as t

from ..utils import (
    drop_titles,
    extract_python_object,
    transform_to_anthropic_schema,
    transform_to_gemini_schema,
    transform_to_openai_schema,
)

T_Retval = t.TypeVar("T_Retval")


class BaseDescriptor(t.Generic[T_Retval]):
    """Base class to be inherited to define descriptors"""

    @property
    def id(self) -> str:
        """Identifier for the descripted object."""
        raise NotImplementedError("Inherited class must implemented this property")

    @property
    def schema(self) -> t.Dict[str, t.Any]:
        """Get the JSON schema for the descripted object."""
        raise NotImplementedError("Inherited class must implemented this property")

    @property
    def openai_schema(self) -> t.Dict[str, t.Any]:
        """Get the JsON schema in openai function calling format."""
        return transform_to_openai_schema(self.id, drop_titles(self.schema))

    @property
    def anthropic_schema(self) -> t.Dict[str, t.Any]:
        """Get the JsON schema in anthropic function calling format."""
        return transform_to_anthropic_schema(self.id, drop_titles(self.schema))

    @property
    def gemini_schema(self) -> t.Dict[str, t.Any]:
        """Get the JsON schema in gemini function calling format."""
        return transform_to_gemini_schema(self.id, drop_titles(self.schema))

    def _validate_python(self, obj: t.Any, **kwargs: t.Any) -> T_Retval:
        """
        Validate a Python object against the descripted object.

        :param obj: Python object to validate
        :param kwargs: Extra keyword arguments
        :raises ValidationError: If validation fails
        :return: The validated object
        """
        raise NotImplementedError("Inherited class must implemented this method")

    def validate_python(self, obj: t.Any, **kwargs: t.Any) -> T_Retval:
        """
        Validate a Python object against the descripted object.

        :param obj: Python object to validate
        :param kwargs: Extra keyword arguments
        :raises ValidationError: If validation fails
        :return: The validated object
        """
        obj = extract_python_object(obj, schema=self.schema, value_type="python")
        return self._validate_python(obj, **kwargs)

    def validate_json(self, data: t.Union[str, bytes, bytearray], **kwargs: t.Any) -> T_Retval:
        """
        Validate JSON data against the descripted object.

        :param data: JSON data to validate
        :param kwargs: Extra keyword arguments
        :raises ValidationError: If validation fails
        :return: The validated object
        """
        obj = extract_python_object(data, schema=self.schema, value_type="json")
        return self._validate_python(obj, **kwargs)
