# Copyright (c) 2008-2014 Simplistix Ltd
# See license.txt for license details.

from collections import namedtuple
from textwrap import dedent
from mock import Mock, call
from re import compile
from testfixtures import (
    Comparison as C,
    Replacer,
    ShouldRaise,
    compare,
    generator,
    singleton,
    )
from testfixtures.compat import (
    class_type_name, exception_module, PY3, xrange,
    BytesLiteral, UnicodeLiteral
    )
from testfixtures.comparison import (
    compare_sequence, not_there, _get_expected_actual
    )
from unittest import TestCase
from .compat import py_33_plus, py_2

hexaddr = compile('0x[0-9A-Fa-f]+')

def hexsub(raw):
    return hexaddr.sub('...', raw)

call_list_repr = repr(Mock().mock_calls.__class__)

class TestCompare(TestCase):

    def checkRaises(self, x=not_there, y=not_there, message=None, regex=None,
                    expected=not_there, actual=not_there,
                    **kw):
        try:
            compare(x, y, expected=expected, actual=actual, **kw)
        except Exception as e:
            if not isinstance(e, AssertionError):
                self.fail('Expected AssertionError, got %r' % e)
            actual = hexsub(e.args[0])
            if message is not None:
                # handy for debugging, but can't be relied on for tests!
                #compare(actual, expected=message, show_whitespace=True)
                self.assertEqual(actual, message)
            else:
                if not regex.match(actual): # pragma: no cover
                    self.fail('%r did not match %r' % (actual, regex.pattern))
        else:
            self.fail('No exception raised!')

    def test_insufficient_arguments_raises(self):
        # More thorough tests in TestGetExpectedActual below, but throwing
        # in a couple just to make sure things work as expected for compare()
        msg = ('Exactly 2 of the arguments (x, y, expected, actual) '
               'must be specified.')
        with ShouldRaise(ValueError(msg)):
            compare()
        with ShouldRaise(ValueError(msg)):
            compare(None)
        with ShouldRaise(ValueError(msg)):
            compare(y=None)
        with ShouldRaise(ValueError(msg)):
            compare(expected=None)
        with ShouldRaise(ValueError(msg)):
            compare(actual=None)

    def test_object_same(self):
        o = object()
        compare(o, o)

    def test_object_diff(self):
        o1 = object()
        o2 = object()
        self.checkRaises(
            o1,o2,
            '<object object at ...> != <object object at ...>'
            )

    def test_object_diff_expected_actual(self):
        o1 = object()
        o2 = object()
        self.checkRaises(
            expected=o1, actual=o2,
            message='<object object at ...> (expected) '
                    '!= (actual) <object object at ...>'
            )

    def test_object_diff_actual_only(self):
        o1 = object()
        o2 = object()
        self.checkRaises(
            o1, actual=o2,
            message='<object object at ...> (expected) '
                    '!= (actual) <object object at ...>'
            )

    def test_object_diff_expected_only(self):
        o1 = object()
        o2 = object()
        self.checkRaises(
            o2, expected=o1,
            message='<object object at ...> (expected) '
                    '!= (actual) <object object at ...>'
            )

    def test_different_types(self):
        self.checkRaises('x', 1, "'x' != 1")

    def test_different_types_expected_actual(self):
        self.checkRaises('x', actual=1, message="'x' (expected) != (actual) 1")

    def test_number_same(self):
        compare(1, 1)

    def test_number_different(self):
        self.checkRaises(1, 2, '1 != 2')

    def test_number_expected_actual(self):
        self.checkRaises(1, actual=2, message='1 (expected) != (actual) 2')

    def test_string_same(self):
        compare('x', 'x')

    def test_unicode_string_different(self):
        if py_2:
            expected = "u'a' != 'b'"
        else:
            expected = "'a' != b'b'"
        self.checkRaises(
            UnicodeLiteral('a'), BytesLiteral('b'),
            expected
            )

    def test_unicode_string_expected_actual(self):
        if py_2:
            expected = "u'a' (expected) != (actual) 'b'"
        else:
            expected = "'a' (expected) != (actual) b'b'"
        self.checkRaises(
            UnicodeLiteral('a'), actual=BytesLiteral('b'),
            message=expected
            )

    def test_string_diff_short(self):
        self.checkRaises(
            '\n'+('x'*9),'\n'+('y'*9),
            "'\\nxxxxxxxxx' != '\\nyyyyyyyyy'"
            )

    def test_string_diff_short_expected_actual(self):
        self.checkRaises(
            '\n'+('x'*9), actual='\n'+('y'*9),
            message="'\\nxxxxxxxxx' (expected) != (actual) '\\nyyyyyyyyy'"
            )

    def test_string_diff_long(self):
        self.checkRaises(
            'x'*11, 'y'*11,
            message=dedent("""
                'xxxxxxxxxxx'
                !=
                'yyyyyyyyyyy'"""))

    def test_string_diff_long_expected_actual(self):
        self.checkRaises(
            'x'*11, actual='y'*11,
            message=dedent("""
                'xxxxxxxxxxx'
                (expected)
                !=
                (actual)
                'yyyyyyyyyyy'"""))

    def test_string_diff_long_newlines(self):
        self.checkRaises(
            dedent("""\
                xxxxx
                yyyyy"""),
            dedent("""\
                xxxxx
                zzzzz"""),
            dedent("""
                @@ -1,2 +1,2 @@
                 xxxxx
                -yyyyy
                +zzzzz""")
            )

    def test_string_diff_long_newlines_expected_actual(self):
        self.checkRaises(
            dedent("""\
                xxxxx
                yyyyy"""),
            actual=dedent("""\
                xxxxx
                zzzzz"""),
            message=dedent("""
                --- expected
                +++ actual
                @@ -1,2 +1,2 @@
                 xxxxx
                -yyyyy
                +zzzzz""")
            )

    def test_exception_same_object(self):
        e = ValueError('some message')
        compare(e, e)

    def test_exception_same_c_wrapper(self):
        e1 = ValueError('some message')
        e2 = ValueError('some message')
        compare(C(e1), e2)

    def test_exception_different_object(self):
        e1 = ValueError('some message')
        e2 = ValueError('some message')
        self.checkRaises(
            e1,e2,
            "ValueError('some message',) != ValueError('some message',)"
            )

    def test_exception_different_object_expected_actual(self):
        e1 = ValueError('some message')
        e2 = ValueError('some message')
        self.checkRaises(
            e1, actual=e2,
            message="ValueError('some message',) (expected) != "
                    "(actual) ValueError('some message',)"
            )

    def test_exception_different_object_c_wrapper(self):
        e1 = ValueError('some message')
        e2 = ValueError('some message')
        compare(C(e1), e2)

    def test_exception_diff(self):
        e1 = ValueError('some message')
        e2 = ValueError('some other message')
        self.checkRaises(
            e1,e2,
            "ValueError('some message',) != ValueError('some other message',)"
            )

    def test_exception_diff_expected_actual(self):
        e1 = ValueError('some message')
        e2 = ValueError('some other message')
        self.checkRaises(
            e1, actual=e2,
            message="ValueError('some message',) (expected) != "
                    "(actual) ValueError('some other message',)"
            )

    def test_exception_diff_c_wrapper(self):
        e1 = ValueError('some message')
        e2 = ValueError('some other message')
        self.checkRaises(
            C(e1), e2, ("\n"
            "  <C(failed):{0}.ValueError>\n"
            "  args:('some message',) != ('some other message',)\n"
            "  </C>"
            " != "
            "ValueError('some other message',)"
            ).format(exception_module))

    def test_sequence_short(self):
        self.checkRaises(
            'the quick brown fox jumped over the lazy dog'.split(),
            'the quick brown fox jumped over the sleeping dog'.split(),
            dedent("""\
                sequence not as expected:

                same:
                ['the', 'quick', 'brown', 'fox', 'jumped', 'over', 'the']

                first:
                ['lazy', 'dog']

                second:
                ['sleeping', 'dog']

                While comparing [7]: 'lazy' != 'sleeping'"""))

    def test_sequence_short_expected_actual(self):
        self.checkRaises(
            expected='the quick brown fox jumped over the lazy dog'.split(),
            actual='the quick brown fox jumped over the sleeping dog'.split(),
            message=dedent("""\
                sequence not as expected:

                same:
                ['the', 'quick', 'brown', 'fox', 'jumped', 'over', 'the']

                expected:
                ['lazy', 'dog']

                actual:
                ['sleeping', 'dog']

                While comparing [7]: 'lazy' (expected) != (actual) 'sleeping'"""))

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
            dedent("""\
                sequence not as expected:

                same:
                ['quite a long string 1',
                 'quite a long string 2',
                 'quite a long string 3',
                 'quite a long string 4']

                first:
                ['quite a long string 5',
                 'quite a long string 6',
                 'quite a long string 7',
                 'quite a long string 8']

                second:
                ['quite a long string 9',
                 'quite a long string 10',
                 'quite a long string 11',
                 'quite a long string 12']

                While comparing [4]: 
                'quite a long string 5'
                !=
                'quite a long string 9'"""))

    def test_sequence_long_expected_actual(self):
        self.checkRaises(
            expected=
            ['quite a long string 1','quite a long string 2',
             'quite a long string 3','quite a long string 4',
             'quite a long string 5','quite a long string 6',
             'quite a long string 7','quite a long string 8'],
            actual=
            ['quite a long string 1','quite a long string 2',
             'quite a long string 3','quite a long string 4',
             'quite a long string 9','quite a long string 10',
             'quite a long string 11','quite a long string 12'],
            message=dedent("""\
                sequence not as expected:

                same:
                ['quite a long string 1',
                 'quite a long string 2',
                 'quite a long string 3',
                 'quite a long string 4']

                expected:
                ['quite a long string 5',
                 'quite a long string 6',
                 'quite a long string 7',
                 'quite a long string 8']

                actual:
                ['quite a long string 9',
                 'quite a long string 10',
                 'quite a long string 11',
                 'quite a long string 12']

                While comparing [4]: 
                'quite a long string 5'
                (expected)
                !=
                (actual)
                'quite a long string 9'"""))

    def test_list_same(self):
        compare([1,2,3], [1,2,3])

    def test_list_different(self):
        self.checkRaises(
            [1,2,3],[1,2,4],
            "sequence not as expected:\n\n"
            "same:\n"
            "[1, 2]\n\n"
            "first:\n"
            "[3]\n\n"
            "second:\n"
            "[4]"
            )

    def test_list_different_expected_actual(self):
        self.checkRaises(
            [1,2,3], actual=[1,2,4],
            message="sequence not as expected:\n\n"
            "same:\n"
            "[1, 2]\n\n"
            "expected:\n"
            "[3]\n\n"
            "actual:\n"
            "[4]"
            )

    def test_list_totally_different(self):
        self.checkRaises(
            [1],[2],
            "sequence not as expected:\n\n"
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
            "sequence not as expected:\n\n"
            "same:\n[1, 2]\n\n"
            "first:\n[]\n\n"
            "second:\n[3]"
            )

    def test_list_second_shorter(self):
        self.checkRaises(
            [1,2,3],[1,2],
            "sequence not as expected:\n\n"
            "same:\n[1, 2]\n\n"
            "first:\n[3]\n\n"
            "second:\n[]"
            )

    def test_dict_same(self):
        compare(dict(x=1), dict(x=1))

    def test_dict_first_missing_keys(self):
        self.checkRaises(
            dict(),dict(z=3),
            "dict not as expected:\n"
            "\n"
            "in second but not first:\n"
            "'z': 3"
            )

    def test_dict_first_missing_keys_expected_actual(self):
        self.checkRaises(
            dict(), actual=dict(z=3),
            message="dict not as expected:\n"
            "\n"
            "in actual but not expected:\n"
            "'z': 3"
            )

    def test_dict_second_missing_keys(self):
        self.checkRaises(
            dict(z=3),dict(),
            "dict not as expected:\n"
            "\n"
            "in first but not second:\n"
            "'z': 3"
            )

    def test_dict_second_missing_keys_expected_actual(self):
        self.checkRaises(
            dict(z=3), actual=dict(),
            message="dict not as expected:\n"
            "\n"
            "in expected but not actual:\n"
            "'z': 3"
            )

    def test_dict_values_different(self):
        self.checkRaises(
            dict(x=1),dict(x=2),
            "dict not as expected:\n"
            "\n"
            "values differ:\n"
            "'x': 1 != 2"
            )

    def test_dict_values_different_expected_actual(self):
        self.checkRaises(
            dict(x=1), actual=dict(x=2),
            message="dict not as expected:\n"
            "\n"
            "values differ:\n"
            "'x': 1 (expected) != (actual) 2"
            )

    def test_dict_tuple_keys_same_value(self):
        compare({(1, 2): None}, {(1, 2): None})

    def test_dict_tuple_keys_different_value(self):
        self.checkRaises(
            {(1, 2): 3},
            {(1, 2): 42},
            "dict not as expected:\n"
            "\n"
            "values differ:\n"
            "(1, 2): 3 != 42"
            )

    def test_dict_tuple_keys_different_value_expected_actual(self):
        self.checkRaises(
            expected={(1, 2): 3},
            actual={(1, 2): 42},
            message="dict not as expected:\n"
            "\n"
            "values differ:\n"
            "(1, 2): 3 (expected) != (actual) 42"
            )

    def test_dict_full_diff(self):
        self.checkRaises(
            dict(x=1, y=2, a=4), dict(x=1, z=3, a=5),
            "dict not as expected:\n"
            "\n"
            'same:\n'
            "['x']\n"
            "\n"
            "in first but not second:\n"
            "'y': 2\n"
            '\n'
            "in second but not first:\n"
            "'z': 3\n"
            '\n'
            "values differ:\n"
            "'a': 4 != 5"
            )

    def test_dict_full_diff_expected_actual(self):
        self.checkRaises(
            dict(x=1, y=2, a=4), actual=dict(x=1, z=3, a=5),
            message="dict not as expected:\n"
            "\n"
            'same:\n'
            "['x']\n"
            "\n"
            "in expected but not actual:\n"
            "'y': 2\n"
            '\n'
            "in actual but not expected:\n"
            "'z': 3\n"
            '\n'
            "values differ:\n"
            "'a': 4 (expected) != (actual) 5"
            )

    def test_dict_consistent_ordering(self):
        self.checkRaises(
            dict(xa=1, xb=2, ya=1, yb=2, aa=3, ab=4),
            dict(xa=1, xb=2, za=3, zb=4, aa=5, ab=5),
            "dict not as expected:\n"
            "\n"
            'same:\n'
            "['xa', 'xb']\n"
            "\n"
            "in first but not second:\n"
            "'ya': 1\n"
            "'yb': 2\n"
            '\n'
            "in second but not first:\n"
            "'za': 3\n"
            "'zb': 4\n"
            '\n'
            "values differ:\n"
            "'aa': 3 != 5\n"
            "'ab': 4 != 5"
            )

    def test_set_same(self):
        compare(set([1]), set([1]))

    def test_set_first_missing_keys(self):
        self.checkRaises(
            set(), set([3]),
            "set not as expected:\n"
            "\n"
            "in second but not first:\n"
            "[3]\n"
            '\n'
            )

    def test_set_first_missing_keys_expected_actual(self):
        self.checkRaises(
            set(), actual=set([3]),
            message="set not as expected:\n"
            "\n"
            "in actual but not expected:\n"
            "[3]\n"
            '\n'
            )

    def test_set_second_missing_keys(self):
        self.checkRaises(
            set([3]), set(),
            "set not as expected:\n"
            "\n"
            "in first but not second:\n"
            "[3]\n"
            '\n'
            )

    def test_set_second_missing_keys_expected_actual(self):
        self.checkRaises(
            set([3]), actual=set(),
            message="set not as expected:\n"
            "\n"
            "in expected but not actual:\n"
            "[3]\n"
            '\n'
            )

    def test_set_full_diff(self):
        self.checkRaises(
            set([1, 2, 4]), set([1, 3, 5]),
            "set not as expected:\n"
            "\n"
            "in first but not second:\n"
            "[2, 4]\n"
            '\n'
            "in second but not first:\n"
            "[3, 5]\n"
            '\n'
            )


    def test_set_full_diff_expected_actual(self):
        self.checkRaises(
            set([1, 2, 4]), actual=set([1, 3, 5]),
            message="set not as expected:\n"
            "\n"
            "in expected but not actual:\n"
            "[2, 4]\n"
            '\n'
            "in actual but not expected:\n"
            "[3, 5]\n"
            '\n'
            )

    def test_tuple_same(self):
        compare((1,2,3), (1,2,3))

    def test_tuple_different(self):
        self.checkRaises(
            (1, 2, 3), (1, 2, 4),
            "sequence not as expected:\n\n"
            "same:\n(1, 2)\n\n"
            "first:\n(3,)\n\n"
            "second:\n(4,)"
            )

    def test_tuple_different_expected_actual(self):
        self.checkRaises(
            (1, 2, 3), actual=(1, 2, 4),
            message="sequence not as expected:\n\n"
            "same:\n(1, 2)\n\n"
            "expected:\n(3,)\n\n"
            "actual:\n(4,)"
            )

    def test_tuple_totally_different(self):
        self.checkRaises(
            (1,), (2,),
            "sequence not as expected:\n\n"
            "same:\n()\n\n"
            "first:\n(1,)\n\n"
            "second:\n(2,)"
            )

    def test_tuple_totally_different_expected_actual(self):
        self.checkRaises(
            (1,), actual=(2,),
            message="sequence not as expected:\n\n"
            "same:\n()\n\n"
            "expected:\n(1,)\n\n"
            "actual:\n(2,)"
            )

    def test_tuple_first_shorter(self):
        self.checkRaises(
            (1, 2), (1, 2, 3),
            "sequence not as expected:\n\n"
            "same:\n(1, 2)\n\n"
            "first:\n()\n\n"
            "second:\n(3,)"
            )

    def test_tuple_first_shorter_expected_actual(self):
        self.checkRaises(
            (1, 2), actual=(1, 2, 3),
            message="sequence not as expected:\n\n"
            "same:\n(1, 2)\n\n"
            "expected:\n()\n\n"
            "actual:\n(3,)"
            )

    def test_tuple_second_shorter(self):
        self.checkRaises(
            (1, 2, 3), (1, 2),
            "sequence not as expected:\n\n"
            "same:\n(1, 2)\n\n"
            "first:\n(3,)\n\n"
            "second:\n()"
            )

    def test_tuple_second_shorter_expected_actual(self):
        self.checkRaises(
            (1, 2, 3), actual=(1, 2),
            message="sequence not as expected:\n\n"
            "same:\n(1, 2)\n\n"
            "expected:\n(3,)\n\n"
            "actual:\n()"
            )

    def test_generator_same(self):
        compare(generator(1,2,3), generator(1,2,3))

    def test_generator_different(self):
        self.checkRaises(
            generator(1,2,3),generator(1,2,4),
            "sequence not as expected:\n\n"
            "same:\n(1, 2)\n\n"
            "first:\n(3,)\n\n"
            "second:\n(4,)"
            )

    def test_generator_different_expected_actual(self):
        self.checkRaises(
            generator(1,2,3), actual=generator(1,2,4),
            message="sequence not as expected:\n\n"
            "same:\n(1, 2)\n\n"
            "expected:\n(3,)\n\n"
            "actual:\n(4,)"
            )

    def test_generator_totally_different(self):
        self.checkRaises(
            generator(1,),generator(2,),
            "sequence not as expected:\n\n"
            "same:\n()\n\n"
            "first:\n(1,)\n\n"
            "second:\n(2,)"
            )

    def test_generator_first_shorter(self):
        self.checkRaises(
            generator(1,2),generator(1,2,3),
            "sequence not as expected:\n\n"
            "same:\n(1, 2)\n\n"
            "first:\n()\n\n"
            "second:\n(3,)"
            )

    def test_generator_second_shorted(self):
        self.checkRaises(
            generator(1,2,3),generator(1,2),
            "sequence not as expected:\n\n"
            "same:\n(1, 2)\n\n"
            "first:\n(3,)\n\n"
            "second:\n()"
            )

    def test_nested_generator_different(self):
        self.checkRaises(
            generator(1, 2, generator(3), 4),
            generator(1, 2, generator(3), 5),
            "sequence not as expected:\n"
            "\n"
            "same:\n"
            "(1, 2, <generator object generator at ...>)\n"
            "\n"
            "first:\n"
            "(4,)\n"
            "\n"
            "second:\n"
            "(5,)"
            )

    def test_nested_generator_different_expected_actual(self):
        self.checkRaises(
            expected=generator(1, 2, generator(3), 4),
            actual=generator(1, 2, generator(3), 5),
            message="sequence not as expected:\n"
            "\n"
            "same:\n"
            "(1, 2, <generator object generator at ...>)\n"
            "\n"
            "expected:\n"
            "(4,)\n"
            "\n"
            "actual:\n"
            "(5,)"
            )

    def test_nested_generator_tuple_left(self):
        compare(
            generator(1, 2, (3, ), 4),
            generator(1, 2, generator(3), 4),
            )

    def test_nested_generator_tuple_right(self):
        compare(
            generator(1, 2, generator(3), 4),
            generator(1, 2, (3, ), 4),
            )

    def test_sequence_and_generator(self):
        compare((1,2,3), generator(1,2,3))

    def test_sequence_and_generator_strict(self):
        expected = compile(
            "\(1, 2, 3\) \(<(class|type) 'tuple'>\) != "
            "<generator object (generator )?at... "
            "\(<(class|type) 'generator'>\)"
            )
        self.checkRaises(
            (1, 2, 3), generator(1, 2, 3),
            regex=expected,
            strict=True,
            )

    def test_sequence_and_generator_strict_expected_actual(self):
        expected = compile(
            "\(1, 2, 3\) \(<(class|type) 'tuple'>\) \(expected\) != "
            "\(actual\) <generator object (generator )?at... "
            "\(<(class|type) 'generator'>\)"
            )
        self.checkRaises(
            (1, 2, 3), actual=generator(1, 2, 3),
            regex=expected,
            strict=True,
            )

    def test_generator_and_sequence(self):
        compare(generator(1,2,3), (1,2,3))

    def test_iterable_with_iterable_same(self):
        compare(xrange(1, 4), xrange(1, 4))

    def test_iterable_with_iterable_different(self):
        self.checkRaises(
            xrange(1, 4), xrange(1, 3),
            "sequence not as expected:\n"
            "\n"
            "same:\n"
            "(1, 2)\n"
            "\n"
            "first:\n"
            "(3,)\n"
            "\n"
            "second:\n"
            "()"
            )

    def test_iterable_and_generator(self):
        compare(xrange(1, 4), generator(1,2,3))

    def test_iterable_and_generator_strict(self):
        expected = compile(
            "x?range\(1, 4\) \(<(class|type) 'x?range'>\) != "
            "<generator object (generator )?at... "
            "\(<(class|type) 'generator'>\)"
            )
        self.checkRaises(
            xrange(1,4), generator(1,2,3),
            regex=expected,
            strict=True,
            )

    def test_generator_and_iterable(self):
        compare(generator(1,2,3), xrange(1,4))

    def test_tuple_and_list(self):
        compare((1,2,3), [1,2,3])

    def test_tuple_and_list_strict(self):
        if py_2:
            expected = ("(1, 2, 3) (<type 'tuple'>) != "
                        "[1, 2, 3] (<type 'list'>)")
        else:
            expected = ("(1, 2, 3) (<class 'tuple'>) != "
                        "[1, 2, 3] (<class 'list'>)")

        self.checkRaises(
            (1, 2, 3), [1, 2, 3],
            expected,
            strict=True
            )

    def test_tuple_and_list_strict_expected_actual(self):
        if py_2:
            expected = ("(1, 2, 3) (<type 'tuple'>) (expected) != "
                        "(actual) [1, 2, 3] (<type 'list'>)")
        else:
            expected = ("(1, 2, 3) (<class 'tuple'>) (expected) != "
                        "(actual) [1, 2, 3] (<class 'list'>)")

        self.checkRaises(
            (1, 2, 3), actual=[1, 2, 3],
            message=expected,
            strict=True
            )

    def test_float_subclass_strict(self):
        class TestFloat(float): pass
        compare(TestFloat(0.75), TestFloat(0.75), strict=True)

    def test_old_style_classes_same(self):
        class X: pass
        compare(X, X)

    def test_old_style_classes_different(self):
        if py_33_plus:
            expected = (
                "<class 'testfixtures.tests.test_compare.TestCompare."
                "test_old_style_classes_different.<locals>.X'>"
                " != "
                "<class 'testfixtures.tests.test_compare.TestCompare."
                "test_old_style_classes_different.<locals>.Y'>"
                )
        elif PY3:
            expected = (
                "<class 'testfixtures.tests.test_compare.X'>"
                " != "
                "<class 'testfixtures.tests.test_compare.Y'>"
                )
        else:
            expected = (
                "<class testfixtures.tests.test_compare.X at ...>"
                " != "
                "<class testfixtures.tests.test_compare.Y at ...>"
                )
        
        class X: pass
        class Y: pass
        self.checkRaises(X, Y, expected)

    def test_show_whitespace(self):
        # does nothing! ;-)
        self.checkRaises(
            ' x \n\r',' x \n \t',
            "' x \\n\\r' != ' x \\n \\t'",
            show_whitespace=True
            )

    def test_show_whitespace_long(self):
        self.checkRaises(
            "\t         \n  '",'\r     \n  ',
            '\n@@ -1,2 +1,2 @@\n'
            '-\'\\t         \\n\'\n'
            '-"  \'"\n'
            '+\'\\r     \\n\'\n'
            '+\'  \'',
            show_whitespace=True
            )

    def test_show_whitespace_long_expected_actual(self):
        self.checkRaises(
            "\t         \n  '", actual='\r     \n  ',
            message='\n--- expected\n+++ actual\n@@ -1,2 +1,2 @@\n'
            '-\'\\t         \\n\'\n'
            '-"  \'"\n'
            '+\'\\r     \\n\'\n'
            '+\'  \'',
            show_whitespace=True
            )

    def test_show_whitespace_equal(self):
        compare('x', 'x', show_whitespace=True)

    def test_show_whitespace_not_used_because_of_other_difference(self):
        self.checkRaises(
            (1, 'a'),
            (2, 'b'),
            "sequence not as expected:\n"
            "\n"
            "same:\n"
            "()\n"
            "\n"
            "first:\n"
            "(1, 'a')\n"
            "\n"
            "second:\n"
            "(2, 'b')",
            show_whitespace=False
            )

    def test_include_trailing_whitespace(self):
        self.checkRaises(
            ' x \n',' x  \n',
            "' x \\n' != ' x  \\n'"
            )

    def test_ignore_trailing_whitespace(self):
        compare(' x \t\n',' x\t  \n',trailing_whitespace=False)

    def test_ignore_trailing_whitespace_non_string(self):
        self.checkRaises(
            1, '',
            "1 != ''",
            trailing_whitespace=False
            )

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
                '    a\nb', blanklines=False)

    def test_ignore_blank_lines_non_string(self):
        self.checkRaises(
            1, '',
            "1 != ''",
            blanklines=False
            )

    def test_supply_comparer(self):
        def compare_dict(x, y, context):
            self.assertEqual(x, {1:1})
            self.assertEqual(y, {2:2})
            self.assertEqual(context.get_option('foo'), 'bar')
            return 'not equal'
        with ShouldRaise(AssertionError('not equal')):
            compare({1:1}, {2:2},
                    foo='bar',
                    comparers={dict: compare_dict})

    def test_register_more_specific(self):
        class_ = namedtuple('Test', 'x')
        with ShouldRaise(AssertionError('compare class_')):
            compare(class_(1), class_(2),
                    comparers={
                    tuple: Mock(return_value='compare tuple'),
                    class_: Mock(return_value='compare class_')
                    })

    def test_extra_comparers_leave_existing(self):
        class MyObject(object):
            def __init__(self, name):
                self.name = name
            def __repr__(self):
                return 'MyObject instance'
        def compare_my_object(x, y, context):
            return '%s != %s' % (x.name, y.name)
        with Replacer() as r:
            r.replace('testfixtures.comparison._registry', {
                    list: compare_sequence,
                    })
            self.checkRaises(
                [1, MyObject('foo')], [1, MyObject('bar')],
                "sequence not as expected:\n"
                "\n"
                "same:\n"
                "[1]\n"
                "\n"
                "first:\n"
                "[MyObject instance]\n"
                "\n"
                "second:\n"
                "[MyObject instance]\n"
                "\n"
                "While comparing [1]: foo != bar",
                comparers={MyObject: compare_my_object}
                )

    def test_list_subclass(self):
        m = Mock()
        m.aCall()
        # Mock().method_calls is a list subclass
        self.checkRaises(
            [call.bCall()], m.method_calls,
            "sequence not as expected:\n\n"
            "same:\n[]\n\n"
            "first:\n[call.bCall()]\n\n"
            "second:\n[call.aCall()]"
            )

    def test_strict_okay(self):
        m = object()
        compare(m, m, strict=True)

    def test_strict_comparer_supplied(self):
        compare_obj = Mock()
        compare_obj.return_value = 'not equal'

        self.checkRaises(
            object(), object(),
            "not equal",
            strict=True,
            comparers={object: compare_obj},
            )

    def test_strict_default_comparer(self):
        class MyList(list): pass
        # default comparer used!
        self.checkRaises(
            MyList((1, 2, 3)), MyList((1, 2, 4)),
            "sequence not as expected:\n"
            "\n"
            "same:\n"
            "[1, 2]\n"
            "\n"
            "first:\n"
            "[3]\n"
            "\n"
            "second:\n"
            "[4]",
            strict=True,
            )

    def test_list_subclass_strict(self):
        m = Mock()
        m.aCall()
        self.checkRaises(
            [call.aCall()], m.method_calls,
            ("[call.aCall()] (<{0} 'list'>) != [call.aCall()] "
             "({1})").format(class_type_name, call_list_repr),
            strict=True,
            )

    def test_list_subclass_long_strict(self):
        m = Mock()
        m.call('X'*20)
        self.checkRaises(
            [call.call('Y'*20)], m.method_calls,
            ("[call.call('YYYYYYYYYYYYYYYYYY... "
             "(<{0} 'list'>) != "
             "[call.call('XXXXXXXXXXXXXXXXXX... "
             "({1})").format(class_type_name, call_list_repr),
            strict=True,
            )

    def test_prefix(self):
        self.checkRaises(1, 2, 'wrong number of orders: 1 != 2',
                         prefix='wrong number of orders')

    def test_prefix_multiline(self):
        self.checkRaises(
            'x'*5+'\n'+'y'*5,'x'*5+'\n'+'z'*5,
            "file content: \n@@ -1,2 +1,2 @@\n xxxxx\n-yyyyy\n+zzzzz",
            prefix='file content'
            )

    def test_generator_with_non_generator(self):
        self.checkRaises(
            generator(1, 2, 3), None,
            '<generator object generator at ...> != None',
            )

    def test_generator_with_buggy_generator(self):
        def bad_gen():
            yield 1
            # raising a TypeError here is important :-/
            raise TypeError('foo')

        with ShouldRaise(TypeError('foo')):
            compare(generator(1, 2, 3), bad_gen())

    def test_nested_dict_tuple_values_different(self):
        self.checkRaises(
            dict(x=(1, 2, 3)), dict(x=(1, 2, 4)),
            "dict not as expected:\n"
            "\n"
            "values differ:\n"
            "'x': (1, 2, 3) != (1, 2, 4)\n"
            '\n'
            "While comparing ['x']: sequence not as expected:\n"
            "\n"
            "same:\n"
            "(1, 2)\n"
            "\n"
            "first:\n"
            "(3,)\n"
            "\n"
            "second:\n"
            "(4,)"
            )

    def test_nested_dict_different(self):
        self.checkRaises(
            dict(x=dict(y=1)), dict(x=dict(y=2)),
            "dict not as expected:\n"
            "\n"
            "values differ:\n"
            "'x': {'y': 1} != {'y': 2}\n"
            '\n'
            "While comparing ['x']: dict not as expected:\n"
            "\n"
            "values differ:\n"
            "'y': 1 != 2"
            )

    def test_tuple_list_different(self):
        self.checkRaises(
            (1, [2, 3, 5]), (1, [2, 4, 5]),
            "sequence not as expected:\n"
            "\n"
            "same:\n"
            "(1,)\n"
            "\n"
            "first:\n"
            "([2, 3, 5],)\n"
            "\n"
            "second:\n"
            "([2, 4, 5],)\n"
            "\n"
            "While comparing [1]: sequence not as expected:\n"
            "\n"
            "same:\n"
            "[2]\n"
            "\n"
            "first:\n"
            "[3, 5]\n"
            "\n"
            "second:\n"
            "[4, 5]"
            )

    def test_tuple_long_strings_different(self):
        self.checkRaises(
            (1, 2, "foo\nbar\nbaz\n", 4),
            (1, 2, "foo\nbob\nbaz\n", 4),
            "sequence not as expected:\n"
            "\n"
            "same:\n"
            "(1, 2)\n"
            "\n"
            "first:\n"
            "('foo\\nbar\\nbaz\\n', 4)\n"
            "\n"
            "second:\n"
            "('foo\\nbob\\nbaz\\n', 4)\n"
            "\n"
            "While comparing [2]: \n"
            "@@ -1,4 +1,4 @@\n"
            # check that show_whitespace bubbles down
            " 'foo\\n'\n"
            "-'bar\\n'\n"
            "+'bob\\n'\n"
            " 'baz\\n'\n"
            " ''",
            show_whitespace=True
            )

    def test_dict_multiple_differences(self):
        self.checkRaises(
            dict(x=(1,2,3), y=(4, 5, 6,)),
            dict(x=(1,2,4), y=(4, 5, 7,)),
            "dict not as expected:\n"
            "\n"
            "values differ:\n"
            "'x': (1, 2, 3) != (1, 2, 4)\n"
            "'y': (4, 5, 6) != (4, 5, 7)\n"
            "\n"
            "While comparing ['x']: sequence not as expected:\n"
            "\n"
            "same:\n"
            "(1, 2)\n"
            "\n"
            "first:\n"
            "(3,)\n"
            "\n"
            "second:\n"
            "(4,)\n"
            "\n"
            "While comparing ['y']: sequence not as expected:\n"
            "\n"
            "same:\n"
            "(4, 5)\n"
            "\n"
            "first:\n"
            "(6,)\n"
            "\n"
            "second:\n"
            "(7,)"
            )

    def test_deep_breadcrumbs(self):
        obj1 = singleton('obj1')
        obj2 = singleton('obj2')
        gen1 = generator(obj1, obj2)
        gen2 = generator(obj1, )
        # dict -> list -> tuple -> generator
        self.checkRaises(
            dict(x=[1, ('a', 'b', gen1), 3], y=[3, 4]),
            dict(x=[1, ('a', 'b', gen2), 3], y=[3, 4]), (
                "dict not as expected:\n"
                "\n"
                "same:\n"
                "['y']\n"
                "\n"
                "values differ:\n"
                "'x': [1, ('a', 'b', {gen1}), 3] != [1, ('a', 'b', {gen2}), 3]\n"
                "\n"
                "While comparing ['x']: sequence not as expected:\n"
                "\n"
                "same:\n"
                "[1]\n"
                "\n"
                "first:\n"
                "[('a', 'b', {gen1}), 3]\n"
                "\n"
                "second:\n"
                "[('a', 'b', {gen2}), 3]\n"
                "\n"
                "While comparing ['x'][1]: sequence not as expected:\n"
                "\n"
                "same:\n"
                "('a', 'b')\n"
                "\n"
                "first:\n"
                "({gen1},)\n"
                "\n"
                "second:\n"
                "({gen2},)\n"
                "\n"
                "While comparing ['x'][1][2]: sequence not as expected:\n"
                "\n"
                "same:\n"
                "(<obj1>,)\n"
                "\n"
                "first:\n"
                "(<obj2>,)\n"
                "\n"
                "second:\n"
                "()"
                ).format(gen1=hexsub(repr(gen1)),
                         gen2=hexsub(repr(gen2)))
            )

    def test_nested_strict_only_type_difference(self):
        MyTuple = namedtuple('MyTuple', 'x y z')
        type_repr = repr(MyTuple)
        tuple_repr = repr(tuple)
        self.checkRaises(
            [MyTuple(1, 2, 3)], [(1, 2, 3)], (
            "sequence not as expected:\n"
            "\n"
            "same:\n"
            "[]\n"
            "\n"
            "first:\n"
            "[MyTuple(x=1, y=2, z=3)]\n"
            "\n"
            "second:\n"
            "[(1, 2, 3)]\n"
            "\n"
            "While comparing [0]: MyTuple(x=1, y=2, z=3) "
            "(%s) "
            "!= (1, 2, 3) "
            "(%s)") % (type_repr, tuple_repr),
            strict=True
            )

    def test_strict_nested_different(self):
        if py_2:
            expected = "[1, 2] (<type 'list'>) != (1, 3) (<type 'tuple'>)"
        else:
            expected = "[1, 2] (<class 'list'>) != (1, 3) (<class 'tuple'>)"

        self.checkRaises(
            (1, 2, [1, 2]), (1, 2, (1, 3)),
            "sequence not as expected:\n"
            "\n"
            "same:\n"
            "(1, 2)\n"
            "\n"
            "first:\n"
            "([1, 2],)\n"
            "\n"
            "second:\n"
            "((1, 3),)"
            "\n\n"
            "While comparing [2]: " + expected,
            strict=True,
            )

    def test_namedtuple_equal(self):
        class_ = namedtuple('Foo', 'x')
        compare(class_(1), class_(1))

    def test_namedtuple_same_type(self):
        class_ = namedtuple('Foo', 'x y')
        self.checkRaises(
            class_(1, 2), class_(1, 3),
            "Foo not as expected:\n\n"
            "same:\n"
            "['x']\n\n"
            "values differ:\n"
            "'y': 2 != 3"
            )

    def test_namedtuple_different_type(self):
        class_a = namedtuple('Foo', 'x y')
        class_b = namedtuple('Bar', 'x y z')
        self.checkRaises(
            class_a(1, 2), class_b(1, 2, 3),
            "Foo(x=1, y=2) (<class 'testfixtures.tests.test_compare.Foo'>) != "
            "Bar(x=1, y=2, z=3) (<class 'testfixtures.tests.test_compare.Bar'>)"
            )

    def test_dict_with_list(self):
        self.checkRaises(
            {1: 'one', 2: 'two'}, [1, 2],
            "{1: 'one', 2: 'two'} != [1, 2]"
        )


