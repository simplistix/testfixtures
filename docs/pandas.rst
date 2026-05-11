Testing with Pandas
===================

.. note::

   To ensure you are using compatible versions, install with the ``testfixtures[pandas]`` extra.

.. invisible-code-block: python

    try:
        import pandas
    except ImportError:
        pandas = None

.. skip: start if(pandas is None, reason="No pandas installed")

When pandas is installed, a :func:`comparer <testfixtures.pandas.compare_dataframe>`
for :class:`pandas.DataFrame` is automatically
:ref:`registered <comparer-register>` with ``ignore_eq=True``. It hands off to
:func:`pandas.testing.assert_frame_equal`, so the diff output and tolerance
semantics are exactly those of pandas' own test helper. Passing ``strict=True``
to :func:`~testfixtures.compare` switches the underlying call to
``check_exact=True``.

Equal frames compare equal:

>>> import pandas as pd
>>> from testfixtures import compare
>>> df1 = pd.DataFrame({'a': [1]})
>>> df2 = pd.DataFrame({'a': [1]})
>>> compare(df1, expected=df2)

When frames differ inside a larger structure,
:func:`~testfixtures.compare`'s breadcrumbs still point at the location
of the difference:

>>> compare({'foo': df1}, expected={'foo': pd.DataFrame({'a': [2]})})
Traceback (most recent call last):
 ...
AssertionError: dict not as expected:
<BLANKLINE>
values differ:
'foo':    a
0  2 (expected) !=    a
0  1 (actual)
<BLANKLINE>
While comparing ['foo']: DataFrame.iloc[:, 0] (column name="a") are different
<BLANKLINE>
DataFrame.iloc[:, 0] (column name="a") values are different (100.0 %)
[index]: [0]
[left]:  [2]
[right]: [1]
At positional index 0, first diff: 2 != 1

Float comparisons use pandas' default ``rtol`` and ``atol``, so small
differences compare equal:

>>> fa = pd.DataFrame({'x': [1.0]})
>>> fb = pd.DataFrame({'x': [1.0 + 1e-9]})
>>> compare(fa, expected=fb)

Pass ``strict=True`` to require bitwise equality instead:

>>> compare(fa, expected=fb, strict=True)
Traceback (most recent call last):
 ...
AssertionError: DataFrame.iloc[:, 0] (column name="x") are different
<BLANKLINE>
DataFrame.iloc[:, 0] (column name="x") values are different (100.0 %)
[index]: [0]
[left]:  [1.000000001]
[right]: [1.0]
