import re

from testfixtures import StrComparison, ShouldRaise, compare


class AClass:
    def __str__(self):
        return 'an A'


class BClass:
    def __str__(self):
        return 'an A'


def test_equal_yes_rhs():
    assert AClass() == StrComparison(AClass, 'an A')


def test_equal_yes_lhs():
    assert StrComparison(AClass, 'an A') == AClass()


def test_equal_no_str_rhs():
    assert not (AClass() == StrComparison(AClass, 'other'))


def test_equal_no_str_lhs():
    assert not (StrComparison(AClass, 'other') == AClass())


def test_equal_no_type_rhs():
    # BClass deliberately has the same str as AClass, so only the type differs.
    assert str(BClass()) == 'an A'
    assert not (BClass() == StrComparison(AClass, 'an A'))


def test_equal_no_type_lhs():
    assert not (StrComparison(AClass, 'an A') == BClass())


def test_not_equal_yes():
    assert BClass() != StrComparison(AClass, 'an A')


def test_not_equal_no():
    assert not (AClass() != StrComparison(AClass, 'an A'))


def test_subclass_is_equal():
    class SubClass(AClass):
        pass
    assert SubClass() == StrComparison(AClass, 'an A')


def test_in_sequence():
    compare((1, 2, AClass()), expected=(1, 2, StrComparison(AClass, 'an A')))


def test_compare():
    compare(AClass(), expected=StrComparison(AClass, 'an A'))


def test_repr():
    compare('<StrComparison: tests.test_strcomparison.AClass: an A>',
            actual=repr(StrComparison(AClass, 'an A')))


def test_str():
    compare('<StrComparison: tests.test_strcomparison.AClass: an A>',
            actual=str(StrComparison(AClass, 'an A')))


def test_match_str():
    compare(AClass(), expected=StrComparison(AClass, match=r'an \w'))


def test_match_str_no_match():
    assert AClass() != StrComparison(AClass, match=r'a B')


def test_match_str_wrong_type():
    assert BClass() != StrComparison(AClass, match=r'an \w')


def test_match_compiled_pattern():
    compare(AClass(), expected=StrComparison(AClass, match=re.compile(r'an \w')))


def test_match_repr():
    compare("<StrComparison: tests.test_strcomparison.AClass: match='an .'>",
            actual=repr(StrComparison(AClass, match=r'an .')))


def test_neither_str_nor_match() -> None:
    with ShouldRaise(TypeError('provide either expected or match')):
        StrComparison(AClass)  # type: ignore[call-overload]


def test_both_str_and_match() -> None:
    with ShouldRaise(TypeError('provide either expected or match')):
        StrComparison(AClass, 'an A', match=r'an \w')  # type: ignore[call-overload]
