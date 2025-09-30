# Tests that ensure compare and Comparison work correctly in strictly type checked environments
from dataclasses import dataclass

from testfixtures import compare, Comparison
from testfixtures.comparison import like


@dataclass
class SampleClass:
    x: int
    y: str


class OtherClass:
    pass

def test_simple_compare() -> None:
    compare(SampleClass(1, '2'), expected=SampleClass(1, '2'))


def test_comparison_bad_typing_in_list() -> None:
    expected: list[SampleClass] = [
        Comparison(SampleClass, x=1, partial=True)  # type: ignore[list-item]
    ]
    compare(expected, actual=[SampleClass(1, '2')])


def test_comparison_via_like_in_list() -> None:
    expected: list[SampleClass] = [like(SampleClass, x=1)]
    compare(expected, actual=[SampleClass(1, '2')])


def test_comparison_via_like_in_assert() -> None:
    expected: SampleClass = like(SampleClass)
    assert expected == SampleClass(1, '2')
    assert expected == SampleClass(3, '4')
    assert expected != SampleClass
    assert expected != OtherClass()
