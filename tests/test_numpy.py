import pytest

pytest.importorskip("numpy")

import numpy as np

import testfixtures.numpy
from testfixtures import ShouldAssert, compare

NUMPY_2_4 = np.lib.NumpyVersion(np.__version__) >= "2.4.0"


def mismatch_at_index(detail: str) -> str:
    if NUMPY_2_4:
        return "Mismatch at index:\n " + detail + "\n"
    return ""


def test_importable():
    compare(testfixtures.numpy.numpy.__name__, expected="numpy")


def test_equal_arrays():
    a1 = np.array([1, 2, 3])
    a2 = np.array([1, 2, 3])
    compare(a1, expected=a2)


def test_unequal_arrays():
    a1 = np.array([1, 2, 3])
    a2 = np.array([1, 2, 4])
    with ShouldAssert(
        "\n"
        "Arrays are not equal\n"
        "\n"
        "Mismatched elements: 1 / 3 (33.3%)\n"
        + mismatch_at_index("[2]: 3 (ACTUAL), 4 (DESIRED)") +
        "Max absolute difference among violations: 1\n"
        "Max relative difference among violations: 0.25\n"
        " ACTUAL: array([1, 2, 3])\n"
        " DESIRED: array([1, 2, 4])"
    ):
        compare(a1, expected=a2)


def test_unequal_arrays_in_dict_breadcrumb():
    a1 = np.array([1])
    a2 = np.array([2])
    with ShouldAssert(
        "dict not as expected:\n"
        "\n"
        "values differ:\n"
        "'foo': array([2]) (expected) != array([1]) (actual)\n"
        "\n"
        "While comparing ['foo']: \n"
        "Arrays are not equal\n"
        "\n"
        "Mismatched elements: 1 / 1 (100%)\n"
        + mismatch_at_index("[0]: 1 (ACTUAL), 2 (DESIRED)") +
        "Max absolute difference among violations: 1\n"
        "Max relative difference among violations: 0.5\n"
        " ACTUAL: array([1])\n"
        " DESIRED: array([2])"
    ):
        compare({"foo": a1}, expected={"foo": a2})


def test_floats_within_tolerance_compare_equal():
    a1 = np.array([1.0 + 1e-9, 2.0])
    a2 = np.array([1.0, 2.0])
    compare(a1, expected=a2)


def test_floats_outside_tolerance():
    a1 = np.array([1.0, 2.0, 3.0])
    a2 = np.array([1.0, 2.5, 3.0])
    with ShouldAssert(
        "\n"
        "Not equal to tolerance rtol=1e-05, atol=1e-08\n"
        "\n"
        "Mismatched elements: 1 / 3 (33.3%)\n"
        + mismatch_at_index("[1]: 2.0 (ACTUAL), 2.5 (DESIRED)") +
        "Max absolute difference among violations: 0.5\n"
        "Max relative difference among violations: 0.2\n"
        " ACTUAL: array([1., 2., 3.])\n"
        " DESIRED: array([1. , 2.5, 3. ])"
    ):
        compare(a1, expected=a2)


def test_strict_requires_exact_floats():
    a1 = np.array([1.0 + 1e-9, 2.0])
    a2 = np.array([1.0, 2.0])
    with ShouldAssert(
        "\n"
        "Arrays are not equal\n"
        "\n"
        "Mismatched elements: 1 / 2 (50%)\n"
        + mismatch_at_index("[0]: 1.000000001 (ACTUAL), 1.0 (DESIRED)") +
        "Max absolute difference among violations: 1.00000008e-09\n"
        "Max relative difference among violations: 1.00000008e-09\n"
        " ACTUAL: array([1., 2.])\n"
        " DESIRED: array([1., 2.])"
    ):
        compare(a1, expected=a2, strict=True)


def test_strict_exact_floats_compare_equal():
    a1 = np.array([1.0, 2.0])
    a2 = np.array([1.0, 2.0])
    compare(a1, expected=a2, strict=True)


def test_dtype_checked_even_when_not_strict():
    a1 = np.array([1, 2], dtype=np.int32)
    a2 = np.array([1, 2], dtype=np.int64)
    with ShouldAssert(
        "\n"
        "Arrays are not equal\n"
        "\n"
        "(dtypes int32, int64 mismatch)\n"
        " ACTUAL: array([1, 2], dtype=int32)\n"
        " DESIRED: array([1, 2])"
    ):
        compare(a1, expected=a2)


