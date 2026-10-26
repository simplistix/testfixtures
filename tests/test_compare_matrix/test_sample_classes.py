import pytest

from testfixtures import ShouldRaise, compare

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
)


def test_no_eq() -> None:
    s = NoEq(1)
    compare(s == s, expected=True)
    compare(NoEq(1) == NoEq(1), expected=False)


def test_eq_not_implemented_for_foreign() -> None:
    compare(EqNotImplementedForForeign(1) == EqNotImplementedForForeign(1), expected=True)
    compare(EqNotImplementedForForeign(1) == EqNotImplementedForForeign(1, 1), expected=False)
    compare(EqNotImplementedForForeign(1).__eq__(Foreign(1)), expected=NotImplemented)


def test_eq_false_for_foreign() -> None:
    compare(EqFalseForForeign(1) == EqFalseForForeign(1), expected=True)
    compare(EqFalseForForeign(1) == EqFalseForForeign(1, 1), expected=False)
    compare(EqFalseForForeign(1).__eq__(Foreign(1)), expected=False)


def test_eq_falsey_for_foreign() -> None:
    compare(EqFalseyForForeign(1) == EqFalseyForForeign(1), expected=True)
    compare(EqFalseyForForeign(1) == EqFalseyForForeign(1, 1), expected=False)
    result = EqFalseyForForeign(1).__eq__(Foreign(1))
    compare(type(result), expected=Falsey)
    compare(bool(result), expected=False)


def test_eq_raises_for_foreign() -> None:
    compare(EqRaisesForForeign(1) == EqRaisesForForeign(1), expected=True)
    compare(EqRaisesForForeign(1) == EqRaisesForForeign(1, 1), expected=False)
    with ShouldRaise(ForeignOperandError('EqRaisesForForeign(1, 0) == Foreign(1, 0)')):
        EqRaisesForForeign(1).__eq__(Foreign(1))


def test_eq_always_true() -> None:
    compare(EqAlwaysTrue(1) == EqAlwaysTrue(2, 1), expected=True)
    compare(EqAlwaysTrue(1).__eq__(Foreign(2)), expected=True)


def test_eq_ignores_detail() -> None:
    compare(EqIgnoresDetail(1) == EqIgnoresDetail(1, 1), expected=True)
    compare(EqIgnoresDetail(1) == EqIgnoresDetail(2), expected=False)
    compare(EqIgnoresDetail(1).__eq__(Foreign(1)), expected=False)


def test_eq_asymmetric() -> None:
    compare(EqAsymmetric(1) == EqAsymmetric(2), expected=True)
    compare(EqAsymmetric(2) == EqAsymmetric(1), expected=False)
    compare(EqAsymmetric(1) == EqAsymmetric(1, 1), expected=False)
    compare(EqAsymmetric(1).__eq__(Foreign(1)), expected=False)


def test_eq_accepts_foreign() -> None:
    compare(EqAcceptsForeign(1) == EqAcceptsForeign(1), expected=True)
    compare(EqAcceptsForeign(1) == EqAcceptsForeign(1, 1), expected=False)
    compare(EqAcceptsForeign(1).__eq__(Foreign(1)), expected=True)
    compare(EqAcceptsForeign(1).__eq__(Foreign(2)), expected=False)


@pytest.mark.parametrize('behaviour', BEHAVIOURS, ids=repr)
def test_subclass_and_foreign(behaviour: Behaviour) -> None:
    subclass = type(behaviour.make_subclass(1, 0))
    compare(issubclass(subclass, behaviour.type), expected=True)
    compare(subclass is behaviour.type, expected=False)
    compare(isinstance(behaviour.make_foreign(1, 0), behaviour.type), expected=False)


def test_falsey_repr() -> None:
    compare(repr(Falsey()), expected='Falsey()')


def test_holder_repr() -> None:
    compare(repr(Holder(NoEq(1), 2)), expected='Holder(a0=NoEq(1, 0), a1=2)')
