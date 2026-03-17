from dataclasses import dataclass

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from serialite import FieldsSerializer, SerializableMixin, SingleField, serializable

# If a Serialite class is passed directly to FastAPI, its deserialization and
# serialization is handled directly by FastAPI. If a Serialite class is a member
# of a Pydantic class, its deserialization and serialization is handled by
# Pydantic. Both cases need to be tested.


@pytest.fixture
def fastapi_mixin_client():
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

    class Bar(SerializableMixin):
        __fields_serializer__ = FieldsSerializer(foo=Foo)

        def __init__(self, foo: Foo):
            self.foo = foo

    @app.post("/", response_model=Bar)
    def extract_foo(bar: Bar) -> Bar:
        if not isinstance(bar, Bar):
            raise TypeError
        return bar

    return TestClient(app)


@pytest.fixture
def pydantic_mixin_client():
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

    class Bar(BaseModel):
        foo: Foo

    @app.post("/", response_model=Bar)
    def extract_foo(bar: Bar) -> Bar:
        return bar

    return TestClient(app)


@pytest.fixture
def fastapi_dataclass_client():
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
    class Bar:
        foo: Foo

    @app.post("/", response_model=Bar)
    def extract_foo(bar: Bar) -> Bar:
        if not isinstance(bar, Bar):
            raise TypeError
        return bar

    return TestClient(app)


@pytest.fixture
def pydantic_dataclass_client():
    app = FastAPI()

    @serializable
    @dataclass(frozen=True)
    class Foo:
        a: int
        b: float
        c: bool
        d: str = "default"

    class Bar(BaseModel):
        foo: Foo

    @app.post("/", response_model=Bar)
    def extract_foo(bar: Bar) -> Bar:
        if not isinstance(bar, Bar):
            raise TypeError
        return bar

    return TestClient(app)


all_clients = [
    "fastapi_mixin_client",
    "pydantic_mixin_client",
    "fastapi_dataclass_client",
    "pydantic_dataclass_client",
]


@pytest.mark.parametrize("client_fixture", all_clients)
def test_fastapi(client_fixture, request):
    client = request.getfixturevalue(client_fixture)

    data = {"foo": {"a": 1, "b": 2.0, "c": True, "d": "anything"}}
    response = client.post("/", json=data)
    assert response.json() == data


@pytest.mark.parametrize("client_fixture", all_clients)
def test_fastapi_ignore_default(client_fixture, request):
    client = request.getfixturevalue(client_fixture)

    data = {"foo": {"a": 1, "b": 2.0, "c": True}}
    response = client.post("/", json=data)
    assert response.json() == data


@pytest.mark.parametrize("client_fixture", all_clients)
def test_fastapi_drop_default(client_fixture, request):
    client = request.getfixturevalue(client_fixture)

    response = client.post("/", json={"foo": {"a": 1, "b": 2.0, "c": True, "d": "default"}})
    assert response.json() == {"foo": {"a": 1, "b": 2.0, "c": True}}


@pytest.mark.parametrize("client_fixture", all_clients)
def test_fastapi_strict(client_fixture, request):
    client = request.getfixturevalue(client_fixture)

    response = client.post("/", json={"foo": {"a": "1", "b": 2.0, "c": True, "d": "anything"}})
    assert response.status_code == 422


@pytest.mark.parametrize("client_fixture", all_clients)
def test_fastapi_error_messages(client_fixture, request):
    client = request.getfixturevalue(client_fixture)

    response = client.post("/", json={"foo": {"a": "1", "b": 2.0, "c": 1, "d": "anything"}})

    messages = response.json()["detail"]
    assert len(messages) == 2

    message1 = messages[0]
    assert message1["type"] == "ExpectedIntegerError"
    assert message1["loc"] == ["body", "foo", "a"]
    assert message1["ctx"] == {"actual": "1"}
    assert message1["msg"] == "Expected integer, but got '1'"

    message2 = messages[1]
    assert message2["type"] == "ExpectedBooleanError"
    assert message2["loc"] == ["body", "foo", "c"]
    assert message2["ctx"] == {"actual": 1}
    assert message2["msg"] == "Expected boolean, but got 1"


@pytest.mark.parametrize("client_fixture", all_clients)
def test_fastapi_not_too_strict(client_fixture, request):
    client = request.getfixturevalue(client_fixture)

    data = {"foo": {"a": 1, "b": 2, "c": True, "d": "anything"}}
    response = client.post("/", json=data)
    assert response.json() == data
    assert isinstance(response.json()["foo"]["b"], float)


@pytest.fixture
def fastapi_pydantic_client():
    app = FastAPI()

    class Foo(BaseModel):
        a: int
        b: float
        c: bool
        d: str = "default"

    class Bar(BaseModel):
        foo: Foo

    @app.post("/", response_model=Bar)
    def extract_foo(bar: Bar) -> Bar:
        if not isinstance(bar, Bar):
            raise TypeError
        return bar

    return TestClient(app)


@pytest.mark.parametrize("client_fixture", all_clients)
def test_schema(client_fixture, request, fastapi_pydantic_client):
    client = request.getfixturevalue(client_fixture)

    actual_response = client.get("/openapi.json").json()
    expected_response = fastapi_pydantic_client.get("/openapi.json").json()
    assert actual_response["paths"] == expected_response["paths"]
    assert actual_response["paths"] == expected_response["paths"]
    assert actual_response["components"]["schemas"]["Bar"]["type"] == "object"
    assert actual_response["components"]["schemas"]["Foo"]["type"] == "object"
    assert (
        actual_response["components"]["schemas"]["Bar"]["properties"]
        == expected_response["components"]["schemas"]["Bar"]["properties"]
    )
    assert actual_response["components"]["schemas"]["Bar"]["required"] == ["foo"]
    assert actual_response["components"]["schemas"]["Foo"]["required"] == ["a", "b", "c"]
    assert actual_response["components"]["schemas"]["Foo"]["properties"]["a"]["type"] == "integer"
    assert actual_response["components"]["schemas"]["Foo"]["properties"]["b"]["type"] == "number"
    assert actual_response["components"]["schemas"]["Foo"]["properties"]["c"]["type"] == "boolean"
    assert actual_response["components"]["schemas"]["Foo"]["properties"]["d"]["type"] == "string"
    assert (
        actual_response["components"]["schemas"]["Foo"]["properties"]["d"]["default"] == "default"
    )
