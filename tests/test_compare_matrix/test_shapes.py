import itertools

import pytest

from testfixtures import compare

from .axes import (
    BEHAVIOURS, CONTAINERS, MODES, PATTERNS, RELATIONS,
    Behaviour, Container, Mode, Pattern, Relation, build, run,
)
from .known_bugs import SHARING_BUGS
from .spec import SPEC, marks_for

CASES = list(itertools.product(PATTERNS, CONTAINERS, BEHAVIOURS, RELATIONS, MODES))
AXES = ('pattern', 'container', 'behaviour', 'relation', 'mode')


def case_id(*axes: Pattern | Container | Behaviour | Relation | Mode) -> str:
    return '-'.join(axis.name for axis in axes)


def sharing_marks(
        pattern: Pattern,
        container: Container,
        behaviour: Behaviour,
        relation: Relation,
        mode: Mode,
) -> list[pytest.MarkDecorator]:
    return [
        pytest.mark.xfail(strict=True, reason=bug.reason)
        for bug in SHARING_BUGS
        if bug.covers(pattern, container, behaviour, relation, mode)
    ]


@pytest.mark.parametrize(AXES, [
    pytest.param(
        *case, id=case_id(*case), marks=marks_for(SPEC[case[2].name, case[3].name, case[4].name])
    )
    for case in CASES
])
def test_unshared(
        pattern: Pattern,
        container: Container,
        behaviour: Behaviour,
        relation: Relation,
        mode: Mode,
) -> None:
    result = run(*build(pattern, container, relation, behaviour, shared=False), mode, behaviour)
    expected = SPEC[behaviour.name, relation.name, mode.name]
    compare(result.outcome, expected=expected.outcome, suffix=result.message)


@pytest.mark.parametrize(AXES, [
    pytest.param(*case, id=case_id(*case), marks=sharing_marks(*case))
    for case in CASES
])
def test_shared(
        pattern: Pattern,
        container: Container,
        behaviour: Behaviour,
        relation: Relation,
        mode: Mode,
) -> None:
    unshared = run(*build(pattern, container, relation, behaviour, shared=False), mode, behaviour)
    shared = run(*build(pattern, container, relation, behaviour, shared=True), mode, behaviour)
    compare(shared.outcome, expected=unshared.outcome, suffix=shared.message)
