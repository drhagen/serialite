from dataclasses import dataclass

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from serialite import FieldsSerializer, SerializableMixin, SingleField, serializable


@pytest.fixture
def fastapi_list_mixin_client():
    app = FastAPI()

    class Foo(SerializableMixin):
        __fields_serializer__ = FieldsSerializer(
            a=int, b=float, c=bool, d=SingleField(str, default="default")
        )

        def __init__(self, a: int, b: float, c: bool, d: str = "default"):
            self.a = a
            self.b = b
            self.c = c
            self.d = d

    class Baz(SerializableMixin):
        __fields_serializer__ = FieldsSerializer(x=str)

        def __init__(self, x: str):
            self.x = x

    class Bar(SerializableMixin):
        __fields_serializer__ = FieldsSerializer(foo=list[Foo], baz=list[Baz])

        def __init__(self, foo: list[Foo], baz: list[Baz]):
            self.foo = foo
            self.baz = baz

    @app.post("/", response_model=Bar)
    def extract_foo(bar: Bar) -> Bar:
        if not isinstance(bar, Bar):
            raise TypeError
        return bar

    return TestClient(app)


@pytest.fixture
def fastapi_list_dataclass_client():
    app = FastAPI()

    @serializable
    @dataclass(frozen=True)
    class Foo:
        a: int
        b: float
        c: bool
        d: str = "default"

    @serializable
    @dataclass(frozen=True)
    class Baz:
        x: str

    @serializable
    @dataclass(frozen=True)
    class Bar:
        foo: list[Foo]
        baz: list[Baz]

    @app.post("/", response_model=Bar)
    def extract_foo(bar: Bar) -> Bar:
        if not isinstance(bar, Bar):
            raise TypeError
        return bar

    return TestClient(app)


list_clients = [
    "fastapi_list_mixin_client",
    "fastapi_list_dataclass_client",
]


@pytest.mark.parametrize("client_fixture", list_clients)
def test_schema_list_field(client_fixture, request):
    """Types nested inside list[T] must appear in components/schemas."""
    client = request.getfixturevalue(client_fixture)

    schema = client.get("/openapi.json").json()
    schemas = schema["components"]["schemas"]

    assert "Bar" in schemas
    assert schemas["Bar"]["type"] == "object"
    assert schemas["Bar"]["required"] == ["foo", "baz"]
    bar_foo = schemas["Bar"]["properties"]["foo"]
    assert bar_foo["type"] == "array"
    assert bar_foo["items"] == {"$ref": "#/components/schemas/Foo"}
    bar_baz = schemas["Bar"]["properties"]["baz"]
    assert bar_baz["type"] == "array"
    assert bar_baz["items"] == {"$ref": "#/components/schemas/Baz"}

    assert "Foo" in schemas
    assert schemas["Foo"]["type"] == "object"
    assert schemas["Foo"]["required"] == ["a", "b", "c"]

    assert "Baz" in schemas
    assert schemas["Baz"]["type"] == "object"
    assert schemas["Baz"]["required"] == ["x"]
