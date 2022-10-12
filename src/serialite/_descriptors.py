__all__ = ["classproperty"]


# classmethod cannot be used with property, so we have to manually write our own
# descriptor class. From https://stackoverflow.com/a/39542816/
class classproperty(property):  # noqa: N801
    def __get__(self, obj, objtype=None):
        return super().__get__(objtype)

    def __set__(self, obj, value):
        super().__set__(type(obj), value)

    def __delete__(self, obj):
        super().__delete__(type(obj))
