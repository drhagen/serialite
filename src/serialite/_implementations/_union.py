__all__ = ["OptionalSerializer", "TryUnionSerializer"]

from .._base import Serializer
from .._errors import Errors
from .._openapi import is_openapi_component
from .._result import Failure, Result, Success


class TryUnionSerializer(Serializer):
    def __init__(self, *serializers: Serializer):
        self.serializers = serializers

    def from_data(self, data):
        # Try each possibility and return the first value that succeeds,
        # otherwise return all errors.
        errors = Errors()
        for serializer in self.serializers:
            match serializer.from_data(data):
                case Failure(error):
                    # Use the serializer representation as the location so that
                    # Errors are more readable.
                    errors.extend(error)
                case Success(value):
                    return Success(value)

        return Failure(errors)

    def to_data(self, value):
        # Try each possibility. It should not be possible for both to fail.
        errors = []
        for serializer in self.serializers:
            try:
                return serializer.to_data(value)
            except Exception as e:
                errors.append(e)

        raise ValueError(
            "All available serializers failed: " + ", ".join(map(str, self.serializers)), errors
        )

    def child_components(self):
        components = {}
        for i, serializer in enumerate(self.serializers):
            if is_openapi_component(serializer):
                components[str(i)] = serializer
        return components

    def to_openapi_schema(self, force: bool = False):
        return {
            "oneOf": [serializer.to_openapi_schema() for serializer in self.serializers],
        }


class OptionalSerializer[Element](Serializer[Element | None]):
    def __init__(self, element_serializer: Serializer[Element]):
        self.element_serializer = element_serializer

    def from_data(self, data) -> Result[Element | None]:
        if data is None:
            return Success(None)
        else:
            # Delegate to the element serializer
            return self.element_serializer.from_data(data)

    def to_data(self, value: Element | None):
        if value is None:
            return None
        else:
            return self.element_serializer.to_data(value)

    def child_components(self):
        if is_openapi_component(self.element_serializer):
            return {"element": self.element_serializer}
        else:
            return {}

    def to_openapi_schema(self, force: bool = False):
        return self.element_serializer.to_openapi_schema() | {"nullable": True}
