from dataclasses import dataclass
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from serialite import (
    Errors,
    ExpectedStringError,
    Failure,
    Serializable,
    Success,
    ValidationError,
    serializable,
)

# A custom scalar is a Serializable subclass of a type that already has a builtin
# serializer (here UUID). The dispatcher must use the subclass's own from_data/
# to_data. And since it is not an OpenAPI component, its schema is inlined into
# the owning model rather than emitted as a separate $ref.


class UUID7(UUID, Serializable):
    """A UUID constrained to version 7."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.version != 7:
            raise ValueError(f"Not a version 7 UUID: {self}")

    @classmethod
    def from_data(cls, data):
        if not isinstance(data, str):
            return Failure(Errors.one(ExpectedStringError(data)))
        try:
            value = cls(data)
        except ValueError:
            error = ValidationError(f"Expected UUID version 7, but got {data!r}")
            return Failure(Errors.one(error))
        return Success(value)

    def to_data(self):
        return str(self)

    @classmethod
    def to_openapi_schema(cls, serializer_to_ref, *, force=False):
        return {"type": "string", "format": "uuid"}


@serializable
@dataclass(frozen=True)
class Event:
    id: UUID7


valid_v7 = "018f8f8f-8f8f-7f8f-8f8f-8f8f8f8f8f8f"
non_v7 = "00112233-4455-6677-8899-aabbccddeeff"


@pytest.fixture
def client():
    app = FastAPI()

    @app.post("/", response_model=Event)
    def echo(event: Event) -> Event:
        return event

    return TestClient(app)


def test_schema_is_inlined(client):
    schemas = client.get("/openapi.json").json()["components"]["schemas"]

    # UUID7 is not an OpenAPI component, so its schema is inlined into the
    # owning property rather than emitted as a separate $ref component.
    assert schemas["Event"]["properties"]["id"] == {"type": "string", "format": "uuid"}
    assert "UUID7" not in schemas


def test_round_trip(client):
    response = client.post("/", json={"id": valid_v7})
    assert response.status_code == 200
    assert response.json() == {"id": valid_v7}


def test_validation_error_propagates(client):
    response = client.post("/", json={"id": non_v7})
    assert response.status_code == 422

    detail = response.json()["detail"]
    assert len(detail) == 1
    assert detail[0]["type"] == "ValidationError"
    assert detail[0]["loc"] == ["body", "id"]
    assert detail[0]["msg"] == f"Expected UUID version 7, but got {non_v7!r}"