def test_shape_checked_no_broadcasting():
    a1 = np.array([3.0, 3.0, 3.0])
    a2 = np.array(3.0)
    with ShouldAssert(
        "\n"
        "Not equal to tolerance rtol=1e-05, atol=1e-08\n"
        "\n"
        "(shapes (3,), () mismatch)\n"
        " ACTUAL: array([3., 3., 3.])\n"
        " DESIRED: array(3.)"
    ):
        compare(a1, expected=a2)


def test_nan_equals_nan():
    a1 = np.array([1.0, np.nan])
    a2 = np.array([1.0, np.nan])
    compare(a1, expected=a2)


def test_nan_equals_nan_strict():
    a1 = np.array([1.0, np.nan])
    a2 = np.array([1.0, np.nan])
    compare(a1, expected=a2, strict=True)


def test_zero_d_arrays_equal():
    compare(np.array(1.0), expected=np.array(1.0))


def test_zero_d_arrays_unequal():
    with ShouldAssert(
        "\n"
        "Not equal to tolerance rtol=1e-05, atol=1e-08\n"
        "\n"
        "Mismatched elements: 1 / 1 (100%)\n"
        "Max absolute difference among violations: 1.\n"
        "Max relative difference among violations: 1.\n"
        " ACTUAL: array(2.)\n"
        " DESIRED: array(1.)"
    ):
        compare(np.array(2.0), expected=np.array(1.0))


def test_equal_masked_arrays():
    m1 = np.ma.MaskedArray([1, 2, 3], mask=[False, True, False])
    m2 = np.ma.MaskedArray([1, 2, 3], mask=[False, True, False])
    compare(m1, expected=m2)


def test_masked_positions_ignore_underlying_data():
    m1 = np.ma.MaskedArray([1, 2, 3], mask=[False, True, False])
    m2 = np.ma.MaskedArray([1, 9, 3], mask=[False, True, False])
    compare(m1, expected=m2)


def test_mask_mismatch_fails_even_when_not_strict():
    m1 = np.ma.MaskedArray([1, 2, 3], mask=[False, True, False])
    m2 = np.ma.MaskedArray([1, 2, 3], mask=[False, False, False])
    with ShouldAssert(
        "masks differ: \n"
        "Arrays are not equal\n"
        "\n"
        "Mismatched elements: 1 / 3 (33.3%)\n"
        + mismatch_at_index("[1]: True (ACTUAL), False (DESIRED)") +
        " ACTUAL: array([False,  True, False])\n"
        " DESIRED: array([False, False, False])"
    ):
        compare(m1, expected=m2)


def test_unequal_masked_data():
    m1 = np.ma.MaskedArray([1, 2, 3], mask=[False, False, False])
    m2 = np.ma.MaskedArray([1, 4, 3], mask=[False, False, False])
    with ShouldAssert(
        "\n"
        "Arrays are not equal\n"
        "\n"
        "Mismatched elements: 1 / 3 (33.3%)\n"
        + mismatch_at_index("[1]: 2 (ACTUAL), 4 (DESIRED)") +
        "Max absolute difference among violations: 2\n"
        "Max relative difference among violations: 0.5\n"
        " ACTUAL: array([1, 2, 3])\n"
        " DESIRED: array([1, 4, 3])"
    ):
        compare(m1, expected=m2)


def test_masked_floats_within_tolerance_compare_equal():
    m1 = np.ma.MaskedArray([1.0 + 1e-9, 2.0], mask=[False, True])
    m2 = np.ma.MaskedArray([1.0, 5.0], mask=[False, True])
    compare(m1, expected=m2)


def test_masked_strict_requires_exact_floats():
    m1 = np.ma.MaskedArray([1.0 + 1e-9, 2.0], mask=[False, True])
    m2 = np.ma.MaskedArray([1.0, 5.0], mask=[False, True])
    with ShouldAssert(
        "\n"
        "Arrays are not equal\n"
        "\n"
        "Mismatched elements: 1 / 1 (100%)\n"
        + mismatch_at_index("[0]: 1.000000001 (ACTUAL), 1.0 (DESIRED)") +
        "Max absolute difference among violations: 1.00000008e-09\n"
        "Max relative difference among violations: 1.00000008e-09\n"
        " ACTUAL: array([1.])\n"
        " DESIRED: array([1.])"
    ):
        compare(m1, expected=m2, strict=True)
