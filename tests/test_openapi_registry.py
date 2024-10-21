import pytest

from buildantic.registry import OpenAPIRegistry


def test_openapi_registry_init():
    valid_spec = {
        "openapi": "3.0.0",
        "paths": {"/test": {"get": {"operationId": "testOperation", "parameters": []}}},
    }
    registry = OpenAPIRegistry(valid_spec)
    assert "testOperation" in registry


def test_openapi_registry_invalid_spec():
    invalid_spec = {"invalid": "spec"}
    with pytest.raises(ValueError):
        OpenAPIRegistry(invalid_spec)


def test_openapi_registry_unsupported_version():
    unsupported_spec = {"openapi": "2.0.0", "paths": {}}
    with pytest.raises(ValueError):
        OpenAPIRegistry(unsupported_spec)


def test_openapi_registry_from_file(tmp_path):
    spec_content = """
    openapi: 3.0.0
    paths:
      /test:
        get:
          operationId: testOperation
          parameters: []
    """
    spec_file = tmp_path / "test_spec.yaml"
    spec_file.write_text(spec_content)

    registry = OpenAPIRegistry.from_file(spec_file)
    assert "testOperation" in registry


def test_openapi_registry_from_file_json(tmp_path):
    spec_content = """
    {
        "openapi": "3.0.0",
        "paths": {
            "/test": {
                "get": {
                    "operationId": "testOperation",
                    "parameters": []
                }
            }
        }
    }
    """
    spec_file = tmp_path / "test_spec.json"
    spec_file.write_text(spec_content)

    registry = OpenAPIRegistry.from_file(spec_file)
    assert "testOperation" in registry


def test_openapi_registry_from_file_not_found():
    with pytest.raises(FileNotFoundError):
        OpenAPIRegistry.from_file("nonexistent_file.yaml")


def test_openapi_registry_from_url(monkeypatch):
    class MockResponse:
        def read(self):
            return b'{"openapi": "3.0.0", "paths": {"/test": {"get": {"operationId": "testOperation", "parameters": []}}}}'

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    def mock_urlopen(url):
        return MockResponse()

    import urllib.request

    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen)

    registry = OpenAPIRegistry.from_url("https://example.com/api-spec.json")
    assert "testOperation" in registry


def test_openapi_registry_from_url_http_error(monkeypatch):
    import urllib.request
    from urllib.error import HTTPError

    def mock_urlopen(url):
        raise HTTPError(url, 404, "Not Found", {}, None)

    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen)

    with pytest.raises(HTTPError):
        OpenAPIRegistry.from_url("https://example.com/api-spec.json")


def test_openapi_registry_schema():
    spec = {
        "openapi": "3.0.0",
        "paths": {
            "/test": {
                "get": {
                    "operationId": "testOperation",
                    "parameters": [{"name": "param1", "in": "query", "schema": {"type": "string"}}],
                }
            }
        },
    }
    registry = OpenAPIRegistry(spec)
    schemas = registry.schema
    assert len(schemas) == 1
    assert schemas[0]["properties"]["param1"]["type"] == "string"


def test_openapi_registry_process_parameters():
    spec = {
        "openapi": "3.0.0",
        "paths": {
            "/test/{pathParam}": {
                "get": {
                    "operationId": "testOperation",
                    "parameters": [
                        {
                            "name": "pathParam",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        },
                        {"name": "queryParam", "in": "query", "schema": {"type": "integer"}},
                    ],
                }
            }
        },
    }
    registry = OpenAPIRegistry(spec)
    operation = registry["testOperation"].ref

    assert operation.path_meta.schema_["properties"]["pathParam"]["type"] == "string"
    assert operation.query_meta.schema_["properties"]["queryParam"]["type"] == "integer"
    assert operation.path_meta.schema_["required"] == ["pathParam"]


def test_openapi_registry_process_request_body():
    spec = {
        "openapi": "3.0.0",
        "paths": {
            "/test": {
                "post": {
                    "operationId": "testOperation",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {"name": {"type": "string"}},
                                }
                            }
                        },
                    },
                }
            }
        },
    }
    registry = OpenAPIRegistry(spec)
    operation = registry["testOperation"].ref

    assert operation.body_meta.schema_["type"] == "object"
    assert operation.body_meta.schema_["properties"]["name"]["type"] == "string"
    assert operation.body_required


def test_openapi_registry_include_headers():
    spec = {
        "openapi": "3.0.0",
        "paths": {
            "/test": {
                "get": {
                    "operationId": "testOperation",
                    "parameters": [
                        {"name": "X-Test-Header", "in": "header", "schema": {"type": "string"}}
                    ],
                }
            }
        },
    }
    registry = OpenAPIRegistry(spec, include_headers=True)
    operation = registry["testOperation"].ref

    assert operation.header_meta is not None
    assert operation.header_meta.schema_["properties"]["X-Test-Header"]["type"] == "string"


def test_openapi_registry_include_cookies():
    spec = {
        "openapi": "3.0.0",
        "paths": {
            "/test": {
                "get": {
                    "operationId": "testOperation",
                    "parameters": [
                        {"name": "sessionId", "in": "cookie", "schema": {"type": "string"}}
                    ],
                }
            }
        },
    }
    registry = OpenAPIRegistry(spec, include_cookies=True)
    operation = registry["testOperation"].ref

    assert operation.cookie_meta is not None
    assert operation.cookie_meta.schema_["properties"]["sessionId"]["type"] == "string"
