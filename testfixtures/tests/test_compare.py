# Copyright (c) 2008 Simplistix Ltd
# See license.txt for license details.

from re import compile
from testfixtures import identity,compare,Comparison as C,generator, ShouldRaise
from unittest import TestCase,TestSuite,makeSuite

hexaddr = compile('0x[0-9A-Fa-f]+')

class TestCompare(TestCase):

    def checkRaises(self,x,y,message=None,regex=None,**kw):
        try:
            compare(x,y,**kw)
        except Exception,e:
            if not isinstance(e,AssertionError):
                self.fail('Expected AssertionError, got %r'%e)
            actual = hexaddr.sub('...',e.args[0])
            if message is not None:
                # handy for debugging, but can't be relied on for tests!
                # compare(actual,message)
                self.assertEqual(actual,message)
            else:
                if not regex.match(actual):
                    self.fail('%r did not match %r'%(actual,regex.pattern))
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
            C(e1),e2,"\n"
            "  <C(failed):exceptions.ValueError>\n"
            "  args:('some message',) != ('some other message',)\n"
            "  </C>"
            " != "
            "ValueError('some other message',)"
            )

    def test_sequence_long(self):
        self.checkRaises(
            ['quite a long string 1','quite a long string 2',
             'quite a long string 3','quite a long string 4',
             'quite a long string 5','quite a long string 6',
             'quite a long string 7','quite a long string 8'],
            ['quite a long string 1','quite a long string 2',
             'quite a long string 3','quite a long string 4',
             'quite a long string 9','quite a long string 10',
             'quite a long string 11','quite a long string 12'],
            "Sequence not as expected:\n\n"
            "same:\n"
            "['quite a long string 1',\n"
            " 'quite a long string 2',\n"
            " 'quite a long string 3',\n"
            " 'quite a long string 4']\n\n"
            "first:\n"
            "['quite a long string 5',\n"
            " 'quite a long string 6',\n"
            " 'quite a long string 7',\n"
            " 'quite a long string 8']\n\n"
            "second:\n"
            "['quite a long string 9',\n"
            " 'quite a long string 10',\n"
            " 'quite a long string 11',\n"
            " 'quite a long string 12']"
            )

    def test_list_same(self):
        self.failUnless(compare([1,2,3],[1,2,3]) is identity)

    def test_list_different(self):
        self.checkRaises(
            [1,2,3],[1,2,4],
            "Sequence not as expected:\n\n"
            "same:\n"
            "[1, 2]\n\n"
            "first:\n"
            "[3]\n\n"
            "second:\n"
            "[4]"
            )

    def test_list_totally_different(self):
        self.checkRaises(
            [1],[2],
            "Sequence not as expected:\n\n"
            "same:\n"
            "[]\n\n"
            "first:\n"
            "[1]\n\n"
            "second:\n"
            "[2]"
            )

    def test_list_first_shorter(self):
        self.checkRaises(
            [1,2],[1,2,3],
            "Sequence not as expected:\n\n"
            "same:\n[1, 2]\n\n"
            "first:\n[]\n\n"
            "second:\n[3]"
            )

    def test_list_second_shorted(self):
        self.checkRaises(
            [1,2,3],[1,2],
            "Sequence not as expected:\n\n"
            "same:\n[1, 2]\n\n"
            "first:\n[3]\n\n"
            "second:\n[]"
            )

    def test_tuple_same(self):
        self.failUnless(compare((1,2,3),(1,2,3)) is identity)

    def test_tuple_different(self):
        self.checkRaises(
            (1,2,3),(1,2,4),
            "Sequence not as expected:\n\n"
            "same:\n(1, 2)\n\n"
            "first:\n(3,)\n\n"
            "second:\n(4,)"
            )

    def test_tuple_totally_different(self):
        self.checkRaises(
            (1,),(2,),
            "Sequence not as expected:\n\n"
            "same:\n()\n\n"
            "first:\n(1,)\n\n"
            "second:\n(2,)"
            )

    def test_tuple_first_shorter(self):
        self.checkRaises(
            (1,2),(1,2,3),
            "Sequence not as expected:\n\n"
            "same:\n(1, 2)\n\n"
            "first:\n()\n\n"
            "second:\n(3,)"
            )

    def test_tuple_second_shorted(self):
        self.checkRaises(
            (1,2,3),(1,2),
            "Sequence not as expected:\n\n"
            "same:\n(1, 2)\n\n"
            "first:\n(3,)\n\n"
            "second:\n()"
            )

    def test_generator_same(self):
        self.failUnless(compare(generator(1,2,3),generator(1,2,3)) is identity)

    def test_generator_different(self):
        self.checkRaises(
            generator(1,2,3),generator(1,2,4),
            "Sequence not as expected:\n\n"
            "same:\n(1, 2)\n\n"
            "first:\n(3,)\n\n"
            "second:\n(4,)"
            )

    def test_generator_totally_different(self):
        self.checkRaises(
            generator(1,),generator(2,),
            "Sequence not as expected:\n\n"
            "same:\n()\n\n"
            "first:\n(1,)\n\n"
            "second:\n(2,)"
            )

    def test_generator_first_shorter(self):
        self.checkRaises(
            generator(1,2),generator(1,2,3),
            "Sequence not as expected:\n\n"
            "same:\n(1, 2)\n\n"
            "first:\n()\n\n"
            "second:\n(3,)"
            )

    def test_generator_second_shorted(self):
        self.checkRaises(
            generator(1,2,3),generator(1,2),
            "Sequence not as expected:\n\n"
            "same:\n(1, 2)\n\n"
            "first:\n(3,)\n\n"
            "second:\n()"
            )

    def test_generator_and_sequence(self):
        expected = compile("\(1, 2, 3\) != <generator object (generator )?at ...>")
        self.checkRaises(
            (1,2,3),generator(1,2,3),
            regex=expected,
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

    def test_include_trailing_whitespace(self):
        self.checkRaises(
            ' x \n',' x  \n',
            "' x \\n' != ' x  \\n'"
            )

    def test_ignore_trailing_whitespace(self):
        compare(' x \t\n',' x\t  \n',trailing_whitespace=False)
        
    def test_ignore_trailing_whitespace_non_string(self):
        with ShouldRaise(TypeError(
            "if blanklines or trailing_whitespace are not True, only string "
            "arguments should be passed, got 1 and ''"
            )):
            compare(1,'',trailing_whitespace=False)

    def test_ignore_trailing_whitespace_but_respect_leading_whitespace(self):
        # NB: careful: this strips off the last newline too
        #     DON'T use if you care about that!
        self.checkRaises(
            'a\n b\n  c\n',
            'a\nb\nc\n',
            "'a\\n b\\n  c' != 'a\\nb\\nc'",
            trailing_whitespace=False
            )

    def test_include_blank_lines(self):
        self.checkRaises(
            '\n \n','\n  ',
            "'\\n \\n' != '\\n  '"
            )
        
    def test_ignore_blank_lines(self):
        compare("""
    a

\t
b
  """,
                '    a\nb',blanklines=False)
        
        
    def test_ignore_blank_lines_non_string(self):
        with ShouldRaise(TypeError(
            "if blanklines or trailing_whitespace are not True, only string "
            "arguments should be passed, got 1 and ''"
            )):
            compare(1,'',blanklines=False)

def test_suite():
    return TestSuite((
        makeSuite(TestCompare),
        ))
