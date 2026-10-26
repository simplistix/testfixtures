"""
The axes along which the compare() matrix varies:

- modes: how ``__eq__`` is treated, from trusted through ignored to strict.
- behaviours: how a type's ``__eq__`` behaves, particularly towards foreign operands.
- relations: how the two objects being compared relate to each other.
- patterns and containers: where objects are shared and what holds them.
"""
from dataclasses import dataclass
from typing import Any, Callable

from testfixtures import compare


class ForeignOperandError(Exception):
    pass


class Falsey:
    """
    A falsey result that is not ``False``.
    """

    def __bool__(self) -> bool:
        return False

    def __repr__(self) -> str:
        return 'Falsey()'


class Sample:
    """
    The base for the sample classes, which only differ in how ``__eq__`` behaves.
    A complete ``__eq__`` compares both ``value`` and ``detail``.
    """

    def __init__(self, value: int, detail: int = 0) -> None:
        self.value = value
        self.detail = detail

    def __repr__(self) -> str:
        return f'{type(self).__name__}({self.value}, {self.detail})'

    def same_as(self, other: 'Sample') -> bool:
        return (self.value, self.detail) == (other.value, other.detail)


class Foreign(Sample):
    """
    An unrelated type carrying the same data as the samples, with no ``__eq__`` of its own.
    """


class NoEq(Sample):
    pass


class EqNotImplementedForForeign(Sample):
    def __eq__(self, other: object) -> Any:
        if not isinstance(other, EqNotImplementedForForeign):
            return NotImplemented
        return self.same_as(other)


class EqFalseForForeign(Sample):
    def __eq__(self, other: object) -> bool:
        return isinstance(other, EqFalseForForeign) and self.same_as(other)


class EqFalseyForForeign(Sample):
    def __eq__(self, other: object) -> Any:
        if not isinstance(other, EqFalseyForForeign):
            return Falsey()
        return self.same_as(other)


class EqRaisesForForeign(Sample):
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, EqRaisesForForeign):
            raise ForeignOperandError(f'{self!r} == {other!r}')
        return self.same_as(other)


class EqAlwaysTrue(Sample):
    def __eq__(self, other: object) -> bool:
        return True


class EqIgnoresDetail(Sample):
    def __eq__(self, other: object) -> bool:
        return isinstance(other, EqIgnoresDetail) and self.value == other.value


class EqAsymmetric(Sample):
    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, EqAsymmetric)
            and self.value <= other.value
            and self.detail == other.detail
        )


class EqAcceptsForeign(Sample):
    def __eq__(self, other: object) -> bool:
        return isinstance(other, (EqAcceptsForeign, Foreign)) and self.same_as(other)


class SubList(list[int]):
    pass


class SubDict(dict[str, int]):
    pass


@dataclass(frozen=True)
class Behaviour:
    name: str
    type: type
    make: Callable[[int, int], Any]
    make_subclass: Callable[[int, int], Any]
    make_foreign: Callable[[int, int], Any]

    def __repr__(self) -> str:
        return self.name


def sample_behaviour(class_: type[Sample]) -> Behaviour:
    subclass = type(f'{class_.__name__}Subclass', (class_,), {})
    return Behaviour(class_.__name__, class_, class_, subclass, Foreign)


BEHAVIOURS = [
    sample_behaviour(NoEq),
    sample_behaviour(EqNotImplementedForForeign),
    sample_behaviour(EqFalseForForeign),
    sample_behaviour(EqFalseyForForeign),
    sample_behaviour(EqRaisesForForeign),
    sample_behaviour(EqAlwaysTrue),
    sample_behaviour(EqIgnoresDetail),
    sample_behaviour(EqAsymmetric),
    sample_behaviour(EqAcceptsForeign),
    Behaviour(
        'list', list,
        make=lambda value, detail: [value, detail],
        make_subclass=lambda value, detail: SubList([value, detail]),
        make_foreign=lambda value, detail: (value, detail),
    ),
    Behaviour(
        'dict', dict,
        make=lambda value, detail: {'value': value, 'detail': detail},
        make_subclass=lambda value, detail: SubDict(value=value, detail=detail),
        make_foreign=Foreign,
    ),
]


@dataclass(frozen=True)
class Relation:
    name: str
    x: Callable[[Behaviour], Any]
    y: Callable[[Behaviour], Any]

    def __repr__(self) -> str:
        return self.name


