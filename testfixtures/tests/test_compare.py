# Copyright (c) 2008 Simplistix Ltd
# See license.txt for license details.

from re import compile
from testfixtures import identity,compare,Comparison as C,generator
from unittest import TestCase,TestSuite,makeSuite

hexaddr = compile('0x[0-9A-Fa-f]+')

class TestCompare(TestCase):

    def checkRaises(self,x,y,message):
        try:
            compare(x,y)
        except Exception,e:
            if not isinstance(e,AssertionError):
                self.fail('Expected AssertionError, got %r'%e)
            actual = hexaddr.sub('...',e.args[0])
            self.assertEqual(actual,message)
        else:
            self.fail('No exception raised!')
            
    def test_object_same(self):
        o = object()
        self.failUnless(compare(o,o) is identity)

    def test_object_diff(self):
        o1 = object()
        o2 = object()
        self.checkRaises(
            o1,o2,
            '<object object at ...> != <object object at ...>'
            )

    def test_different_types(self):
        self.checkRaises('x',1,"'x' != 1")

    def test_number_same(self):
        self.failUnless(compare(1,1) is identity)

    def test_number_different(self):
        self.checkRaises(1,2,'1 != 2')

    def test_string_same(self):
        self.failUnless(compare('x','x') is identity)

    def test_string_diff_short(self):
        self.checkRaises(
            '\n'+('x'*9),'\n'+('y'*9),
            "'\\nxxxxxxxxx' != '\\nyyyyyyyyy'"
            )

    def test_string_diff_long(self):
        self.checkRaises(
            'x'*11,'y'*11,
            "\n'xxxxxxxxxxx'\n!=\n'yyyyyyyyyyy'"
            )

    def test_string_diff_long_newlines(self):
        self.checkRaises(
            'x'*5+'\n'+'y'*5,'x'*5+'\n'+'z'*5,
            "\n@@ -1,2 +1,2 @@\n xxxxx\n-yyyyy\n+zzzzz"
            )

    def test_exception_same_object(self):
        e = ValueError('some message')
        self.failUnless(compare(e,e) is identity)

    def test_exception_same_c_wrapper(self):
        e1 = ValueError('some message')
        e2 = ValueError('some message')
        self.failUnless(compare(C(e1),e2) is identity)

    def test_exception_different_object(self):
        e1 = ValueError('some message')
        e2 = ValueError('some message')
        self.checkRaises(
            e1,e2,
            "ValueError('some message',) != ValueError('some message',)"
            )

    def test_exception_different_object_c_wrapper(self):
        e1 = ValueError('some message')
        e2 = ValueError('some message')
        self.failUnless(compare(C(e1),e2) is identity)

    def test_exception_diff(self):
        e1 = ValueError('some message')
        e2 = ValueError('some other message')
        self.checkRaises(
            e1,e2,
            "ValueError('some message',) != ValueError('some other message',)"
            )

    def test_exception_diff_c_wrapper(self):
        e1 = ValueError('some message')
        e2 = ValueError('some other message')
        self.checkRaises(
            C(e1),e2,
            "<C:exceptions.ValueError with vars ('some message',)>"
            " != "
            "ValueError('some other message',)"
            )

    def test_exception_same_c_wrappers(self):
        # NB: don't use C wrappers on both sides!
        e = ValueError('some message')
        self.checkRaises(
            C(e),C(e),
            "<C:exceptions.ValueError with vars ('some message',)>"
            " != "
            "<C:exceptions.ValueError with vars ('some message',)>"
            )
    
    def test_list_same(self):
        self.failUnless(compare([1,2,3],[1,2,3]) is identity)

    def test_list_different(self):
        self.checkRaises(
            [1,2,3],[1,2,4],
            "Sequence not as expected:\n"
            "  same:[1, 2]\n"
            " first:[3]\n"
            "second:[4]"
            )

    def test_list_totally_different(self):
        self.checkRaises(
            [1],[2],
            "Sequence not as expected:\n"
            "  same:[]\n"
            " first:[1]\n"
            "second:[2]"
            )

    def test_list_first_shorter(self):
        self.checkRaises(
            [1,2],[1,2,3],
            "Sequence not as expected:\n"
            "  same:[1, 2]\n"
            " first:[]\n"
            "second:[3]"
            )

    def test_list_second_shorted(self):
        self.checkRaises(
            [1,2,3],[1,2],
            "Sequence not as expected:\n"
            "  same:[1, 2]\n"
            " first:[3]\n"
            "second:[]"
            )

    def test_tuple_same(self):
        self.failUnless(compare((1,2,3),(1,2,3)) is identity)

    def test_tuple_different(self):
        self.checkRaises(
            (1,2,3),(1,2,4),
            "Sequence not as expected:\n"
            "  same:(1, 2)\n"
            " first:(3,)\n"
            "second:(4,)"
            )

    def test_tuple_totally_different(self):
        self.checkRaises(
            (1,),(2,),
            "Sequence not as expected:\n"
            "  same:()\n"
            " first:(1,)\n"
            "second:(2,)"
            )

    def test_tuple_first_shorter(self):
        self.checkRaises(
            (1,2),(1,2,3),
            "Sequence not as expected:\n"
            "  same:(1, 2)\n"
            " first:()\n"
            "second:(3,)"
            )

    def test_tuple_second_shorted(self):
        self.checkRaises(
            (1,2,3),(1,2),
            "Sequence not as expected:\n"
            "  same:(1, 2)\n"
            " first:(3,)\n"
            "second:()"
            )

    def test_generator_same(self):
        self.failUnless(compare(generator(1,2,3),generator(1,2,3)) is identity)

    def test_generator_different(self):
        self.checkRaises(
            generator(1,2,3),generator(1,2,4),
            "Sequence not as expected:\n"
            "  same:(1, 2)\n"
            " first:(3,)\n"
            "second:(4,)"
            )

    def test_generator_totally_different(self):
        self.checkRaises(
            generator(1,),generator(2,),
            "Sequence not as expected:\n"
            "  same:()\n"
            " first:(1,)\n"
            "second:(2,)"
            )

    def test_generator_first_shorter(self):
        self.checkRaises(
            generator(1,2),generator(1,2,3),
            "Sequence not as expected:\n"
            "  same:(1, 2)\n"
            " first:()\n"
            "second:(3,)"
            )

    def test_generator_second_shorted(self):
        self.checkRaises(
            generator(1,2,3),generator(1,2),
            "Sequence not as expected:\n"
            "  same:(1, 2)\n"
            " first:(3,)\n"
            "second:()"
            )

    def test_generator_and_sequence(self):
        expected = "(1, 2, 3) != <generator object at ...>"
        self.checkRaises(
            (1,2,3),generator(1,2,3),
            expected,
            )

    def test_tuple_and_list(self):
        self.checkRaises(
            (1,2,3),[1,2,3],
            "(1, 2, 3) != [1, 2, 3]"
            )

    def test_old_style_classes_same(self):
        class X:pass
        self.failUnless(compare(X,X) is identity)

    def test_old_style_classes_different(self):
        class X:pass
        class Y:pass
        self.checkRaises(
            X,Y,
            "<class testfixtures.tests.test_compare.X at ...>"
            " != "
            "<class testfixtures.tests.test_compare.Y at ...>"
            )

def test_suite():
    return TestSuite((
        makeSuite(TestCompare),
        ))
