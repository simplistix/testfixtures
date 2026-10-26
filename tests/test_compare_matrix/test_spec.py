import itertools

import pytest

from .axes import BEHAVIOURS, MODES, RELATIONS, Behaviour, Mode, Relation, check, run
from .spec import EXPECTED_KEYS, SPEC, marks_for


def test_spec_covers_every_case() -> None:
    check(set(SPEC), EXPECTED_KEYS)


@pytest.mark.parametrize(('behaviour', 'relation', 'mode'), [
    pytest.param(
        behaviour, relation, mode,
        id=f'{behaviour.name}-{relation.name}-{mode.name}',
        marks=marks_for(SPEC[behaviour.name, relation.name, mode.name]),
    )
    for behaviour, relation, mode in itertools.product(BEHAVIOURS, RELATIONS, MODES)
])
def test_bare(behaviour: Behaviour, relation: Relation, mode: Mode) -> None:
    result = run(relation.x(behaviour), relation.y(behaviour), mode, behaviour)
    expected = SPEC[behaviour.name, relation.name, mode.name]
    check(result.outcome, expected.outcome, result.message)
