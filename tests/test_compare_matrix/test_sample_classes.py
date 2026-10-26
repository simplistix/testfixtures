import pytest

from testfixtures import ShouldRaise

from .axes import (
    BEHAVIOURS,
    Behaviour,
    EqAcceptsForeign,
    EqAlwaysTrue,
    EqAsymmetric,
    EqFalseForForeign,
    EqFalseyForForeign,
    EqIgnoresDetail,
    EqNotImplementedForForeign,
    EqRaisesForForeign,
    Falsey,
    Foreign,
    ForeignOperandError,
    Holder,
    NoEq,
    check,
)


def test_no_eq() -> None:
    s = NoEq(1)
    check(s == s, True)
    check(NoEq(1) == NoEq(1), False)


def test_eq_not_implemented_for_foreign() -> None:
    check(EqNotImplementedForForeign(1) == EqNotImplementedForForeign(1), True)
    check(EqNotImplementedForForeign(1) == EqNotImplementedForForeign(1, 1), False)
    check(EqNotImplementedForForeign(1).__eq__(Foreign(1)), NotImplemented)


def test_eq_false_for_foreign() -> None:
    check(EqFalseForForeign(1) == EqFalseForForeign(1), True)
    check(EqFalseForForeign(1) == EqFalseForForeign(1, 1), False)
    check(EqFalseForForeign(1).__eq__(Foreign(1)), False)


def test_eq_falsey_for_foreign() -> None:
    check(EqFalseyForForeign(1) == EqFalseyForForeign(1), True)
    check(EqFalseyForForeign(1) == EqFalseyForForeign(1, 1), False)
    result = EqFalseyForForeign(1).__eq__(Foreign(1))
    check(type(result), Falsey)
    check(bool(result), False)


def test_eq_raises_for_foreign() -> None:
    check(EqRaisesForForeign(1) == EqRaisesForForeign(1), True)
    check(EqRaisesForForeign(1) == EqRaisesForForeign(1, 1), False)
    with ShouldRaise(ForeignOperandError('EqRaisesForForeign(1, 0) == Foreign(1, 0)')):
        EqRaisesForForeign(1).__eq__(Foreign(1))


def test_eq_always_true() -> None:
    check(EqAlwaysTrue(1) == EqAlwaysTrue(2, 1), True)
    check(EqAlwaysTrue(1).__eq__(Foreign(2)), True)


def test_eq_ignores_detail() -> None:
    check(EqIgnoresDetail(1) == EqIgnoresDetail(1, 1), True)
    check(EqIgnoresDetail(1) == EqIgnoresDetail(2), False)
    check(EqIgnoresDetail(1).__eq__(Foreign(1)), False)


def test_eq_asymmetric() -> None:
    check(EqAsymmetric(1) == EqAsymmetric(2), True)
    check(EqAsymmetric(2) == EqAsymmetric(1), False)
    check(EqAsymmetric(1) == EqAsymmetric(1, 1), False)
    check(EqAsymmetric(1).__eq__(Foreign(1)), False)


def test_eq_accepts_foreign() -> None:
    check(EqAcceptsForeign(1) == EqAcceptsForeign(1), True)
    check(EqAcceptsForeign(1) == EqAcceptsForeign(1, 1), False)
    check(EqAcceptsForeign(1).__eq__(Foreign(1)), True)
    check(EqAcceptsForeign(1).__eq__(Foreign(2)), False)


@pytest.mark.parametrize('behaviour', BEHAVIOURS, ids=repr)
def test_subclass_and_foreign(behaviour: Behaviour) -> None:
    subclass = type(behaviour.make_subclass(1, 0))
    check(issubclass(subclass, behaviour.type), True)
    check(subclass is behaviour.type, False)
    check(isinstance(behaviour.make_foreign(1, 0), behaviour.type), False)


def test_falsey_repr() -> None:
    check(repr(Falsey()), 'Falsey()')


def test_holder_repr() -> None:
    check(repr(Holder(NoEq(1), 2)), 'Holder(a0=NoEq(1, 0), a1=2)')
