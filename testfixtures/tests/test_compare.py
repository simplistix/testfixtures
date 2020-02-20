from datetime import date, datetime
from decimal import Decimal

from functools import partial

from collections import namedtuple

from testfixtures.shouldraise import ShouldAssert
from testfixtures.tests.sample1 import SampleClassA, SampleClassB, Slotted
from testfixtures.mock import Mock, call
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
    BytesLiteral, UnicodeLiteral,
    PY2, PY_37_PLUS, ABC
)
from testfixtures.comparison import compare_sequence, compare_object
from unittest import TestCase

hexaddr = compile('0x[0-9A-Fa-f]+')


def hexsub(raw):
    return hexaddr.sub('...', raw)

call_list_repr = repr(Mock().mock_calls.__class__)

marker = object()

_compare = compare


def check_raises(x=marker, y=marker, message=None, regex=None,
                 compare=compare, **kw):
    args = []
    for value in x, y:
        if value is not marker:
            args.append(value)
    for value in 'x', 'y':
        explicit = 'explicit_{}'.format(value)
        if explicit in kw:
            kw[value] = kw[explicit]
            del kw[explicit]
    try:
        compare(*args, **kw)
    except Exception as e:
        if not isinstance(e, AssertionError):  # pragma: no cover
            raise
        actual = hexsub(e.args[0])
        if message is not None:
            # handy for debugging, but can't be relied on for tests!
            _compare(actual, expected=message, show_whitespace=True)
            assert actual == message
        else:
            if not regex.match(actual):  # pragma: no cover
                raise AssertionError(
                    '%r did not match %r' % (actual, regex.pattern)
                )
    else:
        raise AssertionError('No exception raised!')


class CompareHelper(object):

    def check_raises(self, *args, **kw):
        check_raises(*args, **kw)


