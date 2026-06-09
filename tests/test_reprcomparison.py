import re

from testfixtures import ReprComparison, ShouldRaise, compare


class AClass:
    def __repr__(self):
        return '<AClass>'


class BClass:
    def __repr__(self):
        return '<AClass>'


def test_equal_yes_rhs():
    assert AClass() == ReprComparison(AClass, '<AClass>')


def test_equal_yes_lhs():
    assert ReprComparison(AClass, '<AClass>') == AClass()


def test_equal_no_repr_rhs():
    assert not (AClass() == ReprComparison(AClass, '<other>'))


def test_equal_no_repr_lhs():
    assert not (ReprComparison(AClass, '<other>') == AClass())


def test_equal_no_type_rhs():
    # BClass deliberately has the same repr as AClass, so only the type differs.
    assert repr(BClass()) == '<AClass>'
    assert not (BClass() == ReprComparison(AClass, '<AClass>'))


def test_equal_no_type_lhs():
    assert not (ReprComparison(AClass, '<AClass>') == BClass())


def test_not_equal_yes():
    assert BClass() != ReprComparison(AClass, '<AClass>')


def test_not_equal_no():
    assert not (AClass() != ReprComparison(AClass, '<AClass>'))


def test_subclass_is_equal():
    class SubClass(AClass):
        pass
    assert SubClass() == ReprComparison(AClass, '<AClass>')


def test_in_sequence():
    compare((1, 2, AClass()), expected=(1, 2, ReprComparison(AClass, '<AClass>')))


def test_compare():
    compare(AClass(), expected=ReprComparison(AClass, '<AClass>'))


def test_repr():
    compare('<ReprComparison: tests.test_reprcomparison.AClass: <AClass>>',
            actual=repr(ReprComparison(AClass, '<AClass>')))


def test_str():
    compare('<ReprComparison: tests.test_reprcomparison.AClass: <AClass>>',
            actual=str(ReprComparison(AClass, '<AClass>')))


def test_match_str():
    compare(AClass(), expected=ReprComparison(AClass, match=r'<A.*>'))


def test_match_str_no_match():
    assert AClass() != ReprComparison(AClass, match=r'<B.*>')


def test_match_str_wrong_type():
    assert BClass() != ReprComparison(AClass, match=r'<A.*>')


def test_match_compiled_pattern():
    compare(AClass(), expected=ReprComparison(AClass, match=re.compile(r'<A.*>')))


def test_match_repr():
    compare("<ReprComparison: tests.test_reprcomparison.AClass: match='<A.*>'>",
            actual=repr(ReprComparison(AClass, match=r'<A.*>')))


def test_neither_repr_nor_match() -> None:
    with ShouldRaise(TypeError('provide either expected or match')):
        ReprComparison(AClass)  # type: ignore[call-overload]


def test_both_repr_and_match() -> None:
    with ShouldRaise(TypeError('provide either expected or match')):
        ReprComparison(AClass, '<AClass>', match=r'<A.*>')  # type: ignore[call-overload]
