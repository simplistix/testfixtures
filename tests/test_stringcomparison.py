import re

from testfixtures import StringComparison, TextComparison, compare
from unittest import TestCase


class Tests(TestCase):

    def test_old_name_is_alias(self):
        assert StringComparison is TextComparison

    def test_equal_yes(self):
        self.assertTrue('on 40220' == StringComparison(r'on \d+'))

    def test_equal_no(self):
        self.assertFalse('on xxx' == StringComparison(r'on \d+'))

    def test_not_equal_yes(self):
        self.assertFalse('on 40220' != StringComparison(r'on \d+'))

    def test_not_equal_no(self):
        self.assertTrue('on xxx' != StringComparison(r'on \d+'))

    def test_comp_in_sequence(self):
        self.assertTrue((1, 2, 'on 40220') == (1, 2, StringComparison(r'on \d+')))

    def test_not_string(self):
        self.assertFalse(40220 == StringComparison(r'on \d+'))

    def test_not_string_returns_not_implemented(self):
        assert StringComparison(r'x').__eq__(40220) is NotImplemented

    def test_not_string_reflected_equality(self):
        class MatchesAnything:
            def __eq__(self, other):
                return True
            def __ne__(self, other):
                return False
        other = MatchesAnything()
        assert StringComparison(r'x') == other
        assert other == StringComparison(r'x')
        assert not (StringComparison(r'x') != other)
        assert not (other != StringComparison(r'x'))

    def test_repr(self):
        compare('<S:on \\d+>', repr(StringComparison(r'on \d+')))

    def test_str(self):
        compare('<S:on \\d+>', str(StringComparison(r'on \d+')))

    def test_sort(self):
        a = StringComparison('a')
        b = StringComparison('b')
        c = StringComparison('c')
        compare(sorted(('d', c, 'e', a, 'a1', b)), expected=[a, 'a1', b, c, 'd', 'e'])

    def test_flags_argument(self):
        compare(StringComparison(".*bar", re.DOTALL), actual="foo\nbar")

    def test_flags_parameter(self):
        compare(StringComparison(".*bar", flags=re.DOTALL), actual="foo\nbar")

    def test_flags_names(self):
        compare(StringComparison(".*BaR", dotall=True, ignorecase=True), actual="foo\nbar")

    def test_compiled_pattern(self):
        compare(StringComparison(re.compile(r'on \d+')), actual='on 40220')

    def test_compiled_pattern_with_flags(self):
        compare(StringComparison(re.compile(".*BaR", re.DOTALL | re.IGNORECASE)), actual="foo\nbar")
