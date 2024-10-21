from buildantic.descriptor.base import BaseDescriptor


def test_base_descriptor_id_property():
    class ConcreteDescriptor(BaseDescriptor):
        @property
        def id(self):
            return "test_id"

        @property
        def schema(self):
            return {}

        def validate_python(self, obj, **kwargs):
            pass

        def validate_json(self, data, **kwargs):
            pass

    descriptor = ConcreteDescriptor()
    assert descriptor.id == "test_id"


def test_base_descriptor_schema_property():
    class ConcreteDescriptor(BaseDescriptor):
        @property
        def id(self):
            return "test_id"

        @property
        def schema(self):
            return {"type": "object"}

        def validate_python(self, obj, **kwargs):
            pass

        def validate_json(self, data, **kwargs):
            pass

    descriptor = ConcreteDescriptor()
    assert descriptor.schema == {"type": "object"}


def test_base_descriptor_openai_schema():
    class ConcreteDescriptor(BaseDescriptor):
        @property
        def id(self):
            return "test_id"

        @property
        def schema(self):
            return {"type": "object", "properties": {"foo": {"type": "string"}}}

        def validate_python(self, obj, **kwargs):
            pass

        def validate_json(self, data, **kwargs):
            pass

    descriptor = ConcreteDescriptor()
    expected_schema = {
        "name": "test_id",
        "parameters": {"type": "object", "properties": {"foo": {"type": "string"}}},
    }
    assert descriptor.openai_schema == expected_schema


def test_base_descriptor_anthropic_schema():
    class ConcreteDescriptor(BaseDescriptor):
        @property
        def id(self):
            return "test_id"

        @property
        def schema(self):
            return {"type": "object", "properties": {"foo": {"type": "string"}}}

        def validate_python(self, obj, **kwargs):
            pass

        def validate_json(self, data, **kwargs):
            pass

    descriptor = ConcreteDescriptor()
    expected_schema = {
        "name": "test_id",
        "input_schema": {"type": "object", "properties": {"foo": {"type": "string"}}},
    }
    assert descriptor.anthropic_schema == expected_schema


def test_base_descriptor_gemini_schema():
    class ConcreteDescriptor(BaseDescriptor):
        @property
        def id(self):
            return "test_id"

        @property
        def schema(self):
            return {"type": "object", "properties": {"foo": {"type": "string"}}}

        def validate_python(self, obj, **kwargs):
            pass

        def validate_json(self, data, **kwargs):
            pass

    descriptor = ConcreteDescriptor()
    expected_schema = {
        "name": "test_id",
        "parameters": {"type": "object", "properties": {"foo": {"type": "string"}}},
    }
    assert descriptor.gemini_schema == expected_schema
