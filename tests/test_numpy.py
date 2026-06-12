import pytest

pytest.importorskip("numpy")

import testfixtures.numpy
from testfixtures import compare


def test_importable():
    compare(testfixtures.numpy.numpy.__name__, expected="numpy")
