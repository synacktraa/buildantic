import pytest
from typing_extensions import TypedDict

from buildantic.descriptor import TypeDescriptor
from buildantic.registry import Registry


def test_registry_register_type():
    registry = Registry()

    class TestType(TypedDict):
        pass

    registered_type = registry.register(TestType)
    assert registered_type is TestType
    assert "TestType" in registry
    assert isinstance(registry["TestType"], TypeDescriptor)


def test_registry_register_function():
    registry = Registry()

    def test_function():
        pass

    registered_function = registry.register(test_function)
    assert registered_function is test_function
    assert "test_function" in registry
    assert isinstance(registry["test_function"], TypeDescriptor)


def test_registry_register_duplicate():
    registry = Registry()

    @registry.register
    class TestType(TypedDict):
        pass

    with pytest.raises(ValueError):

        @registry.register
        class TestType(TypedDict):  # Different class with the same name
            pass


def test_registry_register_decorator():
    registry = Registry()

    @registry.register
    def decorated_function():
        return "Hello, World!"

    assert "decorated_function" in registry
    assert decorated_function() == "Hello, World!"
