import pytest

pytest.importorskip("pydantic")

from pydantic import BaseModel, PrivateAttr

import testfixtures.pydantic
from testfixtures import ShouldAssert, compare
from testfixtures.comparing import registry
from testfixtures.pydantic import compare_basemodel


class Point(BaseModel):
    x: int
    y: int


class Session(BaseModel):
    user: str
    _cache: dict = PrivateAttr(default_factory=dict)


class NamedPoint(BaseModel):
    name: str
    x: int
    y: int


class Segment(BaseModel):
    start: Point
    end: Point


def test_importable():
    compare(testfixtures.pydantic.pydantic.__name__, expected="pydantic")


def test_equal_models():
    compare(Point(x=1, y=2), expected=Point(x=1, y=2))


def test_private_attributes_ignored():
    s1 = Session(user='chris')
    s2 = Session(user='chris')
    s1._cache['token'] = 'abc'
    compare(s1, expected=s2)


def test_comparer_in_limited_registry():
    s1 = Session(user='chris')
    s2 = Session(user='chris')
    s1._cache['token'] = 'abc'
    with registry({Session: compare_basemodel}):
        compare(s1, expected=s2)


def test_unequal_models():
    with ShouldAssert(
        "Point not as expected:\n"
        "\n"
        "attributes same:\n"
        "['x']\n"
        "\n"
        "attributes differ:\n"
        "'y': 3 (expected) != 2 (actual)"
    ):
        compare(Point(x=1, y=2), expected=Point(x=1, y=3))


def test_models_of_different_types():
    with ShouldAssert(
        "not equal:\n"
        "NamedPoint(name='p', x=1, y=2) (expected)\n"
        "Point(x=1, y=2) (actual)"
    ):
        compare(Point(x=1, y=2), expected=NamedPoint(name="p", x=1, y=2))


def test_unequal_models_in_dict_breadcrumb():
    with ShouldAssert(
        "dict not as expected:\n"
        "\n"
        "values differ:\n"
        "'foo': Point(x=1, y=3) (expected) != Point(x=1, y=2) (actual)\n"
        "\n"
        "While comparing ['foo']: Point not as expected:\n"
        "\n"
        "attributes same:\n"
        "['x']\n"
        "\n"
        "attributes differ:\n"
        "'y': 3 (expected) != 2 (actual)"
    ):
        compare({"foo": Point(x=1, y=2)}, expected={"foo": Point(x=1, y=3)})


def test_nested_models():
    with ShouldAssert(
        "Segment not as expected:\n"
        "\n"
        "attributes same:\n"
        "['start']\n"
        "\n"
        "attributes differ:\n"
        "'end': Point(x=3, y=5) (expected) != Point(x=3, y=4) (actual)\n"
        "\n"
        "While comparing .end: Point not as expected:\n"
        "\n"
        "attributes same:\n"
        "['x']\n"
        "\n"
        "attributes differ:\n"
        "'y': 5 (expected) != 4 (actual)"
    ):
        compare(
            Segment(start=Point(x=1, y=2), end=Point(x=3, y=4)),
            expected=Segment(start=Point(x=1, y=2), end=Point(x=3, y=5)),
        )
