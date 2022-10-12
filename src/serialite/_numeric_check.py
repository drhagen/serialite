__all__ = ["is_int", "is_real"]

from numbers import Real


def is_int(value):
    """Tests if a value is of type int.

    This behaves exactly like isinstance(value, int) except that bool is
    specifically excluded. In Python, bool is a proper subclass of int.
    """
    return isinstance(value, int) and not isinstance(value, bool)


def is_real(value):
    """Tests if a value is of type Real.

    This behaves exactly like isinstance(value, Real) except that bool is
    specifically excluded. In Python, bool is a proper subclass of int.
    """
    return isinstance(value, Real) and not isinstance(value, bool)
