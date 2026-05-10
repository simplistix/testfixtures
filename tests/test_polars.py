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
    with ShouldRaise(TypeError("the truth value of a DataFrame is ambiguous"
                               "\n\nHint: to check if a DataFrame contains any values,"
                               " use `is_empty()`.")):
        compare(df1, expected=df2)


def test_unequal_dataframes():
    df1 = pl.DataFrame({"a": [1, 2], "b": [3, 4]})
    df2 = pl.DataFrame({"a": [1, 2], "b": [3, 5]})
    with ShouldRaise(TypeError("the truth value of a DataFrame is ambiguous"
                               "\n\nHint: to check if a DataFrame contains any values,"
                               " use `is_empty()`.")):
        compare(df1, expected=df2)
