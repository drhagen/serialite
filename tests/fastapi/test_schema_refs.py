from dataclasses import dataclass

from fastapi import FastAPI
from fastapi.testclient import TestClient

from serialite import (
    FieldsSerializer,
    SerializableMixin,
    serializable,
)


def get_openapi_schemas(app):
    client = TestClient(app)
    schema = client.get("/openapi.json").json()
    return schema["components"]["schemas"]


def test_name_collision_produces_module_qualified_refs():
    class Item(SerializableMixin):
        __fields_serializer__ = FieldsSerializer(x=int)

        def __init__(self, x: int):
            self.x = x

    ItemA = Item  # noqa: N806
    ItemA.__module__ = "package_a.models"
    ItemA.__qualname__ = "Item"

    class WrapperA(SerializableMixin):
        __fields_serializer__ = FieldsSerializer(a=ItemA)

        def __init__(self, a):
            self.a = a

    app_before = FastAPI()

    @app_before.post("/a", response_model=WrapperA)
    def endpoint_before(wrapper: WrapperA) -> WrapperA:
        return wrapper

    schemas_before = get_openapi_schemas(app_before)

    assert schemas_before["WrapperA"]["properties"]["a"] == {"$ref": "#/components/schemas/Item"}
    assert schemas_before["Item"]["properties"]["x"] == {"type": "integer"}
    assert schemas_before["Item"]["required"] == ["x"]

    class Item(SerializableMixin):
        __fields_serializer__ = FieldsSerializer(y=str)

        def __init__(self, y: str):
            self.y = y

    ItemB = Item  # noqa: N806
    ItemB.__module__ = "package_b.models"
    ItemB.__qualname__ = "Item"

    class WrapperB(SerializableMixin):
        __fields_serializer__ = FieldsSerializer(b=ItemB)

        def __init__(self, b):
            self.b = b

    app_after = FastAPI()

    @app_after.post("/a", response_model=WrapperA)
    def endpoint_a(wrapper: WrapperA) -> WrapperA:
        return wrapper

    @app_after.post("/b", response_model=WrapperB)
    def endpoint_b(wrapper: WrapperB) -> WrapperB:
        return wrapper

    schemas_after = get_openapi_schemas(app_after)

    assert schemas_after["WrapperA"]["properties"]["a"] == {
        "$ref": "#/components/schemas/package_a__models__Item"
    }
    assert schemas_after["WrapperB"]["properties"]["b"] == {
        "$ref": "#/components/schemas/package_b__models__Item"
    }

    assert schemas_after["package_a__models__Item"]["properties"]["x"] == {"type": "integer"}
    assert schemas_after["package_a__models__Item"]["required"] == ["x"]

    assert schemas_after["package_b__models__Item"]["properties"]["y"] == {"type": "string"}
    assert schemas_after["package_b__models__Item"]["required"] == ["y"]


def test_name_collision_with_dataclass():
    @serializable
    @dataclass(frozen=True)
    class Item:
        x: int

    ItemA = Item  # noqa: N806
    ItemA.__module__ = "package_a.models"
    ItemA.__qualname__ = "Item"

    @serializable
    @dataclass(frozen=True)
    class WrapperA:
        a: ItemA  # type: ignore[valid-type]

    app_before = FastAPI()

    @app_before.post("/a", response_model=WrapperA)
    def endpoint_before(wrapper: WrapperA) -> WrapperA:
        return wrapper

    schemas_before = get_openapi_schemas(app_before)

    assert schemas_before["WrapperA"]["properties"]["a"] == {"$ref": "#/components/schemas/Item"}
    assert schemas_before["Item"]["properties"]["x"] == {"type": "integer"}

    @serializable
    @dataclass(frozen=True)
    class Item:
        y: str

    ItemB = Item  # noqa: N806
    ItemB.__module__ = "package_b.models"
    ItemB.__qualname__ = "Item"

    @serializable
    @dataclass(frozen=True)
    class WrapperB:
        b: ItemB  # type: ignore[valid-type]

    app_after = FastAPI()

    @app_after.post("/a", response_model=WrapperA)
    def endpoint_a(wrapper: WrapperA) -> WrapperA:
        return wrapper

    @app_after.post("/b", response_model=WrapperB)
    def endpoint_b(wrapper: WrapperB) -> WrapperB:
        return wrapper

    schemas_after = get_openapi_schemas(app_after)

    assert schemas_after["WrapperA"]["properties"]["a"] == {
        "$ref": "#/components/schemas/package_a__models__Item"
    }
    assert schemas_after["WrapperB"]["properties"]["b"] == {
        "$ref": "#/components/schemas/package_b__models__Item"
    }

    assert schemas_after["package_a__models__Item"]["properties"]["x"] == {"type": "integer"}
    assert schemas_after["package_b__models__Item"]["properties"]["y"] == {"type": "string"}
