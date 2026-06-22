import pytest

pytest.importorskip("pydantic")

import testfixtures.pydantic
from testfixtures import compare


def test_importable():
    compare(testfixtures.pydantic.pydantic.__name__, expected="pydantic")
