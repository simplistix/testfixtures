"""
Tools for helping to test applications that use NumPy.
"""
from typing import TYPE_CHECKING

import numpy as numpy
from numpy import ndarray
from numpy.ma import MaskedArray, getmaskarray
from numpy.testing import assert_allclose, assert_array_equal

if TYPE_CHECKING:
    from .comparing import CompareContext

INEXACT_KINDS = 'fc'
# The tolerances used by the pandas and polars frame comparers, rather than
# assert_allclose's tighter defaults, so float semantics agree across all three:
RTOL = 1e-5
ATOL = 1e-8


def compare_ndarray(x: ndarray, y: ndarray, context: 'CompareContext') -> str | None:
    """
    Returns a textual description of the differences between two
    :class:`numpy.ndarray` instances, as reported by
    :func:`numpy.testing.assert_allclose` for float and complex arrays
    or :func:`numpy.testing.assert_array_equal` for arrays of any other
    :class:`dtype <numpy.dtype>`.

    Shape and dtype must always match: there is no broadcasting and an
    ``int32`` array is never equal to an ``int64`` one. NaNs in matching
    positions compare equal.

    When ``strict=True`` is passed to :func:`~testfixtures.compare`,
    float and complex values must be exactly equal; otherwise ``rtol=1e-5``
    and ``atol=1e-8`` apply, matching the pandas and polars comparers.
    """
    try:
        if x.dtype.kind in INEXACT_KINDS and not context.strict:
            assert_allclose(y, x, rtol=RTOL, atol=ATOL, strict=True)
        else:
            assert_array_equal(y, x, strict=True)
    except AssertionError as e:
        return str(e)
    return None


def compare_masked_array(x: MaskedArray, y: MaskedArray, context: 'CompareContext') -> str | None:
    """
    Returns a textual description of the differences between two
    :class:`numpy.ma.MaskedArray` instances.

    Masks are part of the data, so they must match exactly regardless of
    other options; data under masked positions is ignored. The unmasked
    data is then compared as described for
    :func:`~testfixtures.numpy.compare_ndarray`.
    """
    masks = compare_ndarray(getmaskarray(x), getmaskarray(y), context)
    if masks is not None:
        return 'masks differ: ' + masks
    return compare_ndarray(x.compressed(), y.compressed(), context)
