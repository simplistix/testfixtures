import pytest

pytest.importorskip("polars")

import polars as pl

import testfixtures.polars
from testfixtures import ShouldAssert, compare


def test_importable():
    compare(testfixtures.polars.polars.__name__, expected="polars")


def test_equal_dataframes():
    df1 = pl.DataFrame({"a": [1, 2], "b": [3, 4]})
    df2 = pl.DataFrame({"a": [1, 2], "b": [3, 4]})
    compare(df1, expected=df2)


def test_unequal_dataframes():
    df1 = pl.DataFrame({"a": [1, 2], "b": [3, 4]})
    df2 = pl.DataFrame({"a": [1, 2], "b": [3, 5]})
    with ShouldAssert(
        'DataFrames are different (value mismatch for column "b")\n'
        "[left]: shape: (2,)\n"
        "Series: 'b' [i64]\n"
        "[\n"
        "\t3\n"
        "\t5\n"
        "]\n"
        "[right]: shape: (2,)\n"
        "Series: 'b' [i64]\n"
        "[\n"
        "\t3\n"
        "\t4\n"
        "]"
    ):
        compare(df1, expected=df2)


def test_unequal_dataframes_in_dict_breadcrumb():
    df1 = pl.DataFrame({"a": [1]})
    df2 = pl.DataFrame({"a": [2]})
    with ShouldAssert(
        "dict not as expected:\n"
        "\n"
        "values differ:\n"
        "'foo': shape: (1, 1)\n"
        "┌─────┐\n"
        "│ a   │\n"
        "│ --- │\n"
        "│ i64 │\n"
        "╞═════╡\n"
        "│ 2   │\n"
        "└─────┘ (expected) != shape: (1, 1)\n"
        "┌─────┐\n"
        "│ a   │\n"
        "│ --- │\n"
        "│ i64 │\n"
        "╞═════╡\n"
        "│ 1   │\n"
        "└─────┘ (actual)\n"
        "\n"
        "While comparing ['foo']: DataFrames are different"
        ' (value mismatch for column "a")\n'
        "[left]: shape: (1,)\n"
        "Series: 'a' [i64]\n"
        "[\n"
        "\t2\n"
        "]\n"
        "[right]: shape: (1,)\n"
        "Series: 'a' [i64]\n"
        "[\n"
        "\t1\n"
        "]"
    ):
        compare({"foo": df1}, expected={"foo": df2})


def test_floats_within_tolerance_compare_equal():
    df1 = pl.DataFrame({"x": [1.0, 2.0]})
    df2 = pl.DataFrame({"x": [1.0 + 1e-9, 2.0]})
    compare(df1, expected=df2)


def test_strict_requires_exact_floats():
    df1 = pl.DataFrame({"x": [1.0, 2.0]})
    df2 = pl.DataFrame({"x": [1.0 + 1e-9, 2.0]})
    with ShouldAssert(
        'DataFrames are different (value mismatch for column "x")\n'
        "[left]: shape: (2,)\n"
        "Series: 'x' [f64]\n"
        "[\n"
        "\t1.0\n"
        "\t2.0\n"
        "]\n"
        "[right]: shape: (2,)\n"
        "Series: 'x' [f64]\n"
        "[\n"
        "\t1.0\n"
        "\t2.0\n"
        "]"
    ):
        compare(df1, expected=df2, strict=True)


def test_strict_exact_floats_compare_equal():
    df1 = pl.DataFrame({"x": [1.0, 2.0]})
    df2 = pl.DataFrame({"x": [1.0, 2.0]})
    compare(df1, expected=df2, strict=True)
