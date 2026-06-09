# Tests that ensure compare and Comparison work correctly in strictly type checked environments
import re
from collections import OrderedDict
from dataclasses import dataclass
from uuid import UUID, uuid4

from testfixtures import compare, Comparison
from testfixtures.comparison import like, sequence, contains, unordered, mapping


@dataclass
class SampleClass:
    x: int
    y: str


class OtherClass:
    pass


@dataclass
class ListCollection:
    items: list[SampleClass]


@dataclass
class TupleCollection:
    items: tuple[SampleClass, ...]


@dataclass
class DictCollection:
    items: dict[str, SampleClass]


@dataclass
class OrderedDictCollection:
    items: "OrderedDict[str, SampleClass]"


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


def test_uuid_already_seen_like():
    comparison = Comparison(UUID)
    uuid = uuid4()
    compare(uuid, expected=like(UUID))


def test_like_str_pattern() -> None:
    expected: str = like(r'on \d+')
    compare(expected, actual='on 40220')


def test_like_compiled_pattern() -> None:
    expected: str = like(re.compile(r'on \d+'))
    compare(expected, actual='on 40220')


class TestSequence:
    def test_minimal(self) -> None:
        actual = ListCollection([SampleClass(1, '2')])
        compare(actual, expected=ListCollection(sequence()([SampleClass(1, '2')])))

    def test_maximal(self) -> None:
        actual = ListCollection(
            [SampleClass(1, 'x'), SampleClass(2, 'x'), SampleClass(3, 'x')]
        )
        compare(
            actual,
            expected=ListCollection(
                sequence(partial=True, ordered=False, recursive=False)(
                    [
                        SampleClass(3, 'x'),
                        SampleClass(2, 'x'),
                    ],
                )
            ),
        )

    def test_minimal_type_override(self) -> None:
        actual = TupleCollection((SampleClass(1, '2'),))
        compare(
            actual,
            expected=TupleCollection(
                sequence(returns=tuple[SampleClass, ...])([SampleClass(1, '2')])
            ),
        )

    def test_maximal_type_override(self) -> None:
        actual = TupleCollection(
            (
                SampleClass(1, 'x'),
                SampleClass(2, 'x'),
                SampleClass(3, 'x'),
            )
        )
        compare(
            actual,
            expected=TupleCollection(
                sequence(
                    partial=True,
                    ordered=False,
                    recursive=False,
                    returns=tuple[SampleClass, ...],
                )(
                    [
                        SampleClass(3, 'x'),
                        SampleClass(2, 'x'),
                    ]
                )
            ),
        )


class TestContains:
    def test_it(self) -> None:
        actual = ListCollection([SampleClass(1, "2"), SampleClass(3, "4")])
        compare(actual, expected=ListCollection(contains([SampleClass(1, "2")])))

    def test_type_override(self) -> None:
        actual = TupleCollection((SampleClass(1, "2"), SampleClass(3, "4")))
        compare(
            actual,
            expected=TupleCollection(
                contains([SampleClass(1, "2")], returns=tuple[SampleClass, ...])
            ),
        )


class TestUnordered:
    def test_it(self) -> None:
        actual = ListCollection([SampleClass(2, "x"), SampleClass(1, "x")])
        compare(
            actual,
            expected=ListCollection(
                unordered([SampleClass(1, "x"), SampleClass(2, "x")])
            ),
        )

    def test_type_override(self) -> None:
        actual = TupleCollection((SampleClass(2, "x"), SampleClass(1, "x")))
        compare(
            actual,
            expected=TupleCollection(
                unordered(
                    [SampleClass(1, "x"), SampleClass(2, "x")],
                    returns=tuple[SampleClass, ...],
                )
            ),
        )


class TestMapping:
    def test_it(self) -> None:
        actual = DictCollection({"a": SampleClass(1, "2"), "b": SampleClass(3, "4")})
        compare(
            actual,
            expected=DictCollection(mapping(partial=True)({"a": SampleClass(1, "2")})),
        )

    def test_type_override(self) -> None:
        actual = OrderedDictCollection(OrderedDict(a=SampleClass(1, "2")))
        compare(
            actual,
            expected=OrderedDictCollection(
                mapping(returns=OrderedDict[str, SampleClass])(
                    {"a": SampleClass(1, "2")}
                )
            ),
        )
