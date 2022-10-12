# Serialite

Serialite is a library serializing and deserializing arbitrarily complex objects in Python. You
apply the `@serializable` decorator to a dataclass to automatically create `to_data` and `from_data`
methods using the type annotations. Or for more control, inherit from the `SerializableMixin` and
implement the class attribute `__fields_serializer__`. For even more control, inherit from the 
abstract base class `Serializer` and implement the `to_data` and `from_data` methods directly. 

## Basics

The abstract base class is `Serializer`:

```python
class Serializer(Generic[Output]):
    def from_data(self, data: Json) -> DeserializationSuccess[Output]: ...
    def to_data(self, value: Output) -> Json: ...
```

The class is generic in the type of the object that it serializes. The two abstract methods
`from_data` and `to_data` are the key to the whole design, which revolves around getting objects to
and from JSON-serializable data, which are objects constructed entirely of `bool`s, `int`s, 
`float`s, `list`s, and `dict`s. Such structures can be consumed by `json.dumps` to produce a string
and produced by `json.loads` after consuming a string. By basing the serialization around JSON
serializable data, complex structures can be built up or torn down piece by piece while
alternatively building up complex error messages during deserialization which pinpoint the location
in the structure where the bad data exist.

For new classes, it is recommended that the `Serializer` be implemented on the class itself. There is
an abstract base class `Serializable` that classes can inherit from to indicate this. There is a mixin
`SerializableMixin` that provides an implementation of `from_data` and `to_data` for any class that
implements the `__fields_serializer` class attribute.

For `dataclass`es, it is even easier. There is a decorator `serializable` that inserts
`SerializableMixin` into the list of base classes after the `dataclass` decorator has run and also
generates `__fields_serializer__` from the data class attributes.

Finding the correct serializer for each type can be a pain, so
`serializer(cls: type) -> Serializer` is provided as a convenience function. This is a single
dispatch function, which looks up the serializer registered for a particular type. For example,
`serializer(list[float])` will return `ListSerializer(FloatSerializer)`.
