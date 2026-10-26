import itertools

from .axes import BEHAVIOURS, MODES, RELATIONS, check, problem, run
from .spec import EXPECTED_KEYS, SPEC, known_bug


def test_spec_covers_every_case() -> None:
    check(set(SPEC), EXPECTED_KEYS)


def test_bare() -> None:
    problems = {}
    for behaviour, relation, mode in itertools.product(BEHAVIOURS, RELATIONS, MODES):
        expected = SPEC[behaviour.name, relation.name, mode.name]
        result = run(relation.x(behaviour), relation.y(behaviour), mode, behaviour)
        found = problem(result, expected.outcome, known_bug(expected))
        if found:
            problems[f'{behaviour.name}-{relation.name}-{mode.name}'] = found
    check(problems, {})
