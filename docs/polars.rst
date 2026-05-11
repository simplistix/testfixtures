Testing with Polars
===================

.. note::

   To ensure you are using compatible versions, install with the ``testfixtures[polars]`` extra.

.. invisible-code-block: python

    try:
        import polars
    except ImportError:
        polars = None

.. skip: start if(polars is None, reason="No polars installed")

When polars is installed, a :func:`comparer <testfixtures.polars.compare_dataframe>`
for ``polars.DataFrame`` is automatically
:ref:`registered <comparer-register>` with ``ignore_eq=True``. It hands off to
:func:`polars.testing.assert_frame_equal`, so the diff output and tolerance
semantics are exactly those of polars' own test helper. Passing ``strict=True``
to :func:`~testfixtures.compare` switches the underlying call to
``check_exact=True``.

Equal frames compare equal:

>>> import polars as pl
>>> from testfixtures import compare
>>> df1 = pl.DataFrame({'a': [1]})
>>> df2 = pl.DataFrame({'a': [1]})
>>> compare(df1, expected=df2)

When frames differ inside a larger structure,
:func:`~testfixtures.compare`'s breadcrumbs still point at the location
of the difference:

>>> compare({'foo': df1}, expected={'foo': pl.DataFrame({'a': [2]})})
Traceback (most recent call last):
 ...
AssertionError: dict not as expected:
<BLANKLINE>
values differ:
'foo': shape: (1, 1)
...
While comparing ['foo']: DataFrames are different (value mismatch for column "a")
[left]: shape: (1,)
Series: 'a' [i64]
[
	2
]
[right]: shape: (1,)
Series: 'a' [i64]
[
	1
]

Float comparisons use polars' default ``rel_tol`` and ``abs_tol``, so small
differences compare equal:

>>> fa = pl.DataFrame({'x': [1.0]})
>>> fb = pl.DataFrame({'x': [1.0 + 1e-9]})
>>> compare(fa, expected=fb)

Pass ``strict=True`` to require bitwise equality instead:

>>> compare(fa, expected=fb, strict=True)
Traceback (most recent call last):
 ...
AssertionError: DataFrames are different (value mismatch for column "x")
[left]: shape: (1,)
Series: 'x' [f64]
[
	1.0
]
[right]: shape: (1,)
Series: 'x' [f64]
[
	1.0
]
