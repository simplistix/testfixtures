"""
Cases where sharing an object changes what compare() reports, grouped by cause.

Each bug covers every combination of the axis values it lists, with ``None`` meaning
every value on that axis. The tests require exactly these cases to fail, so a bug that
covers too much, or too little, makes the suite fail.
"""
from dataclasses import dataclass

from .axes import Behaviour, Container, Mode, Pattern, Relation

ALL_MODES = None
NON_STRICT = frozenset({'trusted', 'ignore_unrelated', 'ignore_type', 'ignore_all'})
EQ_TRUSTED = frozenset({'trusted', 'ignore_unrelated'})
STRICT = frozenset({'strict'})

ON_Y = frozenset({'repeated_in_y', 'shared_across_sides_at_different_paths'})

KEEPS_GOING = frozenset({'dict', 'attributes'})

COMPARED_BY_IDENTITY = (
    'Once repeated, an object without __eq__ is compared by identity, not by attribute.'
)
ALREADY_SEEN_REACHES_EQ = (
    "Once repeated on the y side, the object reaches x's __eq__ wrapped in AlreadySeen, "
    'which it does not recognise. See issue 271.'
)
STRUCTURAL_EQUALITY_LOST = (
    'Once repeated, a list is compared with a tuple using ==, '
    'losing the element-wise equality found the first time.'
)
REPEAT_MAKES_EQ_RAISE = (
    'Dicts and attributes carry on past the first difference, so the repeat is reached, '
    'and the AlreadySeen wrapper makes __eq__ raise.'
)


@dataclass(frozen=True)
class KnownBug:
    reason: str
    behaviours: frozenset[str] | None
    relations: frozenset[str] | None
    patterns: frozenset[str] | None
    modes: frozenset[str] | None = ALL_MODES
    containers: frozenset[str] | None = None

    def covers(
            self,
            pattern: Pattern,
            container: Container,
            behaviour: Behaviour,
            relation: Relation,
            mode: Mode,
    ) -> bool:
        return all(
            values is None or value.name in values for values, value in (
                (self.patterns, pattern),
                (self.containers, container),
                (self.behaviours, behaviour),
                (self.relations, relation),
                (self.modes, mode),
            )
        )


def names(*names: str) -> frozenset[str]:
    return frozenset(names)


SHARING_BUGS = [
    KnownBug(
        COMPARED_BY_IDENTITY,
        behaviours=names('NoEq'),
        relations=names('equal'),
        patterns=ON_Y | {'repeated_in_x'},
    ),
    KnownBug(
        COMPARED_BY_IDENTITY,
        behaviours=names('EqAcceptsForeign'),
        relations=names('x_foreign'),
        patterns=names('shared_across_sides_at_different_paths'),
        modes=NON_STRICT,
    ),
    KnownBug(
        COMPARED_BY_IDENTITY,
        behaviours=names('EqAlwaysTrue'),
        relations=names('x_foreign', 'x_foreign_other_value'),
        patterns=names('shared_across_sides_at_different_paths'),
        modes=NON_STRICT,
    ),
    KnownBug(
        ALREADY_SEEN_REACHES_EQ,
        behaviours=names(
            'EqAcceptsForeign', 'EqAsymmetric', 'EqFalseForForeign', 'EqFalseyForForeign',
            'EqIgnoresDetail', 'EqRaisesForForeign',
        ),
        relations=names('equal'),
        patterns=ON_Y,
    ),
    KnownBug(
        ALREADY_SEEN_REACHES_EQ,
        behaviours=names(
            'EqAcceptsForeign', 'EqAsymmetric', 'EqFalseForForeign', 'EqFalseyForForeign',
            'EqIgnoresDetail', 'EqRaisesForForeign',
        ),
        relations=names('x_subclass', 'y_subclass'),
        patterns=ON_Y,
        modes=NON_STRICT,
    ),
    KnownBug(
        ALREADY_SEEN_REACHES_EQ,
        behaviours=names('EqAcceptsForeign'),
        relations=names('y_foreign'),
        patterns=ON_Y,
        modes=NON_STRICT,
    ),
    KnownBug(
        ALREADY_SEEN_REACHES_EQ,
        behaviours=names('EqAsymmetric'),
        relations=names('x_subclass_other_value'),
        patterns=ON_Y,
        modes=NON_STRICT,
    ),
    KnownBug(
        ALREADY_SEEN_REACHES_EQ,
        behaviours=names('EqAsymmetric'),
        relations=names('x_value_lower'),
        patterns=ON_Y,
        modes=EQ_TRUSTED,
    ),
    KnownBug(
        ALREADY_SEEN_REACHES_EQ,
        behaviours=names('EqIgnoresDetail'),
        relations=names('detail_differs'),
        patterns=ON_Y,
        modes=EQ_TRUSTED,
    ),
    KnownBug(
        STRUCTURAL_EQUALITY_LOST,
        behaviours=names('list'),
        relations=names('x_foreign'),
        patterns=names('repeated_in_both', 'repeated_in_y'),
        modes=NON_STRICT,
    ),
    KnownBug(
        STRUCTURAL_EQUALITY_LOST,
        behaviours=names('list'),
        relations=names('y_foreign'),
        patterns=names('repeated_in_both', 'repeated_in_x'),
        modes=NON_STRICT,
    ),
    KnownBug(
        REPEAT_MAKES_EQ_RAISE,
        behaviours=names('EqRaisesForForeign'),
        relations=names(
            'detail_differs', 'x_value_lower', 'x_value_higher',
            'x_subclass_other_value', 'y_subclass_other_value',
        ),
        patterns=ON_Y,
        containers=KEEPS_GOING,
    ),
    KnownBug(
        REPEAT_MAKES_EQ_RAISE,
        behaviours=names('EqRaisesForForeign'),
        relations=names('x_subclass', 'y_subclass', 'y_foreign', 'y_foreign_other_value'),
        patterns=ON_Y,
        modes=STRICT,
        containers=KEEPS_GOING,
    ),
    KnownBug(
        REPEAT_MAKES_EQ_RAISE,
        behaviours=names('EqRaisesForForeign'),
        relations=names('x_foreign', 'x_foreign_other_value'),
        patterns=names('repeated_in_y'),
        modes=STRICT,
        containers=KEEPS_GOING,
    ),
]


def sharing_bug(
        pattern: Pattern,
        container: Container,
        behaviour: Behaviour,
        relation: Relation,
        mode: Mode,
) -> str | None:
    for bug in SHARING_BUGS:
        if bug.covers(pattern, container, behaviour, relation, mode):
            return bug.reason
    return None
