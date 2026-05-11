import pytest

pytest.importorskip("polars")

import polars as pl

import testfixtures.polars
from testfixtures import ShouldRaise, compare


def test_importable():
    compare(testfixtures.polars.polars.__name__, expected="polars")


def test_equal_dataframes():
    df1 = pl.DataFrame({"a": [1, 2], "b": [3, 4]})
    df2 = pl.DataFrame({"a": [1, 2], "b": [3, 4]})
    compare(df1, expected=df2)


def test_unequal_dataframes():
    df1 = pl.DataFrame({"a": [1, 2], "b": [3, 4]})
    df2 = pl.DataFrame({"a": [1, 2], "b": [3, 5]})
    with ShouldRaise(AssertionError, match='value mismatch for column "b"'):
        compare(df1, expected=df2)


def test_unequal_dataframes_in_dict_breadcrumb():
    df1 = pl.DataFrame({"a": [1]})
    df2 = pl.DataFrame({"a": [2]})
    with ShouldRaise(AssertionError, match=r"While comparing \['foo'\]"):
        compare({"foo": df1}, expected={"foo": df2})


def test_floats_within_tolerance_compare_equal():
    df1 = pl.DataFrame({"x": [1.0, 2.0]})
    df2 = pl.DataFrame({"x": [1.0 + 1e-9, 2.0]})
    compare(df1, expected=df2)


def test_strict_requires_exact_floats():
    df1 = pl.DataFrame({"x": [1.0, 2.0]})
    df2 = pl.DataFrame({"x": [1.0 + 1e-9, 2.0]})
    with ShouldRaise(AssertionError, match='value mismatch for column "x"'):
        compare(df1, expected=df2, strict=True)


def test_strict_exact_floats_compare_equal():
    df1 = pl.DataFrame({"x": [1.0, 2.0]})
    df2 = pl.DataFrame({"x": [1.0, 2.0]})
    compare(df1, expected=df2, strict=True)
