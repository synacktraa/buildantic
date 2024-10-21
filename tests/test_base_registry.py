import pytest

from buildantic.registry.base import BaseRegistry


class MockDescriptor:
    def __init__(self, id: str):
        self.id = id


class MockBaseRegistry(BaseRegistry):
    def __init__(self):
        self._descriptor_map = {}

    @property
    def descriptor_map(self):
        return self._descriptor_map


def test_base_registry_contains():
    registry = MockBaseRegistry()
    registry._descriptor_map = {"test": MockDescriptor("test")}
    assert "test" in registry
    assert "nonexistent" not in registry


def test_base_registry_getitem():
    registry = MockBaseRegistry()
    descriptor = MockDescriptor("test")
    registry._descriptor_map = {"test": descriptor}
    assert registry["test"] == descriptor
    with pytest.raises(KeyError):
        registry["nonexistent"]


def test_base_registry_ids():
    registry = MockBaseRegistry()
    registry._descriptor_map = {"test1": MockDescriptor("test1"), "test2": MockDescriptor("test2")}
    assert set(registry.ids) == {"test1", "test2"}


def test_base_registry_descriptors():
    registry = MockBaseRegistry()
    descriptor1 = MockDescriptor("test1")
    descriptor2 = MockDescriptor("test2")
    registry._descriptor_map = {"test1": descriptor1, "test2": descriptor2}
    assert registry.descriptor_map == {"test1": descriptor1, "test2": descriptor2}