class TestCompare(CompareHelper, TestCase):

    def test_object_same(self):
        o = object()
        compare(o, o)

    def test_object_diff(self):
        self.check_raises(
            object(), object(),
            '<object object at ...> != <object object at ...>'
        )

    def test_different_types(self):
        self.check_raises('x', 1, "'x' != 1")

    def test_number_same(self):
        compare(1, 1)

    def test_number_different(self):
        self.check_raises(1, 2, '1 != 2')

    def test_decimal_different(self):
        self.check_raises(Decimal(1), Decimal(2),
                          "Decimal('1') != Decimal('2')")

    def test_different_with_labels(self):
        self.check_raises(1, 2, '1 (expected) != 2 (actual)',
                          x_label='expected', y_label='actual')

    def test_string_same(self):
        compare('x', 'x')

    def test_unicode_string_different(self):
        if PY2:
            expected = "u'a' != 'b'"
        else:
            expected = "'a' != b'b'"
        self.check_raises(
            UnicodeLiteral('a'), BytesLiteral('b'),
            expected
            )

    def test_bytes_different(self):
        if PY2:
            expected = (
                "\n" 
                "'12345678901'\n"
                '!=\n'
                "'12345678902'"
            )
        else:
            expected = (
                "\n" 
                "b'12345678901'\n"
                '!=\n'
                "b'12345678902'"
            )
        self.check_raises(
            BytesLiteral('12345678901'),
            BytesLiteral('12345678902'),
            expected
            )

    def test_bytes_same_strict(self):
        compare(actual=b'', expected=b'', strict=True)

    if PY3:
        def test_moar_bytes_different(self):
            self.check_raises(
                actual=b'{"byte_pound":"b\'\\\\xa3\'"}',
                expected=b'{"byte_pound":"b\\\'\\xa3\'"}',
                message = (
                    "\n"
                    "b'{\"byte_pound\":\"b\\\\\\'\\\\xa3\\\'\"}' (expected)\n"
                    '!=\n'
                    "b'{\"byte_pound\":\"b\\\'\\\\\\\\xa3\\\'\"}' (actual)"
                )
            )

    def test_string_diff_short(self):
        self.check_raises(
            '\n'+('x'*9), '\n'+('y'*9),
            "'\\nxxxxxxxxx' != '\\nyyyyyyyyy'"
            )

    def test_string_diff_long(self):
        self.check_raises(
            'x'*11, 'y'*11,
            "\n'xxxxxxxxxxx'\n!=\n'yyyyyyyyyyy'"
            )

    def test_string_diff_long_newlines(self):
        self.check_raises(
            'x'*5+'\n'+'y'*5, 'x'*5+'\n'+'z'*5,
            "\n--- first\n+++ second\n@@ -1,2 +1,2 @@\n xxxxx\n-yyyyy\n+zzzzz"
            )

    def test_string_diff_short_labels(self):
        self.check_raises(
            '\n'+('x'*9), '\n'+('y'*9),
            "'\\nxxxxxxxxx' (expected) != '\\nyyyyyyyyy' (actual)",
            x_label='expected',
            y_label='actual'
            )

    def test_string_diff_long_labels(self):
        self.check_raises(
            'x'*11, 'y'*11,
            "\n'xxxxxxxxxxx' (expected)\n!=\n'yyyyyyyyyyy' (actual)",
            x_label='expected',
            y_label='actual'
            )

    def test_string_diff_long_newlines_labels(self):
        self.check_raises(
            'x'*5+'\n'+'y'*5, 'x'*5+'\n'+'z'*5,
            "\n--- expected\n+++ actual\n"
            "@@ -1,2 +1,2 @@\n xxxxx\n-yyyyy\n+zzzzz",
            x_label='expected',
            y_label='actual'
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
        compare(e1, e2)

    def test_exception_different_object_c_wrapper(self):
        e1 = ValueError('some message')
        e2 = ValueError('some message')
        compare(C(e1), e2)

    def test_exception_diff(self):
        e1 = ValueError('some message')
        e2 = ValueError('some other message')
        if PY_37_PLUS:
            self.check_raises(
                e1, e2,
                "ValueError('some message') != ValueError('some other message')"
                )
        else:
            self.check_raises(
                e1, e2,
                "ValueError('some message',) != ValueError('some other message',)"
                )

    def test_exception_diff_c_wrapper(self):
        e1 = ValueError('some message')
        e2 = ValueError('some other message')
        self.check_raises(
            C(e1), e2,
            ("\n"
             "<C(failed):{}.ValueError>\n"
             "attributes differ:\n"
             "'args': ('some message',) (Comparison) "
             "!= ('some other message',) (actual)\n"
             "</C>"
             " != ValueError('some other message'{})"
             ).format(exception_module,
                      '' if PY_37_PLUS else ','))

    def test_sequence_long(self):
        self.check_raises(
            ['quite a long string 1', 'quite a long string 2',
             'quite a long string 3', 'quite a long string 4',
             'quite a long string 5', 'quite a long string 6',
             'quite a long string 7', 'quite a long string 8'],
            ['quite a long string 1', 'quite a long string 2',
             'quite a long string 3', 'quite a long string 4',
             'quite a long string 9', 'quite a long string 10',
             'quite a long string 11', 'quite a long string 12'],
            "sequence not as expected:\n\n"
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
            " 'quite a long string 12']\n"
            "\n"
            "While comparing [4]: \n"
            "'quite a long string 5'\n"
            "!=\n"
            "'quite a long string 9'"
            )

    def test_sequence_different_labels_supplied(self):
        self.check_raises(
            [1, 2, 3], [1, 2, 4],
            "sequence not as expected:\n\n"
            "same:\n"
            "[1, 2]\n\n"
            "expected:\n"
            "[3]\n\n"
            "actual:\n"
            "[4]",
            x_label='expected',
            y_label='actual',
            )

    def test_list_same(self):
        compare([1, 2, 3], [1, 2, 3])

    def test_list_different(self):
        self.check_raises(
            [1, 2, 3], [1, 2, 4],
            "sequence not as expected:\n\n"
            "same:\n"
            "[1, 2]\n\n"
            "first:\n"
            "[3]\n\n"
            "second:\n"
            "[4]"
            )

    def test_list_different_float(self):
        self.check_raises(
            [1, 2, 3.0], [1, 2, 4.0],
            "sequence not as expected:\n\n"
            "same:\n"
            "[1, 2]\n\n"
            "first:\n"
            "[3.0]\n\n"
            "second:\n"
            "[4.0]"
            )

    def test_list_different_decimal(self):
        self.check_raises(
            [1, 2, Decimal(3)], [1, 2, Decimal(4)],
            "sequence not as expected:\n\n"
            "same:\n"
            "[1, 2]\n\n"
            "first:\n"
            "[Decimal('3')]\n\n"
            "second:\n"
            "[Decimal('4')]"
            )

    def test_list_totally_different(self):
        self.check_raises(
            [1], [2],
            "sequence not as expected:\n\n"
            "same:\n"
            "[]\n\n"
            "first:\n"
            "[1]\n\n"
            "second:\n"
            "[2]"
            )

    def test_list_first_shorter(self):
        self.check_raises(
            [1, 2], [1, 2, 3],
            "sequence not as expected:\n\n"
            "same:\n[1, 2]\n\n"
            "first:\n[]\n\n"
            "second:\n[3]"
            )

    def test_list_second_shorter(self):
        self.check_raises(
            [1, 2, 3], [1, 2],
            "sequence not as expected:\n\n"
            "same:\n[1, 2]\n\n"
            "first:\n[3]\n\n"
            "second:\n[]"
            )

    def test_dict_same(self):
        compare(dict(x=1), dict(x=1))

    def test_dict_first_missing_keys(self):
        self.check_raises(
            dict(), dict(z=3),
            "dict not as expected:\n"
            "\n"
            "in second but not first:\n"
            "'z': 3"
            )

    def test_dict_second_missing_keys(self):
        self.check_raises(
            dict(z=3), dict(),
            "dict not as expected:\n"
            "\n"
            "in first but not second:\n"
            "'z': 3"
            )

    def test_dict_values_different(self):
        self.check_raises(
            dict(x=1), dict(x=2),
            "dict not as expected:\n"
            "\n"
            "values differ:\n"
            "'x': 1 != 2"
            )

    def test_dict_labels_specified(self):
        self.check_raises(
            dict(x=1, y=2), dict(x=2, z=3),
            "dict not as expected:\n"
            "\n"
            "in expected but not actual:\n"
            "'y': 2\n"
            "\n"
            "in actual but not expected:\n"
            "'z': 3\n"
            "\n"
            "values differ:\n"
            "'x': 1 (expected) != 2 (actual)",
            x_label='expected',
            y_label='actual'
            )

    def test_dict_tuple_keys_same_value(self):
        compare({(1, 2): None}, {(1, 2): None})

    def test_dict_tuple_keys_different_value(self):
        self.check_raises(
            {(1, 2): 3},
            {(1, 2): 42},
            "dict not as expected:\n"
            "\n"
            "values differ:\n"
            "(1, 2): 3 != 42"
            )

    def test_dict_full_diff(self):
        self.check_raises(
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

    def test_dict_consistent_ordering(self):
        self.check_raises(
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

    def test_dict_consistent_ordering_types_same(self):
        if PY3:
            same = "[6, None]\n"
        else:
            same = "[None, 6]\n"

        self.check_raises(
            {None: 1, 6: 2, 1: 3},
            {None: 1, 6: 2, 1: 4},
            "dict not as expected:\n"
            "\n"+
            'same:\n'+
            same+
            "\n"
            "values differ:\n"
            "1: 3 != 4"
            )

    def test_dict_consistent_ordering_types_x_not_y(self):
        self.check_raises(
            {None: 1, 3: 2},
            {},
            "dict not as expected:\n"
            "\n"
            "in first but not second:\n"
            "3: 2\n"
            "None: 1"
            )

    def test_dict_consistent_ordering_types_y_not_x(self):
        self.check_raises(
            {},
            {None: 1, 3: 2},
            "dict not as expected:\n"
            "\n"
            "in second but not first:\n"
            "3: 2\n"
            "None: 1"
            )

    def test_dict_consistent_ordering_types_value(self):
        self.check_raises(
            {None: 1, 6: 2},
            {None: 3, 6: 4},
            "dict not as expected:\n"
            "\n"
            "values differ:\n"
            "6: 2 != 4\n"
            "None: 1 != 3"
            )

    def test_set_same(self):
        compare(set([1]), set([1]))

    def test_set_first_missing_keys(self):
        self.check_raises(
            set(), set([3]),
            "set not as expected:\n"
            "\n"
            "in second but not first:\n"
            "[3]\n"
            '\n'
            )

    def test_set_second_missing_keys(self):
        self.check_raises(
            set([3]), set(),
            "set not as expected:\n"
            "\n"
            "in first but not second:\n"
            "[3]\n"
            '\n'
            )

    def test_set_full_diff(self):
        self.check_raises(
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

    def test_set_type_ordering(self):
        self.check_raises(
            {None, 1}, {'', 2},
            "set not as expected:\n"
            "\n"
            "in first but not second:\n"
            "[1, None]\n"
            '\n'
            "in second but not first:\n"
            "['', 2]\n"
            '\n'
            )

    def test_set_labels(self):
        self.check_raises(
            set([1, 2, 4]), set([1, 3, 5]),
            "set not as expected:\n"
            "\n"
            "in expected but not actual:\n"
            "[2, 4]\n"
            '\n'
            "in actual but not expected:\n"
            "[3, 5]\n"
            '\n',
            x_label='expected',
            y_label='actual',
        )

    def test_tuple_same(self):
        compare((1, 2, 3), (1, 2, 3))

    def test_tuple_different(self):
        self.check_raises(
            (1, 2, 3), (1, 2, 4),
            "sequence not as expected:\n\n"
            "same:\n(1, 2)\n\n"
            "first:\n(3,)\n\n"
            "second:\n(4,)"
            )

    def test_tuple_totally_different(self):
        self.check_raises(
            (1, ), (2, ),
            "sequence not as expected:\n\n"
            "same:\n()\n\n"
            "first:\n(1,)\n\n"
            "second:\n(2,)"
            )

    def test_tuple_first_shorter(self):
        self.check_raises(
            (1, 2), (1, 2, 3),
            "sequence not as expected:\n\n"
            "same:\n(1, 2)\n\n"
            "first:\n()\n\n"
            "second:\n(3,)"
            )

    def test_tuple_second_shorter(self):
        self.check_raises(
            (1, 2, 3), (1, 2),
            "sequence not as expected:\n\n"
            "same:\n(1, 2)\n\n"
            "first:\n(3,)\n\n"
            "second:\n()"
            )

    def test_generator_same(self):
        compare(generator(1, 2, 3), generator(1, 2, 3))

    def test_generator_different(self):
        self.check_raises(
            generator(1, 2, 3), generator(1, 2, 4),
            "sequence not as expected:\n\n"
            "same:\n(1, 2)\n\n"
            "first:\n(3,)\n\n"
            "second:\n(4,)"
            )

    def test_generator_totally_different(self):
        self.check_raises(
            generator(1, ), generator(2, ),
            "sequence not as expected:\n\n"
            "same:\n()\n\n"
            "first:\n(1,)\n\n"
            "second:\n(2,)"
            )

    def test_generator_first_shorter(self):
        self.check_raises(
            generator(1, 2), generator(1, 2, 3),
            "sequence not as expected:\n\n"
            "same:\n(1, 2)\n\n"
            "first:\n()\n\n"
            "second:\n(3,)"
            )

    def test_generator_second_shorted(self):
        self.check_raises(
            generator(1, 2, 3), generator(1, 2),
            "sequence not as expected:\n\n"
            "same:\n(1, 2)\n\n"
            "first:\n(3,)\n\n"
            "second:\n()"
            )

    def test_nested_generator_different(self):
        self.check_raises(
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
        compare((1, 2, 3), generator(1, 2, 3))

    def test_sequence_and_generator_strict(self):
        expected = compile(
            "\(1, 2, 3\) \(<(class|type) 'tuple'>\) \(expected\) != "
            "<generator object (generator )?at... "
            "\(<(class|type) 'generator'>\) \(actual\)"
            )
        self.check_raises(
            (1, 2, 3), generator(1, 2, 3),
            regex=expected,
            strict=True,
            x_label='expected',
            y_label='actual',
            )

    def test_generator_and_sequence(self):
        compare(generator(1, 2, 3), (1, 2, 3))

    def test_iterable_with_iterable_same(self):
        compare(xrange(1, 4), xrange(1, 4))

    def test_iterable_with_iterable_different(self):
        self.check_raises(
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
        compare(xrange(1, 4), generator(1, 2, 3))

    def test_iterable_and_generator_strict(self):
        expected = compile(
            "x?range\(1, 4\) \(<(class|type) 'x?range'>\) != "
            "<generator object (generator )?at... "
            "\(<(class|type) 'generator'>\)"
            )
        self.check_raises(
            xrange(1, 4), generator(1, 2, 3),
            regex=expected,
            strict=True,
            )

    def test_generator_and_iterable(self):
        compare(generator(1, 2, 3), xrange(1, 4))

    def test_tuple_and_list(self):
        compare((1, 2, 3), [1, 2, 3])

    def test_tuple_and_list_strict(self):
        if PY2:
            expected = ("(1, 2, 3) (<type 'tuple'>) != "
                        "[1, 2, 3] (<type 'list'>)")
        else:
            expected = ("(1, 2, 3) (<class 'tuple'>) != "
                        "[1, 2, 3] (<class 'list'>)")

        self.check_raises(
            (1, 2, 3), [1, 2, 3],
            expected,
            strict=True
            )

    def test_float_subclass_strict(self):
        class TestFloat(float):
            pass
        compare(TestFloat(0.75), TestFloat(0.75), strict=True)

    def test_old_style_classes_same(self):
        class X:
            pass
        compare(X, X)

    def test_old_style_classes_different(self):
        if PY3:
            expected = (
                "<class 'testfixtures.tests.test_compare.TestCompare."
                "test_old_style_classes_different.<locals>.X'>"
                " != "
                "<class 'testfixtures.tests.test_compare.TestCompare."
                "test_old_style_classes_different.<locals>.Y'>"
                )
        else:
            expected = (
                "<class testfixtures.tests.test_compare.X at ...>"
                " != "
                "<class testfixtures.tests.test_compare.Y at ...>"
                )

        class X:
            pass

        class Y:
            pass
        self.check_raises(X, Y, expected)

    def test_new_style_classes_same(self):
        class X(object):
            pass
        compare(X, X)

    def test_new_style_classes_different(self):
        if PY3:
            expected = (
                "<class 'testfixtures.tests.test_compare.TestCompare."
                "test_new_style_classes_different.<locals>.X'>"
                " != "
                "<class 'testfixtures.tests.test_compare.TestCompare."
                "test_new_style_classes_different.<locals>.Y'>"
                )
        else:
            expected = (
                "<class 'testfixtures.tests.test_compare.X'>"
                " != "
                "<class 'testfixtures.tests.test_compare.Y'>"
                )

        class X(object):
            pass

        class Y(object):
            pass
        self.check_raises(X, Y, expected)

    def test_show_whitespace(self):
        # does nothing! ;-)
        self.check_raises(
            ' x \n\r', ' x \n \t',
            "' x \\n\\r' != ' x \\n \\t'",
            show_whitespace=True
            )

    def test_show_whitespace_long(self):
        self.check_raises(
            "\t         \n  '", '\r     \n  ',
            '\n--- first\n'
            '+++ second\n'
            '@@ -1,2 +1,2 @@\n'
            '-\'\\t         \\n\'\n'
            '-"  \'"\n'
            '+\'\\r     \\n\'\n'
            '+\'  \'',
            show_whitespace=True
            )

    def test_show_whitespace_equal(self):
        compare('x', 'x', show_whitespace=True)

    def test_show_whitespace_not_used_because_of_other_difference(self):
        self.check_raises(
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
        self.check_raises(
            ' x \n', ' x  \n',
            "' x \\n' != ' x  \\n'"
            )

    def test_ignore_trailing_whitespace(self):
        compare(' x \t\n', ' x\t  \n', trailing_whitespace=False)

    def test_ignore_trailing_whitespace_non_string(self):
        self.check_raises(
            1, '',
            "1 != ''",
            trailing_whitespace=False
            )

    def test_ignore_trailing_whitespace_but_respect_leading_whitespace(self):
        # NB: careful: this strips off the last newline too
        #     DON'T use if you care about that!
        self.check_raises(
            'a\n b\n  c\n',
            'a\nb\nc\n',
            "'a\\n b\\n  c' != 'a\\nb\\nc'",
            trailing_whitespace=False
            )

    def test_include_blank_lines(self):
        self.check_raises(
            '\n \n', '\n  ',
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
        self.check_raises(
            1, '',
            "1 != ''",
            blanklines=False
            )

    def test_supply_comparer(self):
        def compare_dict(x, y, context):
            self.assertEqual(x, {1: 1})
            self.assertEqual(y, {2: 2})
            self.assertEqual(context.get_option('foo'), 'bar')
            return 'not equal'
        with ShouldAssert('not equal'):
            compare({1: 1}, {2: 2},
                    foo='bar',
                    comparers={dict: compare_dict})

    def test_register_more_specific(self):
        class_ = namedtuple('Test', 'x')
        with ShouldAssert('compare class_'):
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
            self.check_raises(
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
        class  MyList(list): pass
        a_list = MyList([1])
        b_list = MyList([2])
        self.check_raises(
            a_list, b_list,
            "sequence not as expected:\n\n"
            "same:\n[]\n\n"
            "first:\n[1]\n\n"
            "second:\n[2]"
            )

    def test_strict_okay(self):
        m = object()
        compare(m, m, strict=True)

    def test_strict_comparer_supplied(self):

        compare_obj = Mock()
        compare_obj.return_value = 'not equal'

        self.check_raises(
            object(), object(),
            "not equal",
            strict=True,
            comparers={object: compare_obj},
            )

    def test_strict_default_comparer(self):
        class MyList(list):
            pass
        # default comparer used!
        self.check_raises(
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
        self.check_raises(
            [call.aCall()], m.method_calls,
            ("[call.aCall()] (<{0} 'list'>) != [call.aCall()] "
             "({1})").format(class_type_name, call_list_repr),
            strict=True,
            )

    def test_list_subclass_long_strict(self):
        m = Mock()
        m.call('X'*20)
        self.check_raises(
            [call.call('Y'*20)], m.method_calls,
            ("[call.call('YYYYYYYYYYYYYYYYYY... "
             "(<{0} 'list'>) != "
             "[call.call('XXXXXXXXXXXXXXXXXX... "
             "({1})").format(class_type_name, call_list_repr),
            strict=True,
            )

    def test_prefix(self):
        self.check_raises(1, 2, 'wrong number of orders: 1 != 2',
                          prefix='wrong number of orders')

    def test_prefix_multiline(self):
        self.check_raises(
            'x'*5+'\n'+'y'*5, 'x'*5+'\n'+'z'*5,
            "file content: \n--- first\n+++ second\n"
            "@@ -1,2 +1,2 @@\n xxxxx\n-yyyyy\n+zzzzz",
            prefix='file content'
            )

    def test_suffix(self):
        self.check_raises(
            1, 2,
            '1 != 2\n'
            'additional context',
            suffix='additional context',
            )

    def test_labels_multiline(self):
        self.check_raises(
            'x'*5+'\n'+'y'*5, 'x'*5+'\n'+'z'*5,
            "\n--- expected\n+++ actual\n"
            "@@ -1,2 +1,2 @@\n xxxxx\n-yyyyy\n+zzzzz",
            x_label='expected',
            y_label='actual'
            )

    def test_generator_with_non_generator(self):
        self.check_raises(
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
        self.check_raises(
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
        self.check_raises(
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

    def test_nested_dict_empty_but_same(self):
        compare(dict(x=dict()), dict(x=dict()), ignore_eq=True)

    def test_nested_dict_empty_with_keys(self):
        compare(dict(x=dict(x=1)), dict(x=dict(x=1)), ignore_eq=True)

    def test_tuple_list_different(self):
        self.check_raises(
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
        self.check_raises(
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
            "--- first\n"
            "+++ second\n"
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
        self.check_raises(
            dict(x=(1, 2, 3), y=(4, 5, 6, )),
            dict(x=(1, 2, 4), y=(4, 5, 7, )),
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
        self.check_raises(
            dict(x=[1, ('a', 'b', gen1), 3], y=[3, 4]),
            dict(x=[1, ('a', 'b', gen2), 3], y=[3, 4]), (
                "dict not as expected:\n"
                "\n"
                "same:\n"
                "['y']\n"
                "\n"
                "values differ:\n"
                "'x': [1, ('a', 'b', {gen1}), 3] != [1, ('a', 'b', {gen2}), 3]"
                "\n\n"
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

    def test_nested_labels(self):
        obj1 = singleton('obj1')
        obj2 = singleton('obj2')
        gen1 = generator(obj1, obj2)
        gen2 = generator(obj1, )
        # dict -> list -> tuple -> generator
        self.check_raises(
            dict(x=[1, ('a', 'b', gen1), 3], y=[3, 4]),
            dict(x=[1, ('a', 'b', gen2), 3], y=[3, 4]), (
                "dict not as expected:\n"
                "\n"
                "same:\n"
                "['y']\n"
                "\n"
                "values differ:\n"
                "'x': [1, ('a', 'b', {gen1}), 3] (expected) != "
                "[1, ('a', 'b', {gen2}), 3] (actual)\n"
                "\n"
                "While comparing ['x']: sequence not as expected:\n"
                "\n"
                "same:\n"
                "[1]\n"
                "\n"
                "expected:\n"
                "[('a', 'b', {gen1}), 3]\n"
                "\n"
                "actual:\n"
                "[('a', 'b', {gen2}), 3]\n"
                "\n"
                "While comparing ['x'][1]: sequence not as expected:\n"
                "\n"
                "same:\n"
                "('a', 'b')\n"
                "\n"
                "expected:\n"
                "({gen1},)\n"
                "\n"
                "actual:\n"
                "({gen2},)\n"
                "\n"
                "While comparing ['x'][1][2]: sequence not as expected:\n"
                "\n"
                "same:\n"
                "(<obj1>,)\n"
                "\n"
                "expected:\n"
                "(<obj2>,)\n"
                "\n"
                "actual:\n"
                "()"
                ).format(gen1=hexsub(repr(gen1)),
                         gen2=hexsub(repr(gen2))),
            x_label='expected',
            y_label='actual',
            )

    def test_nested_strict_only_type_difference(self):
        MyTuple = namedtuple('MyTuple', 'x y z')
        type_repr = repr(MyTuple)
        tuple_repr = repr(tuple)
        self.check_raises(
            [MyTuple(1, 2, 3)],
            [(1, 2, 3)],
            ("sequence not as expected:\n"
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
        if PY2:
            expected = "[1, 2] (<type 'list'>) != (1, 3) (<type 'tuple'>)"
        else:
            expected = "[1, 2] (<class 'list'>) != (1, 3) (<class 'tuple'>)"

        self.check_raises(
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
        self.check_raises(
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
        self.check_raises(
            class_a(1, 2), class_b(1, 2, 3),
            "Foo(x=1, y=2) (<class 'testfixtures.tests.test_compare.Foo'>) != "
            "Bar(x=1, y=2, z=3) "
            "(<class 'testfixtures.tests.test_compare.Bar'>)"
            )

    def test_dict_with_list(self):
        self.check_raises(
            {1: 'one', 2: 'two'}, [1, 2],
            "{1: 'one', 2: 'two'} != [1, 2]"
        )

    def test_explicit_expected(self):
        self.check_raises('x', expected='y',
                          message="'y' (expected) != 'x' (actual)")

    def test_explicit_actual(self):
        self.check_raises('x', actual='y',
                          message="'x' (expected) != 'y' (actual)")

    def test_explicit_both(self):
        self.check_raises(expected='x', actual='y',
                          message="'x' (expected) != 'y' (actual)")

    def test_implicit_and_labels(self):
        self.check_raises('x', 'y',
                          x_label='x_label', y_label='y_label',
                          message="'x' (x_label) != 'y' (y_label)")

    def test_explicit_and_labels(self):
        self.check_raises(explicit_x='x', explicit_y='y',
                          x_label='x_label', y_label='y_label',
                          message="'x' (x_label) != 'y' (y_label)")

    def test_invalid_two_args_expected(self):
        with ShouldRaise(TypeError(
                "Exactly two objects needed, you supplied: ['z', 'x', 'y']"
        )):
            compare('x', 'y', expected='z')

    def test_invalid_two_args_actual(self):
        with ShouldRaise(TypeError(
                "Exactly two objects needed, you supplied: ['x', 'y', 'z']"
        )):
            compare('x', 'y', actual='z')

    def test_invalid_zero_args(self):
        with ShouldRaise(TypeError(
                'Exactly two objects needed, you supplied:'
        )):
            compare()

    def test_invalid_one_args(self):
        with ShouldRaise(TypeError(
                "Exactly two objects needed, you supplied: ['x']"
        )):
            compare('x')

    def test_invalid_three_args(self):
        with ShouldRaise(TypeError(
                "Exactly two objects needed, you supplied: ['x', 'y', 'z']"
        )):
            compare('x', 'y', 'z')

    def test_invalid_because_of_typo(self):
        with ShouldRaise(TypeError(
                "Exactly two objects needed, you supplied: ['x'] {'expceted': 'z'}"
        )):
            compare('x', expceted='z')

    def test_dont_raise(self):
        self.assertEqual(compare('x', 'y', raises=False), "'x' != 'y'")

    class OrmObj(object):
        def __init__(self, a):
            self.a = a
        def __eq__(self, other):
            return True
        def __repr__(self):
            return 'OrmObj: '+str(self.a)

    def test_django_orm_is_horrible(self):

        self.assertTrue(self.OrmObj(1) == self.OrmObj(2))

        def query_set():
            yield self.OrmObj(1)
            yield self.OrmObj(2)

        self.check_raises(
            message=(
                "sequence not as expected:\n"
                "\n"
                "same:\n"
                "(OrmObj: 1,)\n"
                "\n"
                "expected:\n"
                "(OrmObj: 3,)\n"
                "\n"
                "actual:\n"
                "(OrmObj: 2,)\n"
                '\n'
                'While comparing [1]: OrmObj not as expected:\n'
                '\n'
                'attributes differ:\n'
                "'a': 3 (expected) != 2 (actual)"
            ),
            expected=[self.OrmObj(1), self.OrmObj(3)],
            actual=query_set(),
            ignore_eq=True
        )

    def test_django_orm_is_horrible_part_2(self):

        t_compare = partial(compare, ignore_eq=True)

        t_compare(self.OrmObj(1), self.OrmObj(1))
        t_compare(self.OrmObj('some longish string'),
                  self.OrmObj('some longish string'))
        t_compare(self.OrmObj(date(2016, 1, 1)),
                  self.OrmObj(date(2016, 1, 1)))

    def test_django_orm_is_horrible_part_3(self):
        compare(
            expected=self.OrmObj(1),
            actual=self.OrmObj(1),
            ignore_eq=True
        )

    def test_django_orm_is_horrible_part_4(self):
        self.check_raises(
            message='[1] (expected) != 2 (actual)',
            expected=[1],
            actual=2,
            ignore_eq=True
        )

    def test_mock_call_same(self):
        m = Mock()
        m.foo(1, 2, x=3)
        compare(m.mock_calls, m.mock_calls)

    def test_mock_call_same_strict(self):
        m = Mock()
        m.foo(1, 2, x=3)
        compare(m.mock_calls, m.mock_calls, strict=True)

    def test_calls_different(self):
        m1 = Mock()
        m2 = Mock()
        m1.foo(1, 2, x=3, y=4)
        m2.bar(1, 3, x=7, y=4)

        self.check_raises(
            m1.mock_calls,
            m2.mock_calls,
            "sequence not as expected:\n"
            "\n"
            "same:\n"
            "[]\n"
            "\n"
            "first:\n"
            "[call.foo(1, 2, x=3, y=4)]\n"
            "\n"
            "second:\n"
            "[call.bar(1, 3, x=7, y=4)]"
            "\n\n"
            'While comparing [0]: \n'
            "'call.foo(1, 2, x=3, y=4)'\n"
            '!=\n'
            "'call.bar(1, 3, x=7, y=4)'"
        )

    def test_call_args_different(self):
        m = Mock()
        m.foo(1)

        self.check_raises(
            m.foo.call_args,
            call(2),
            "'call(1)' != 'call(2)'"
        )

    def test_compare_arbitrary_nested_same(self):
        compare(SampleClassA([SampleClassB()]),
                SampleClassA([SampleClassB()]))

    def test_compare_different_vars(self):
        obj1 = SampleClassB(1)
        obj1.same = 42
        obj1.foo = '1'
        obj2 = SampleClassB(2)
        obj2.same = 42
        obj2.bar = '2'
        self.check_raises(
            obj1, obj2,
            "SampleClassB not as expected:\n"
            "\n"
            "attributes same:\n"
            "['same']\n"
            "\n"
            'attributes in first but not second:\n'
            "'foo': '1'\n"
            "\n"
            'attributes in second but not first:\n'
            "'bar': '2'\n"
            '\n'
            'attributes differ:\n'
            "'args': (1,) != (2,)\n"
            '\n'
            "While comparing .args: sequence not as expected:\n"
            '\n'
            'same:\n'
            '()\n'
            '\n'
            'first:\n'
            '(1,)\n'
            '\n'
            'second:\n'
            '(2,)'
        )

    def test_compare_arbitrary_nested_diff(self):
        class OurClass:
            def __init__(self, *args):
                self.args = args
            def __repr__(self):
                return '<OurClass obj>'
        self.check_raises(
            OurClass(OurClass(1)),
            OurClass(OurClass(2)),
            "OurClass not as expected:\n"
            "\n"
            'attributes differ:\n'
            "'args': (<OurClass obj>,) != (<OurClass obj>,)\n"
            '\n'
            'While comparing .args: sequence not as expected:\n'
            '\n'
            'same:\n'
            '()\n'
            '\n'
            'first:\n'
            '(<OurClass obj>,)\n'
            '\n'
            'second:\n'
            '(<OurClass obj>,)\n'
            '\n'
            'While comparing .args[0]: OurClass not as expected:\n'
            '\n'
            'attributes differ:\n'
            "'args': (1,) != (2,)\n"
            '\n'
            'While comparing .args[0].args: sequence not as expected:\n'
            '\n'
            'same:\n'
            '()\n'
            '\n'
            'first:\n'
            '(1,)\n'
            '\n'
            'second:\n'
            '(2,)'
        )

    def test_compare_slotted_same(self):
        compare(Slotted(1, 2), Slotted(1, 2))

    def test_compare_slotted_diff(self):
        self.check_raises(
            Slotted(1, 2),
            Slotted(1, 3),
            "Slotted not as expected:\n"
            "\n"
            "attributes same:\n"
            "['x']\n"
            "\n"
            'attributes differ:\n'
            "'y': 2 != 3"
        )

    def test_empty_sets(self):
        compare(set(), set())

    def test_empty_sets_strict(self):
        compare(set(), set(), strict=True)

    def test_datetime_not_equal(self):
        self.check_raises(
            datetime(2001, 1, 1),
            datetime(2001, 1, 2),
            "datetime.datetime(2001, 1, 1, 0, 0) != "
            "datetime.datetime(2001, 1, 2, 0, 0)"
        )

    def test_inherited_slots(self):

        class Parent(object):
            __slots__ = ('a',)

        class Child(Parent):
            __slots__ = ('b',)

            def __init__(self, a, b):
                self.a, self.b = a, b

        self.check_raises(
            Child(1, 'x'),
            Child(2, 'x'),
            'Child not as expected:\n'
            '\n'
            'attributes same:\n'
            "['b']\n"
            '\n'
            'attributes differ:\n'
            "'a': 1 != 2"
        )

    def test_empty_child_slots(self):

        class Parent(object):
            __slots__ = ('a',)

            def __init__(self, a):
                self.a = a

        class Child(Parent):
            __slots__ = ()

        compare(Child(1), Child(1))

    def test_slots_and_attrs(self):

        class Parent(object):
            __slots__ = ('a',)

        class Child(Parent):
            def __init__(self, a, b):
                self.a = a
                self.b = b

        self.check_raises(Child(1, 2), Child(1, 3), message=(
            'Child not as expected:\n'
            '\n'
            'attributes same:\n'
            "['a']\n"
            '\n'
            'attributes differ:\n'
            "'b': 2 != 3"
        ))

    def test_partial_callable_different(self):

        def foo(x): pass
        def bar(y): pass

        self.check_raises(
            partial(foo),
            partial(bar),
            (
                'partial not as expected:\n'
                '\n'
                'attributes same:\n'
                "['args', 'keywords']\n"
                '\n'
                'attributes differ:\n'
                "'func': {foo} != {bar}\n"
                '\n'
                'While comparing .func: {foo} != {bar}'
            ).format(foo=hexsub(repr(foo)), bar=hexsub(repr(bar))))

    def test_partial_args_different(self):

        def foo(x): pass

        self.check_raises(
            partial(foo, 1),
            partial(foo, 2),
            'partial not as expected:\n'
            '\n'
            'attributes same:\n'
            "['func', 'keywords']\n"
            '\n'
            'attributes differ:\n'
            "'args': (1,) != (2,)\n"
            '\n'
            'While comparing .args: sequence not as expected:\n'
            '\n'
            'same:\n'
            '()\n'
            '\n'
            'first:\n'
            '(1,)\n'
            '\n'
            'second:\n'
            '(2,)'
        )

    def test_partial_kw_different(self):

        def foo(x): pass

        self.check_raises(
            partial(foo, x=1, y=3),
            partial(foo, x=2, z=4),
            'partial not as expected:\n'
            '\n'
            'attributes same:\n'
            "['args', 'func']\n"
            '\n'
            'attributes differ:\n'
            "'keywords': {'x': 1, 'y': 3} != {'x': 2, 'z': 4}\n"
            '\n'
            'While comparing .keywords: dict not as expected:\n'
            '\n'
            'in first but not second:\n'
            "'y': 3\n"
            '\n'
            'in second but not first:\n'
            "'z': 4\n"
            '\n'
            'values differ:\n'
            "'x': 1 != 2"
        )

    def test_partial_equal(self):

        def foo(x): pass

        compare(partial(foo, 1, x=2), partial(foo, 1, x=2))

    def test_repr_and_attributes_equal(self):

        class Wut(object):
            def __repr__(self):
                return 'Wut'
            def __eq__(self, other):
                return False

        self.check_raises(
            Wut(),
            Wut(),
            "Both x and y appear as 'Wut', but are not equal!"
        )

        self.check_raises(
            expected=Wut(),
            actual=Wut(),
            message="Both expected and actual appear as 'Wut', but are not equal!"
        )

    def test_string_with_slotted(self):

        class Slotted(object):
            __slots__ = ['foo']
            def __init__(self, foo):
                self.foo = foo
            def __repr__(self):
                return repr(self.foo)

        self.check_raises(
            'foo',
            Slotted('foo'),
            "'foo' (%s) != 'foo' (%s)" % (repr(str), repr(Slotted))
        )

    def test_not_recursive(self):
        self.check_raises(
            {1: 'foo', 2: 'foo'},
            {1: 'bar', 2: 'bar'},
            "dict not as expected:\n"
            "\n"
            "values differ:\n"
            "1: 'foo' != 'bar'\n"
            "2: 'foo' != 'bar'\n"
            "\n"
            "While comparing [1]: 'foo' != 'bar'"
            "\n\n"
            "While comparing [2]: 'foo' != 'bar'"
            )


class TestIgnore(CompareHelper):

    class Parent(object):
        def __init__(self, id, other):
            self.id = id
            self.other = other
        def __repr__(self):
            return '<{}:{}>'.format(type(self).__name__, self.id)

    class Child(Parent): pass

    def test_ignore_attributes(self):
        compare(self.Parent(1, 3), self.Parent(2, 3), ignore_attributes={'id'})

    def test_ignore_attributes_different_types(self):
        self.check_raises(
            self.Parent(1, 3),
            self.Child(2, 3),
            '<Parent:1> != <Child:2>',
            ignore_attributes={'id'}
        )

    def test_ignore_attributes_per_type(self):
        ignore = {self.Parent: {'id'}}
        compare(self.Parent(1, 3), self.Parent(2, 3), ignore_attributes=ignore)
        self.check_raises(
            self.Child(1, 3),
            self.Child(2, 3),
            'Child not as expected:\n'
            '\n'
            'attributes same:\n'
            "['other']\n"
            '\n'
            'attributes differ:\n'
            "'id': 1 != 2",
            ignore_attributes=ignore
        )


class TestCompareObject(object):

    class Thing(object):
        def __init__(self, **kw):
            for k, v in kw.items():
                setattr(self, k, v)

    def test_ignore(self):
        def compare_thing(x, y, context):
            return compare_object(x, y, context, ignore_attributes=['y'])
        compare(self.Thing(x=1, y=2), self.Thing(x=1, y=3),
                comparers={self.Thing: compare_thing})

    def test_ignore_dict_context_list_param(self):
        def compare_thing(x, y, context):
            return compare_object(x, y, context, ignore_attributes=['y'])
        compare(self.Thing(x=1, y=2, z=3), self.Thing(x=1, y=4, z=5),
                comparers={self.Thing: compare_thing},
                ignore_attributes={self.Thing: ['z']})

    def test_ignore_list_context_list_param(self):
        def compare_thing(x, y, context):
            return compare_object(x, y, context, ignore_attributes=['y'])
        compare(self.Thing(x=1, y=2, z=3), self.Thing(x=1, y=4, z=5),
                comparers={self.Thing: compare_thing},
                ignore_attributes=['z'])


class BaseClass(ABC):
    pass


class MyDerivedClass(BaseClass):

    def __init__(self, thing):
        self.thing = thing


class ConcreteBaseClass(object): pass


class ConcreteDerivedClass(ConcreteBaseClass):

    def __init__(self, thing):
        self.thing = thing


class TestBaseClasses(CompareHelper):

    def test_abc_equal(self):
        thing1 = MyDerivedClass(1)
        thing2 = MyDerivedClass(1)

        compare(thing1, thing2)

    def test_abc_unequal(self):
        thing1 = MyDerivedClass(1)
        thing2 = MyDerivedClass(2)

        self.check_raises(thing1, thing2, message=(
            "MyDerivedClass not as expected:\n\n"
            "attributes differ:\n"
            "'thing': 1 != 2"
        ))

    def test_concrete_equal(self):
        thing1 = ConcreteDerivedClass(1)
        thing2 = ConcreteDerivedClass(1)

        compare(thing1, thing2)

    def test_concrete_unequal(self):
        thing1 = ConcreteDerivedClass(1)
        thing2 = ConcreteDerivedClass(2)

        self.check_raises(thing1, thing2, message=(
            "ConcreteDerivedClass not as expected:\n\n"
            "attributes differ:\n"
            "'thing': 1 != 2"
        ))
