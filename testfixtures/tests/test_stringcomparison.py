import re

from testfixtures import StringComparison as S, compare
from testfixtures.compat import PY2
from unittest import TestCase


class Tests(TestCase):

    def test_equal_yes(self):
        self.assertTrue('on 40220' == S('on \d+'))

    def test_equal_no(self):
        self.assertFalse('on xxx' == S('on \d+'))

    def test_not_equal_yes(self):
        self.assertFalse('on 40220' != S('on \d+'))

    def test_not_equal_no(self):
        self.assertTrue('on xxx' != S('on \d+'))

    def test_comp_in_sequence(self):
        self.assertTrue((
            1, 2, 'on 40220'
            ) == (
            1, 2, S('on \d+')
            ))

    def test_not_string(self):
        self.assertFalse(40220 == S('on \d+'))

    def test_repr(self):
        compare('<S:on \\d+>',
                repr(S('on \d+')))

    def test_str(self):
        compare('<S:on \\d+>',
                str(S('on \d+')))

    def test_sort(self):
        a = S('a')
        b = S('b')
        c = S('c')
        compare(sorted(('d', c, 'e', a, 'a1', b)),
                [a, 'a1', b, c, 'd', 'e'])

    if PY2:
        # cmp no longer exists in Python 3!

        def test_cmp_yes(self):
            self.assertFalse(cmp(S('on \d+'), 'on 4040'))

        def test_cmp_no(self):
            self.assertTrue(cmp(S('on \d+'), 'on xx'))

    def test_flags_argument(self):
        compare(S(".*bar", re.DOTALL), actual="foo\nbar")

    def test_flags_parameter(self):
        compare(S(".*bar", flags=re.DOTALL), actual="foo\nbar")

    def test_flags_names(self):
        compare(S(".*BaR", dotall=True, ignorecase=True), actual="foo\nbar")
