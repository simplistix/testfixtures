import pytest

pytest.importorskip("pandas")

import pandas as pd

import testfixtures.pandas
from testfixtures import ShouldAssert, compare


def test_importable():
    compare(testfixtures.pandas.pandas.__name__, expected="pandas")


def test_equal_dataframes():
    df1 = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    df2 = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    compare(df1, expected=df2)


def test_unequal_dataframes():
    df1 = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    df2 = pd.DataFrame({"a": [1, 2], "b": [3, 5]})
    with ShouldAssert(
        'DataFrame.iloc[:, 1] (column name="b") are different\n'
        "\n"
        'DataFrame.iloc[:, 1] (column name="b") values are different (50.0 %)\n'
        "[index]: [0, 1]\n"
        "[left]:  [3, 5]\n"
        "[right]: [3, 4]\n"
        "At positional index 1, first diff: 5 != 4"
    ):
        compare(df1, expected=df2)


def test_unequal_dataframes_in_dict_breadcrumb():
    df1 = pd.DataFrame({"a": [1]})
    df2 = pd.DataFrame({"a": [2]})
    with ShouldAssert(
        "dict not as expected:\n"
        "\n"
        "values differ:\n"
        "'foo':    a\n"
        "0  2 (expected) !=    a\n"
        "0  1 (actual)\n"
        "\n"
        'While comparing [\'foo\']: DataFrame.iloc[:, 0] (column name="a") are different\n'
        "\n"
        'DataFrame.iloc[:, 0] (column name="a") values are different (100.0 %)\n'
        "[index]: [0]\n"
        "[left]:  [2]\n"
        "[right]: [1]\n"
        "At positional index 0, first diff: 2 != 1"
    ):
        compare({"foo": df1}, expected={"foo": df2})


def test_floats_within_tolerance_compare_equal():
    df1 = pd.DataFrame({"x": [1.0, 2.0]})
    df2 = pd.DataFrame({"x": [1.0 + 1e-9, 2.0]})
    compare(df1, expected=df2)


def test_strict_requires_exact_floats():
    df1 = pd.DataFrame({"x": [1.0, 2.0]})
    df2 = pd.DataFrame({"x": [1.0 + 1e-9, 2.0]})
    with ShouldAssert(
        'DataFrame.iloc[:, 0] (column name="x") are different\n'
        "\n"
        'DataFrame.iloc[:, 0] (column name="x") values are different (50.0 %)\n'
        "[index]: [0, 1]\n"
        "[left]:  [1.000000001, 2.0]\n"
        "[right]: [1.0, 2.0]"
    ):
        compare(df1, expected=df2, strict=True)


def test_strict_exact_floats_compare_equal():
    df1 = pd.DataFrame({"x": [1.0, 2.0]})
    df2 = pd.DataFrame({"x": [1.0, 2.0]})
    compare(df1, expected=df2, strict=True)