RELATIONS = [
    Relation('equal', lambda b: b.make(1, 0), lambda b: b.make(1, 0)),
    Relation('x_value_lower', lambda b: b.make(1, 0), lambda b: b.make(2, 0)),
    Relation('x_value_higher', lambda b: b.make(2, 0), lambda b: b.make(1, 0)),
    Relation('detail_differs', lambda b: b.make(1, 0), lambda b: b.make(1, 1)),
    Relation('x_subclass', lambda b: b.make_subclass(1, 0), lambda b: b.make(1, 0)),
    Relation('y_subclass', lambda b: b.make(1, 0), lambda b: b.make_subclass(1, 0)),
    Relation('x_foreign', lambda b: b.make_foreign(1, 0), lambda b: b.make(1, 0)),
    Relation('y_foreign', lambda b: b.make(1, 0), lambda b: b.make_foreign(1, 0)),
    Relation('x_subclass_other_value', lambda b: b.make_subclass(1, 0), lambda b: b.make(2, 0)),
    Relation('y_subclass_other_value', lambda b: b.make(1, 0), lambda b: b.make_subclass(2, 0)),
    Relation('x_foreign_other_value', lambda b: b.make_foreign(1, 0), lambda b: b.make(2, 0)),
    Relation('y_foreign_other_value', lambda b: b.make(1, 0), lambda b: b.make_foreign(2, 0)),
]


class Unrelated:
    """
    Never compared: ignoring its ``__eq__`` only switches on per-type ``ignore_eq`` handling.
    """


@dataclass(frozen=True)
class Mode:
    name: str
    column: str
    kw: Callable[[Behaviour], dict[str, Any]]

    def __repr__(self) -> str:
        return self.name


MODES = [
    Mode('trusted', 'trusted', lambda b: {}),
    Mode('ignore_unrelated', 'unrelated', lambda b: {'ignore_eq': Unrelated}),
    Mode('ignore_type', 'type', lambda b: {'ignore_eq': b.type}),
    Mode('ignore_all', 'all', lambda b: {'ignore_eq': True}),
    Mode('strict', 'strict', lambda b: {'strict': True}),
]

# Outcomes of a comparison:
EQUAL = '=='
NOT_EQUAL = '!='
RAISES = 'raise'


@dataclass(frozen=True)
class Result:
    outcome: str
    message: str | None = None


def run(x: Any, y: Any, mode: Mode, behaviour: Behaviour) -> Result:
    try:
        compare(x=x, y=y, **mode.kw(behaviour))
    except AssertionError as e:
        return Result(NOT_EQUAL, str(e))
    except ForeignOperandError as e:
        return Result(RAISES, str(e))
    return Result(EQUAL)


Ref = Callable[[str], Any]


@dataclass(frozen=True)
class Pattern:
    """
    Where objects are shared. ``build`` is passed ``X`` and ``Y``, which return the
    relation's x-side and y-side objects for a key. When sharing, the same key returns
    the same object; otherwise every call returns a fresh one.
    """
    name: str
    build: Callable[[Ref, Ref], tuple[list[Any], list[Any]]]

    def __repr__(self) -> str:
        return self.name


PATTERNS = [
    Pattern('nothing_repeated', lambda X, Y: ([X('a')], [Y('b')])),
    Pattern('repeated_in_x', lambda X, Y: ([X('a'), X('a')], [Y('b'), Y('c')])),
    Pattern('repeated_in_y', lambda X, Y: ([X('a'), X('b')], [Y('c'), Y('c')])),
    Pattern('repeated_in_both', lambda X, Y: ([X('a'), X('a')], [Y('b'), Y('b')])),
    Pattern('shared_across_sides', lambda X, Y: ([X('s'), X('a')], [X('s'), Y('b')])),
    Pattern(
        'shared_across_sides_at_different_paths',
        lambda X, Y: ([X('s'), X('a')], [Y('b'), X('s')]),
    ),
]


class Holder:
    def __init__(self, *items: Any) -> None:
        for i, item in enumerate(items):
            setattr(self, f'a{i}', item)

    def __repr__(self) -> str:
        attrs = ', '.join(f'{name}={value!r}' for name, value in vars(self).items())
        return f'Holder({attrs})'


def nest(items: list[Any]) -> list[Any]:
    head, *tail = items
    return [head, nest(tail)] if tail else [head]


@dataclass(frozen=True)
class Container:
    name: str
    wrap: Callable[[list[Any]], Any]

    def __repr__(self) -> str:
        return self.name


CONTAINERS = [
    Container('list', lambda items: items),
    Container('dict', lambda items: {f'k{i}': item for i, item in enumerate(items)}),
    Container('attributes', lambda items: Holder(*items)),
    Container('tuples', lambda items: [(item,) for item in items]),
    Container('nested', nest),
]


def build(
        pattern: Pattern,
        container: Container,
        relation: Relation,
        behaviour: Behaviour,
        shared: bool,
) -> tuple[Any, Any]:
    made: dict[tuple[str, str], Any] = {}

    def ref(side: str, make: Callable[[Behaviour], Any]) -> Ref:
        def get(key: str) -> Any:
            if not shared:
                return make(behaviour)
            if (side, key) not in made:
                made[side, key] = make(behaviour)
            return made[side, key]
        return get

    x_items, y_items = pattern.build(ref('x', relation.x), ref('y', relation.y))
    return container.wrap(x_items), container.wrap(y_items)
