import pytest

pytest.importorskip("numpy")

import numpy as np

import testfixtures.numpy
from testfixtures import ShouldRaise, compare


def test_importable():
    compare(testfixtures.numpy.numpy.__name__, expected="numpy")


def test_equal_arrays():
    a1 = np.array([1, 2, 3])
    a2 = np.array([1, 2, 3])
    with ShouldRaise(ValueError(
        "The truth value of an array with more than one element is ambiguous."
        " Use a.any() or a.all()"
    )):
        compare(a1, expected=a2)


def test_unequal_arrays():
    a1 = np.array([1, 2, 3])
    a2 = np.array([1, 2, 4])
    with ShouldRaise(ValueError(
        "The truth value of an array with more than one element is ambiguous."
        " Use a.any() or a.all()"
    )):
        compare(a1, expected=a2)


def test_equal_arrays_in_dict():
    a1 = np.array([1, 2, 3])
    a2 = np.array([1, 2, 3])
    with ShouldRaise(ValueError(
        "The truth value of an array with more than one element is ambiguous."
        " Use a.any() or a.all()"
    )):
        compare({"foo": a1}, expected={"foo": a2})
