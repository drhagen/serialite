from dataclasses import dataclass

import pytest
from fastapi import Body, FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from serialite import (
    AbstractSerializableMixin,
    FieldsSerializer,
    SerializableMixin,
    SingleField,
    abstract_serializable,
    serializable,
)

# Starting in Python 3.10, classes can get garbage collected and not show up in
# __subclasses__ anymore. This is a place to put such objects to prevent them
# from being garbage collected.
garbage_collection_protection = []


@pytest.fixture(scope="module")
def fastapi_mixin_client():
    app = FastAPI()

    class Base(AbstractSerializableMixin):
        __subclass_serializers__ = {}  # noqa: RUF012
        __fields_serializer__ = FieldsSerializer(a=str, b=float)

        def __init__(self, a: str, b: float):
            self.a = a
            self.b = b

    class Foo(SerializableMixin, Base):
        __fields_serializer__ = FieldsSerializer(**Base.__fields_serializer__, c=bool)

        def __init__(self, a: str, b: float, c: bool):
            super().__init__(a, b)
            self.c = c

    Base.__subclass_serializers__["Foo"] = Foo

    class Bar(SerializableMixin, Base):
        __fields_serializer__ = FieldsSerializer(
            **Base.__fields_serializer__, d=SingleField(int, default=-1)
        )

        def __init__(self, a: str, b: float, d: int = -1):
            super().__init__(a, b)
            self.d = d

    Base.__subclass_serializers__["Bar"] = Bar

    garbage_collection_protection.extend([Foo, Bar])

    @app.post("/")
    def base_a(base: Base = Body(...)) -> str:
        return base.a

    class Wrapper(BaseModel):
        base: Base

    @app.post("/wrapped/")
    def wrapped(wrapped: Wrapper) -> Wrapper:
        if not isinstance(wrapped, Wrapper):
            raise TypeError
        return wrapped

    return TestClient(app)


@pytest.fixture()
def fastapi_dataclass_client():
    app = FastAPI()

    @abstract_serializable
    @dataclass(frozen=True)
    class Base:
        a: str
        b: float

    @serializable
    @dataclass(frozen=True)
    class Foo(Base):
        c: bool

    @serializable
    @dataclass(frozen=True)
    class Bar(Base):
        d: int = -1

    garbage_collection_protection.extend([Foo, Bar])

    @app.post("/")
    def base_a(base: Base) -> str:
        return base.a

    class Wrapper(BaseModel):
        base: Base

    @app.post("/wrapped/")
    def wrapped(wrapped: Wrapper) -> Wrapper:
        if not isinstance(wrapped, Wrapper):
            raise TypeError
        return wrapped

    return TestClient(app)


@pytest.mark.parametrize("client_fixture", ["fastapi_mixin_client", "fastapi_dataclass_client"])
def test_fastapi_basic(client_fixture, request):
    client = request.getfixturevalue(client_fixture)

    response = client.post("/", json={"_type": "Foo", "a": "anything", "b": 2.0, "c": True})
    assert response.json() == "anything"

    response = client.post("/", json={"_type": "Bar", "a": "anything", "b": 2.0, "d": 2})
    assert response.json() == "anything"


@pytest.mark.parametrize("client_fixture", ["fastapi_mixin_client", "fastapi_dataclass_client"])
def test_fastapi_strict(client_fixture, request):
    client = request.getfixturevalue(client_fixture)

    response = client.post("/", json={"_type": "Foo", "a": "anything", "b": "2.0", "c": True})
    assert response.status_code == 422

    response = client.post("/", json={"_type": "Bar", "a": "anything", "b": 2.0, "d": 2.0})
    assert response.status_code == 422


@pytest.mark.parametrize("client_fixture", ["fastapi_mixin_client", "fastapi_dataclass_client"])
def test_fastapi_not_too_strict(client_fixture, request):
    client = request.getfixturevalue(client_fixture)

    response = client.post("/", json={"_type": "Foo", "a": "anything", "b": 2, "c": True})
    assert response.json() == "anything"

    response = client.post("/", json={"_type": "Bar", "a": "anything", "b": 2, "d": 2})
    assert response.json() == "anything"


@pytest.mark.parametrize("client_fixture", ["fastapi_mixin_client", "fastapi_dataclass_client"])
def test_fastapi_basic_wrapped(client_fixture, request):
    client = request.getfixturevalue(client_fixture)

    data = {"base": {"_type": "Foo", "a": "anything", "b": 2.0, "c": True}}
    response = client.post("/wrapped/", json=data)
    assert response.json() == data

    data = {"base": {"_type": "Bar", "a": "anything", "b": 2.0, "d": 2}}
    response = client.post("/wrapped/", json=data)
    assert response.json() == data


@pytest.mark.parametrize("client_fixture", ["fastapi_mixin_client", "fastapi_dataclass_client"])
def test_fastapi_wrapped_strict(client_fixture, request):
    client = request.getfixturevalue(client_fixture)

    data = {"base": {"_type": "Foo", "a": "anything", "b": "2.0", "c": True}}
    response = client.post("/wrapped/", json=data)
    assert response.status_code == 422

    data = {"base": {"_type": "Bar", "a": "anything", "b": 2.0, "d": 2.0}}
    response = client.post("/wrapped/", json=data)
    assert response.status_code == 422


@pytest.mark.parametrize("client_fixture", ["fastapi_mixin_client", "fastapi_dataclass_client"])
def test_fastapi_wrapped_not_too_strict(client_fixture, request):
    client = request.getfixturevalue(client_fixture)

    data = {"base": {"_type": "Foo", "a": "anything", "b": 2, "c": True}}
    response = client.post("/wrapped/", json=data)
    assert response.json() == data

    data = {"base": {"_type": "Bar", "a": "anything", "b": 2, "d": 2}}
    response = client.post("/wrapped/", json=data)
    assert response.json() == data
