import pytest

pytest.importorskip("pandas")

import testfixtures.pandas
from testfixtures import compare


def test_importable():
    compare(testfixtures.pandas.pandas.__name__, expected="pandas")
