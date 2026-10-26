import itertools
from functools import cache

from .axes import (
    BEHAVIOURS, CONTAINERS, MODES, PATTERNS, RELATIONS,
    Behaviour, Container, Mode, Pattern, Relation, Result, build, check, problem, run,
)
from .known_bugs import sharing_bug
from .spec import SPEC, known_bug

Case = tuple[Pattern, Container, Behaviour, Relation, Mode]

CASES: list[Case] = list(itertools.product(PATTERNS, CONTAINERS, BEHAVIOURS, RELATIONS, MODES))


def case_id(case: Case) -> str:
    return '-'.join(axis.name for axis in case)


def result(case: Case, shared: bool) -> Result:
    pattern, container, behaviour, relation, mode = case
    return run(*build(pattern, container, relation, behaviour, shared), mode, behaviour)


@cache
def unshared(case: Case) -> Result:
    return result(case, shared=False)


def test_unshared() -> None:
    problems = {}
    for case in CASES:
        _, _, behaviour, relation, mode = case
        expected = SPEC[behaviour.name, relation.name, mode.name]
        found = problem(unshared(case), expected.outcome, known_bug(expected))
        if found:
            problems[case_id(case)] = found
    check(problems, {})


def test_shared() -> None:
    problems = {}
    for case in CASES:
        found = problem(result(case, shared=True), unshared(case).outcome, sharing_bug(*case))
        if found:
            problems[case_id(case)] = found
    check(problems, {})
