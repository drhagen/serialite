from pydantic import BaseModel

from serialite import SerializableMixin


def test_serialite_is_subclass_of_pydantic():
    class Foo(SerializableMixin):
        def __init__(self, a: int):
            self.a = a

    assert issubclass(Foo, BaseModel)


def test_random_is_not_subclass_of_pydantic():
    assert not issubclass(list, BaseModel)


def test_serialite_is_not_subclass_of_pydantic_subclass():
    class Foo(SerializableMixin):
        def __init__(self, a: int):
            self.a = a

    class UnknownClass(BaseModel):
        pass

    assert not issubclass(Foo, UnknownClass)


def test_serialite_instance_is_instance_of_pydantic():
    class Foo(SerializableMixin):
        def __init__(self, a: int):
            self.a = a

    assert isinstance(Foo(a=1), BaseModel)


def test_random_is_not_instance_of_pydantic():
    assert not isinstance([], BaseModel)


def test_serialite_instance_is_not_instance_of_pydantic_subclass():
    class Foo(SerializableMixin):
        def __init__(self, a: int):
            self.a = a

    class UnknownClass(BaseModel):
        pass

    assert not isinstance(Foo(a=1), UnknownClass)
