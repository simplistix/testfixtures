import pytest

pytest.importorskip("structlog")

import testfixtures.structlog
from testfixtures import compare


def test_importable():
    compare(testfixtures.structlog.structlog.__name__, expected="structlog")
