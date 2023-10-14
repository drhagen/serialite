import pytest

from serialite import StableSet


@pytest.mark.parametrize(
    ("set1", "set2"),
    [
        (StableSet(), StableSet()),
        (StableSet(4, 1), StableSet(4, 1)),
        (StableSet(4, 1), StableSet(1, 4)),
    ],
)
def test_equal(set1, set2):
    assert set1 == set2


@pytest.mark.parametrize(
    ("set1", "set2"),
    [
        (StableSet(), StableSet(2)),
        (StableSet(2), StableSet()),
        (StableSet(4), StableSet(4, 1)),
        (StableSet(4, 1), StableSet(4)),
    ],
)
def test_not_equal(set1, set2):
    assert set1 != set2


@pytest.mark.parametrize(
    ("set1", "set2", "expected"),
    [
        (StableSet(), StableSet(), StableSet()),
        (StableSet(4, 1), StableSet(4), StableSet(4, 1)),
        (StableSet(4, 1, 2), StableSet(4, 5, 6), StableSet(4, 1, 2, 5, 6)),
    ],
)
def test_union(set1, set2, expected):
    actual = set1 | set2
    assert actual == expected
    assert list(actual) == list(expected)


@pytest.mark.parametrize(
    ("set1", "set2", "expected"),
    [
        (StableSet(), StableSet(), StableSet()),
        (StableSet(4, 1), StableSet(1, 4), StableSet(4, 1)),
        (StableSet(4, 1), StableSet(4), StableSet(4)),
        (StableSet(4, 1, 2), StableSet(4, 5, 6), StableSet(4)),
    ],
)
def test_intersection(set1, set2, expected):
    actual = set1 & set2
    assert actual == expected
    assert list(actual) == list(expected)


@pytest.mark.parametrize(
    ("set1", "set2", "expected"),
    [
        (StableSet(), StableSet(), StableSet()),
        (StableSet(4, 1), StableSet(1, 4), StableSet()),
        (StableSet(4, 1), StableSet(4), StableSet(1)),
        (StableSet(4, 1, 2), StableSet(4, 5, 6), StableSet(1, 2)),
    ],
)
def test_subtraction(set1, set2, expected):
    actual = set1 - set2
    assert actual == expected
    assert list(actual) == list(expected)


@pytest.mark.parametrize(
    ("set1", "set2", "expected"),
    [
        (StableSet(), StableSet(), StableSet()),
        (StableSet(4, 1), StableSet(1, 4), StableSet()),
        (StableSet(4, 1), StableSet(4), StableSet(1)),
        (StableSet(4, 1, 2), StableSet(4, 5, 6), StableSet(1, 2, 5, 6)),
    ],
)
def test_difference(set1, set2, expected):
    actual = set1 ^ set2
    assert actual == expected
    assert list(actual) == list(expected)
