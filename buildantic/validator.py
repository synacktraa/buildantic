import typing as t

from jsonschema.validators import validator_for  # type: ignore[import-untyped]
from pydantic_core import from_json

if t.TYPE_CHECKING:
    from jsonschema.protocols import Validator as ValidatorProtocol  # type: ignore[import-untyped]

__all__ = ("SchemaValidator",)


class SchemaValidator:
    """
    Validator interface for data validation against given schema.
    This is different from pydantic's schema validator which uses jsonschema library
    """

    def __init__(self, __schema: t.Dict[str, t.Any]) -> None:
        """
        Create a schema validator instance.

        :param __schema: The schema to create validator from
        """
        validator_cls: type[ValidatorProtocol] = validator_for(__schema)  # type: ignore[no-any-unimported]
        validator_cls.check_schema(__schema)
        self.__instance: ValidatorProtocol = validator_cls(__schema)  # type: ignore[no-any-unimported]

    def validate_python(self, obj: t.Any) -> t.Any:
        """
        Validate a Python object against the schema.

        :param obj: Python object to validate
        :raises ValidationError: If validation fails
        :return: The validated python object
        """
        self.__instance.validate(instance=obj)
        return obj

    def validate_json(self, data: t.Union[str, bytes, bytearray]) -> t.Any:
        """
        Validate JSON data against the schema.

        :param data: JSON data to validate
        :raises ValidationError: If validation fails
        :return: The validated python object
        """
        return self.validate_python(obj=from_json(data))
