from testfixtures import StringComparison as S
from unittest import TestCase

class Tests(TestCase):

    def test_equal_yes(self):
        self.failUnless('on 40220'==S('on \d+'))

    def test_equal_no(self):
        self.failIf('on xxx'==S('on \d+'))

    def test_not_equal_yes(self):
        self.failIf('on 40220'!=S('on \d+'))

    def test_not_equal_no(self):
        self.failUnless('on xxx'!=S('on \d+'))

    def test_comp_in_sequence(self):
        self.failUnless((
            1,2,'on 40220'
            )==(
            1,2,S('on \d+')
            ))

    def test_not_string(self):
        self.failIf(40220==S('on \d+'))
    
