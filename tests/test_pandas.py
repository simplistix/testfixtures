import pytest

pytest.importorskip("pandas")

import pandas as pd

import testfixtures.pandas
from testfixtures import ShouldRaise, compare


def test_importable():
    compare(testfixtures.pandas.pandas.__name__, expected="pandas")


def test_equal_dataframes():
    df1 = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    df2 = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    compare(df1, expected=df2)


def test_unequal_dataframes():
    df1 = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    df2 = pd.DataFrame({"a": [1, 2], "b": [3, 5]})
    with ShouldRaise(AssertionError, match='column name="b"'):
        compare(df1, expected=df2)


def test_unequal_dataframes_in_dict_breadcrumb():
    df1 = pd.DataFrame({"a": [1]})
    df2 = pd.DataFrame({"a": [2]})
    with ShouldRaise(AssertionError, match=r"While comparing \['foo'\]"):
        compare({"foo": df1}, expected={"foo": df2})


def test_floats_within_tolerance_compare_equal():
    df1 = pd.DataFrame({"x": [1.0, 2.0]})
    df2 = pd.DataFrame({"x": [1.0 + 1e-9, 2.0]})
    compare(df1, expected=df2)


def test_strict_requires_exact_floats():
    df1 = pd.DataFrame({"x": [1.0, 2.0]})
    df2 = pd.DataFrame({"x": [1.0 + 1e-9, 2.0]})
    with ShouldRaise(AssertionError, match='column name="x"'):
        compare(df1, expected=df2, strict=True)


def test_strict_exact_floats_compare_equal():
    df1 = pd.DataFrame({"x": [1.0, 2.0]})
    df2 = pd.DataFrame({"x": [1.0, 2.0]})
    compare(df1, expected=df2, strict=True)
