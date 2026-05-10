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
    with ShouldRaise(ValueError("The truth value of a DataFrame is ambiguous."
                                " Use a.empty, a.bool(), a.item(), a.any() or a.all().")):
        compare(df1, expected=df2)


def test_unequal_dataframes():
    df1 = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    df2 = pd.DataFrame({"a": [1, 2], "b": [3, 5]})
    with ShouldRaise(ValueError("The truth value of a DataFrame is ambiguous."
                                " Use a.empty, a.bool(), a.item(), a.any() or a.all().")):
        compare(df1, expected=df2)
