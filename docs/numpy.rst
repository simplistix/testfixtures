Testing with NumPy
==================

.. note::

   To ensure you are using compatible versions, install with the ``testfixtures[numpy]`` extra.

.. invisible-code-block: python

    try:
        import numpy
    except ImportError:
        numpy = None

.. skip: start if(numpy is None, reason="No numpy installed")

When numpy is installed, :func:`comparers <testfixtures.numpy.compare_ndarray>`
for :class:`numpy.ndarray` and :class:`numpy.ma.MaskedArray` are automatically
:ref:`registered <comparer-register>` with ``ignore_eq=True``. They hand off to
:func:`numpy.testing.assert_allclose` for float and complex arrays and
:func:`numpy.testing.assert_array_equal` for arrays of any other
:class:`dtype <numpy.dtype>`, so the diff output is that of numpy's own
test helpers.

Shape and dtype must always match: there is no broadcasting and an ``int32``
array is never equal to an ``int64`` one. NaNs in matching positions compare
equal. numpy scalars need none of this: their ``==`` returns a real
:class:`bool`, so they already work with :func:`~testfixtures.compare`.

Equal arrays compare equal:

>>> import numpy as np
>>> from testfixtures import compare
>>> compare(np.array([1, 2, 3]), expected=np.array([1, 2, 3]))

When arrays differ, numpy's excellent summaries are used:

>>> compare(np.array([1., 2., 3.]), expected=np.array([1., 2.5, 3.]))
Traceback (most recent call last):
 ...
AssertionError: ...
Not equal to tolerance rtol=1e-05, atol=1e-08
<BLANKLINE>
Mismatched elements: 1 / 3 (33.3%)...
Max absolute difference among violations: 0.5
Max relative difference among violations: 0.2
 ACTUAL: array([1., 2., 3.])
 DESIRED: array([1. , 2.5, 3. ])

When arrays differ inside a larger structure,
:func:`~testfixtures.compare`'s breadcrumbs still point at the location
of the difference:

>>> compare({'foo': np.array([1])}, expected={'foo': np.array([2])})
Traceback (most recent call last):
 ...
AssertionError: dict not as expected:
<BLANKLINE>
values differ:
'foo': array([2]) (expected) != array([1]) (actual)
<BLANKLINE>
While comparing ['foo']: ...
Arrays are not equal
<BLANKLINE>
Mismatched elements: 1 / 1 (100%)...
Max absolute difference among violations: 1
Max relative difference among violations: 0.5
 ACTUAL: array([1])
 DESIRED: array([2])

Float and complex arrays compare equal within ``rtol=1e-5`` and ``atol=1e-8``,
matching the pandas and polars comparers rather than the tighter defaults of
:func:`numpy.testing.assert_allclose`:

>>> fa = np.array([1.0 + 1e-9, 2.0])
>>> fb = np.array([1.0, 2.0])
>>> compare(fa, expected=fb)

Pass ``strict=True`` to require bitwise equality instead:

>>> compare(fa, expected=fb, strict=True)
Traceback (most recent call last):
 ...
AssertionError: ...
Arrays are not equal
<BLANKLINE>
Mismatched elements: 1 / 2 (50%)...
Max absolute difference among violations: 1.00000008e-09
Max relative difference among violations: 1.00000008e-09
 ACTUAL: array([1., 2.])
 DESIRED: array([1., 2.])

Masked arrays
-------------

For :class:`numpy.ma.MaskedArray`, the mask is part of the data, much as
nulls are in a dataframe: masks must match exactly regardless of other
options, while data under matching masked positions is ignored:

>>> m1 = np.ma.MaskedArray([1, 2, 3], mask=[False, True, False])
>>> m2 = np.ma.MaskedArray([1, 9, 3], mask=[False, True, False])
>>> compare(m1, expected=m2)

>>> compare(m1, expected=np.ma.MaskedArray([1, 2, 3]))
Traceback (most recent call last):
 ...
AssertionError: masks differ: ...
Arrays are not equal
<BLANKLINE>
Mismatched elements: 1 / 3 (33.3%)...
 ACTUAL: array([False,  True, False])
 DESIRED: array([False, False, False])
