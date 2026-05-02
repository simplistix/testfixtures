import pytest

pytest.importorskip("polars")

import testfixtures.polars
from testfixtures import compare


def test_importable():
    compare(testfixtures.polars.polars.__name__, expected="polars")
