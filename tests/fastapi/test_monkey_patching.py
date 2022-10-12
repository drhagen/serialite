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