a = singleton('a')
b = singleton('b')


class TestGetExpectedActual(TestCase):
    """
    Specific test cases for the _get_expected_auctual() helper method.
    """
    def test_unnamed_arguments(self):
        self.assertEqual(_get_expected_actual(a, b, not_there, not_there),
                         (a, b, False))

    def test_only_expected_named(self):
        self.assertEqual(_get_expected_actual(a, not_there, b, not_there),
                         (b, a, True))

    def test_only_actual_named(self):
        self.assertEqual(_get_expected_actual(a, not_there, not_there, b),
                         (a, b, True))

    def test_both_named_arguments(self):
        self.assertEqual(_get_expected_actual(not_there, not_there, a, b),
                         (a, b, True))

    msg = 'Exactly 2 of the arguments (x, y, expected, actual) must be specified.'

    def test_no_arguments_raises(self):
        with ShouldRaise(ValueError(self.msg)):
            _get_expected_actual(not_there, not_there, not_there, not_there)

    def test_one_arguments_raises(self):
        with ShouldRaise(ValueError(self.msg)):
            _get_expected_actual(None, not_there, not_there, not_there)
        with ShouldRaise(ValueError(self.msg)):
            _get_expected_actual(not_there, None, not_there, not_there)
        with ShouldRaise(ValueError(self.msg)):
            _get_expected_actual(not_there, not_there, None, not_there)
        with ShouldRaise(ValueError(self.msg)):
            _get_expected_actual(not_there, not_there, not_there, None)

    def test_three_arguments_raises(self):
        with ShouldRaise(ValueError(self.msg)):
            _get_expected_actual(None, not_there, not_there, not_there)
        with ShouldRaise(ValueError(self.msg)):
            _get_expected_actual(not_there, None, not_there, not_there)
        with ShouldRaise(ValueError(self.msg)):
            _get_expected_actual(not_there, not_there, None, not_there)
        with ShouldRaise(ValueError(self.msg)):
            _get_expected_actual(not_there, not_there, not_there, None)

    def test_four_arguments_raises(self):
        with ShouldRaise(ValueError(self.msg)):
            _get_expected_actual(None, None, None, None)

    # Test the pathological case where someone passes only y as a named argument
    def test_y_without_x_raises(self):
        msg = 'Must specify x and y together, or x with one of expected/actual.'
        with ShouldRaise(ValueError(msg)):
            _get_expected_actual(not_there, None, None, not_there)
        with ShouldRaise(ValueError(msg)):
            _get_expected_actual(not_there, None, not_there, None)
