from unittest import TestCase
import sys

from testfixtures import Comparison as C, TempDirectory, compare, diff
from testfixtures.compat import PY2, PY3, exception_module
from testfixtures.shouldraise import ShouldAssert
from testfixtures.tests.sample1 import SampleClassA, a_function
import pytest


class AClass:

    def __init__(self, x, y=None):
        self.x = x
        if y:
            self.y = y

    def __repr__(self):
        return '<'+self.__class__.__name__+'>'


class BClass(AClass):
    pass


class WeirdException(Exception):
    def __init__(self, x, y):
        self.x = x
        self.y = y


class X(object):
    __slots__ = ['x']


class FussyDefineComparison(object):

    def __init__(self, attr):
        self.attr = attr

    def __eq__(self, other):
        if not isinstance(other, self.__class__):  # pragma: no cover
            raise TypeError()
        return False  # pragma: no cover

    def __ne__(self, other):
        return not self == other  # pragma: no cover


def compare_repr(obj, expected):
    actual = diff(expected, repr(obj))
    if actual:  # pragma: no cover
        raise AssertionError(actual)


class TestC(TestCase):

    def test_example(self):
        # In this pattern, we want to check a sequence is
        # of the correct type and order.
        r = a_function()
        self.assertEqual(r, (
            C('testfixtures.tests.sample1.SampleClassA'),
            C('testfixtures.tests.sample1.SampleClassB'),
            C('testfixtures.tests.sample1.SampleClassA'),
            ))
        # We also want to check specific parts of some
        # of the returned objects' attributes
        self.assertEqual(r[0].args[0], 1)
        self.assertEqual(r[1].args[0], 2)
        self.assertEqual(r[2].args[0], 3)

    def test_example_with_object(self):
        # Here we see compare an object with a Comparison
        # based on an object of the same type and with the
        # same attributes:
        self.assertEqual(
            C(AClass(1, 2)),
            AClass(1, 2),
            )
        # ...even though the original class doesn't support
        # meaningful comparison:
        self.assertNotEqual(
            AClass(1, 2),
            AClass(1, 2),
            )

    def test_example_with_vars(self):
        # Here we use a Comparison to make sure both the
        # type and attributes of an object are correct.
        self.assertEqual(
            C('testfixtures.tests.test_comparison.AClass',
              x=1, y=2),
            AClass(1, 2),
            )

    def test_example_with_odd_vars(self):
        # If the variable names class with parameters to the
        # Comparison constructor, they can be specified in a
        # dict:
        self.assertEqual(
            C('testfixtures.tests.test_comparison.AClass',
              {'x': 1, 'y': 2}),
            AClass(1, 2),
            )

    def test_example_not_strict(self):
        # Here, we only care about the 'x' attribute of
        # the AClass object, so we turn strict mode off.
        # With strict mode off, only attributes specified
        # in the Comparison object will be checked, and
        # any others will be ignored.
        self.assertEqual(
            C('testfixtures.tests.test_comparison.AClass',
              x=1,
              strict=False),
            AClass(1, 2),
            )

    def test_example_dont_use_c_wrappers_on_both_sides(self):
        # NB: don't use C wrappers on both sides!
        e = ValueError('some message')
        x, y = C(e), C(e)
        assert x != y
        compare_repr(x, "<C(failed):{mod}.ValueError>wrong type</C>".format(
                            mod=exception_module))
        compare_repr(
            y,
            "<C:{mod}.ValueError>args: ('some message',)</C>".format(
                mod=exception_module)
        )

    def test_repr_module(self):
        compare_repr(C('datetime'), '<C:datetime>')

    def test_repr_class(self):
        compare_repr(C('testfixtures.tests.sample1.SampleClassA'),
                     '<C:testfixtures.tests.sample1.SampleClassA>')

    def test_repr_function(self):
        compare_repr(C('testfixtures.tests.sample1.z'),
                     '<C:testfixtures.tests.sample1.z>')

    def test_repr_instance(self):
        compare_repr(C(SampleClassA('something')),
                     "<C:testfixtures.tests.sample1.SampleClassA>"
                     "args: ('something',)"
                     "</C>"
                     )

    def test_repr_exception(self):
        compare_repr(C(ValueError('something')),
                     ("<C:{0}.ValueError>args: ('something',)</C>"
                      ).format(exception_module))

    def test_repr_exception_not_args(self):
        if sys.version_info >= (3, 2, 4):
            # in PY3, even args that aren't set still appear to be there
            args = "args: (1, 2)\n"
        else:
            args = "args: ()\n"

        compare_repr(
            C(WeirdException(1, 2)),
            "\n<C:testfixtures.tests.test_comparison.WeirdException>\n"
            + args +
            "x: 1\n"
            "y: 2\n"
            "</C>"
        )

    def test_repr_class_and_vars(self):
        compare_repr(
            C(SampleClassA, {'args': (1,)}),
            "<C:testfixtures.tests.sample1.SampleClassA>args: (1,)</C>"
        )

    def test_repr_nested(self):
        compare_repr(
            C(SampleClassA, y=C(AClass), z=C(BClass(1, 2))),
            "\n"
            "<C:testfixtures.tests.sample1.SampleClassA>\n"
            "y: <C:testfixtures.tests.test_comparison.AClass>\n"
            "z: \n"
            "  <C:testfixtures.tests.test_comparison.BClass>\n"
            "  x: 1\n"
            "  y: 2\n"
            "  </C>\n"
            "</C>"
            )

    def test_repr_failed_wrong_class(self):
        c = C('testfixtures.tests.test_comparison.AClass', x=1, y=2)
        assert c != BClass(1, 2)
        compare_repr(c,
                     "<C(failed):testfixtures.tests.test_comparison.AClass>"
                     "wrong type</C>"
                     )

    def test_repr_failed_all_reasons_in_one(self):
        c = C('testfixtures.tests.test_comparison.AClass',
              y=5, z='missing')
        assert c != AClass(1, 2)
        compare_repr(c,
                     "\n"
                     "<C(failed):testfixtures.tests.test_comparison.AClass>\n"
                     "attributes in Comparison but not actual:\n"
                     "'z': 'missing'\n\n"
                     "attributes in actual but not Comparison:\n"
                     "'x': 1\n\n"
                     "attributes differ:\n"
                     "'y': 5 (Comparison) != 2 (actual)\n"
                     "</C>",
                     )

    def test_repr_failed_not_in_other(self):
        c = C('testfixtures.tests.test_comparison.AClass',
              x=1, y=2, z=(3, ))
        assert c != AClass(1, 2)
        compare_repr(c ,
                     "\n"
                     "<C(failed):testfixtures.tests.test_comparison.AClass>\n"
                     "attributes same:\n"
                     "['x', 'y']\n\n"
                     "attributes in Comparison but not actual:\n"
                     "'z': (3,)\n"
                     "</C>",
                     )

    def test_repr_failed_not_in_self_strict(self):
        c = C('testfixtures.tests.test_comparison.AClass', y=2)
        assert c != AClass((1, ), 2)
        compare_repr(c,
                     "\n"
                     "<C(failed):testfixtures.tests.test_comparison.AClass>\n"
                     "attributes same:\n"
                     "['y']\n\n"
                     "attributes in actual but not Comparison:\n"
                     "'x': (1,)\n"
                     "</C>",
                     )

    def test_repr_failed_not_in_self_not_strict(self):
        c = C('testfixtures.tests.test_comparison.AClass',
              x=1, y=2, z=(3, ))
        assert c != AClass(1, 2)
        compare_repr(c,
                     "\n"
                     "<C(failed):testfixtures.tests.test_comparison.AClass>\n"
                     "attributes same:\n"
                     "['x', 'y']\n\n"
                     "attributes in Comparison but not actual:\n"
                     "'z': (3,)\n"
                     "</C>",
                     )

    def test_repr_failed_one_attribute_not_equal(self):
        c = C('testfixtures.tests.test_comparison.AClass', x=1, y=(2, ))
        assert c != AClass(1, (3, ))
        compare_repr(c,
                     "\n"
                     "<C(failed):testfixtures.tests.test_comparison.AClass>\n"
                     "attributes same:\n"
                     "['x']\n\n"
                     "attributes differ:\n"
                     "'y': (2,) (Comparison) != (3,) (actual)\n"
                     "</C>",
                     )

    def test_repr_failed_nested(self):
        left_side = [C(AClass, x=1, y=2),
                     C(BClass, x=C(AClass, x=1, y=2), y=C(AClass))]
        right_side = [AClass(1, 3), AClass(1, 3)]

        # do the comparison
        left_side == right_side

        compare_repr(
            left_side,
            "[\n"
            "<C(failed):testfixtures.tests.test_comparison.AClass>\n"
            "attributes same:\n"
            "['x']\n\n"
            "attributes differ:\n"
            "'y': 2 (Comparison) != 3 (actual)\n"
            "</C>, \n"
            "<C:testfixtures.tests.test_comparison.BClass>\n"
            "x: \n"
            "  <C:testfixtures.tests.test_comparison.AClass>\n"
            "  x: 1\n"
            "  y: 2\n"
            "  </C>\n"
            "y: <C:testfixtures.tests.test_comparison.AClass>\n"
            "</C>]"
        )

        compare_repr(right_side, "[<AClass>, <AClass>]")

    def test_repr_failed_nested_failed(self):
        left_side = [C(AClass, x=1, y=2),
                     C(BClass,
                       x=C(AClass, x=1, strict=False),
                       y=C(AClass, z=2))]
        right_side = [AClass(1, 2),
                      BClass(AClass(1, 2), AClass(1, 2))]

        # do the comparison
        left_side == right_side

        compare_repr(
            left_side,
            "[\n"
            "<C:testfixtures.tests.test_comparison.AClass>\n"
            "x: 1\n"
            "y: 2\n"
            "</C>, \n"
            "<C(failed):testfixtures.tests.test_comparison.BClass>\n"
            "attributes same:\n"
            "['x']\n\n"
            "attributes differ:\n"
            "'y': \n"
            "<C(failed):testfixtures.tests.test_comparison.AClass>\n"
            "attributes in Comparison but not actual:\n"
            "'z': 2\n\n"
            "attributes in actual but not Comparison:\n"
            "'x': 1\n"
            "'y': 2\n"
            "</C> (Comparison) != <AClass> (actual)\n"
            "</C>]",
        )

        compare_repr(right_side, '[<AClass>, <BClass>]')

    def test_repr_failed_passed_failed(self):
        c = C('testfixtures.tests.test_comparison.AClass', x=1, y=2)
        assert c != AClass(1, 3)
        compare_repr(c,
                     "\n"
                     "<C(failed):testfixtures.tests.test_comparison.AClass>\n"
                     "attributes same:\n"
                     "['x']\n\n"
                     "attributes differ:\n"
                     "'y': 2 (Comparison) != 3 (actual)\n"
                     "</C>",
                     )

        assert c == AClass(1, 2)

        assert c != AClass(3, 2)
        compare_repr(c,
                     "\n"
                     "<C(failed):testfixtures.tests.test_comparison.AClass>\n"
                     "attributes same:\n"
                     "['y']\n\n"
                     "attributes differ:\n"
                     "'x': 1 (Comparison) != 3 (actual)\n"
                     "</C>",
                     )

    def test_first(self):
        self.assertEqual(
            C('testfixtures.tests.sample1.SampleClassA'),
            SampleClassA()
            )

    def test_second(self):
        self.assertEqual(
            SampleClassA(),
            C('testfixtures.tests.sample1.SampleClassA'),
            )

    def test_not_same_first(self):
        self.assertNotEqual(
            C('datetime'),
            SampleClassA()
            )

    def test_not_same_second(self):
        self.assertNotEqual(
            SampleClassA(),
            C('datetime')
            )

    def test_object_supplied(self):
        self.assertEqual(
            SampleClassA(1),
            C(SampleClassA(1))
            )

    def test_class_and_vars(self):
        self.assertEqual(
            SampleClassA(1),
            C(SampleClassA, {'args': (1,)})
            )

    def test_class_and_kw(self):
        self.assertEqual(
            SampleClassA(1),
            C(SampleClassA, args=(1,))
            )

    def test_class_and_vars_and_kw(self):
        self.assertEqual(
            AClass(1, 2),
            C(AClass, {'x': 1}, y=2)
            )

    def test_object_and_vars(self):
        # vars passed are used instead of the object's
        self.assertEqual(
            SampleClassA(1),
            C(SampleClassA(), {'args': (1,)})
            )

    def test_object_and_kw(self):
        # kws passed are used instead of the object's
        self.assertEqual(
            SampleClassA(1),
            C(SampleClassA(), args=(1,))
            )

    def test_object_not_strict(self):
        # only attributes on comparison object
        # are used
        self.assertEqual(
            C(AClass(1), strict=False),
            AClass(1, 2),
            )

    def test_exception(self):
        self.assertEqual(
            ValueError('foo'),
            C(ValueError('foo'))
            )

    def test_exception_class_and_args(self):
        self.assertEqual(
            ValueError('foo'),
            C(ValueError, args=('foo', ))
            )

    def test_exception_instance_and_args(self):
        self.assertEqual(
            ValueError('foo'),
            C(ValueError('bar'), args=('foo', ))
            )

    def test_exception_not_same(self):
        self.assertNotEqual(
            ValueError('foo'),
            C(ValueError('bar'))
            )

    def test_exception_no_args_different(self):
        self.assertNotEqual(
            WeirdException(1, 2),
            C(WeirdException(1, 3))
            )

    def test_exception_no_args_same(self):
        self.assertEqual(
            C(WeirdException(1, 2)),
            WeirdException(1, 2)
            )

    def test_repr_file_different(self):
        with TempDirectory() as d:
            path = d.write('file', b'stuff')
            f = open(path)
            f.close()
        if PY3:
            c = C('io.TextIOWrapper', name=path, mode='r', closed=False,
                  strict=False)
            assert f != c
            compare_repr(c,
                         "\n"
                         "<C(failed):_io.TextIOWrapper>\n"
                         "attributes same:\n"
                         "['mode', 'name']\n\n"
                         "attributes differ:\n"
                         "'closed': False (Comparison) != True (actual)\n"
                         "</C>",
                         )
        else:
            c = C(file, name=path, mode='r', closed=False, strict=False)
            assert f != c
            compare_repr(c,
                         "\n"
                         "<C(failed):__builtin__.file>\n"
                         "attributes same:\n"
                         "['mode', 'name']\n\n"
                         "attributes differ:\n"
                         "'closed': False (Comparison) != True (actual)\n"
                         "</C>",
                         )

    def test_file_same(self):
        with TempDirectory() as d:
            path = d.write('file', b'stuff')
            f = open(path)
            f.close()
        if PY3:
            self.assertEqual(
                f,
                C('io.TextIOWrapper', name=path, mode='r', closed=True,
                  strict=False)
                )
        else:
            self.assertEqual(
                f,
                C(file, name=path, mode='r', closed=True, strict=False)
                )

    def test_no___dict___strict(self):
        c = C(X, x=1)
        assert c != X()
        compare_repr(c, "\n"
                        "<C(failed):testfixtures.tests.test_comparison.X>\n"
                        "attributes in Comparison but not actual:\n"
                        "'x': 1\n"
                        "</C>")

    def test_no___dict___not_strict_same(self):
        x = X()
        x.x = 1
        self.assertEqual(C(X, x=1, strict=False), x)

    def test_no___dict___not_strict_missing_attr(self):
        c = C(X, x=1, strict=False)
        assert c != X()
        compare_repr(c,
                     "\n"
                     "<C(failed):testfixtures.tests.test_comparison.X>\n"
                     "attributes in Comparison but not actual:\n"
                     "'x': 1\n"
                     "</C>",
                     )

    def test_no___dict___not_strict_different(self):
        x = X()
        x.x = 2
        c = C(X, x=1, y=2, strict=False)
        assert c != x
        compare_repr(c,
                     "\n"
                     "<C(failed):testfixtures.tests.test_comparison.X>\n"
                     "attributes in Comparison but not actual:\n"
                     "'y': 2\n\n"
                     "attributes differ:\n"
                     "'x': 1 (Comparison) != 2 (actual)\n"
                     "</C>",
                     )

    def test_compared_object_defines_eq(self):
        # If an object defines eq, such as Django instances,
        # things become tricky

        class Annoying:
            def __init__(self):
                self.eq_called = 0

            def __eq__(self, other):
                self.eq_called += 1
                if isinstance(other, Annoying):
                    return True
                return False

        self.assertEqual(Annoying(), Annoying())

        # Suddenly, order matters.

        # This order is wrong, as it uses the class's __eq__:
        self.assertFalse(Annoying() == C(Annoying))
        if PY2:
            # although this, which is subtly different, does not:
            self.assertFalse(Annoying() != C(Annoying))
        else:
            # but on PY3 __eq__ is used as a fallback:
            self.assertTrue(Annoying() != C(Annoying))

        # This is the right ordering:
        self.assertTrue(C(Annoying) == Annoying())
        self.assertFalse(C(Annoying) != Annoying())

        # When the ordering is right, you still get the useful
        # comparison representation afterwards
        c = C(Annoying, eq_called=1)
        c == Annoying()
        compare_repr(
            c,
            '\n<C(failed):testfixtures.tests.test_comparison.Annoying>\n'
            'attributes differ:\n'
            "'eq_called': 1 (Comparison) != 0 (actual)\n"
            '</C>'
        )

    def test_importerror(self):
        assert C(ImportError('x')) == ImportError('x')

    def test_class_defines_comparison_strictly(self):
        self.assertEqual(
            C('testfixtures.tests.test_comparison.FussyDefineComparison',
              attr=1),
            FussyDefineComparison(1)
            )

    def test_cant_resolve(self):
        try:
            C('testfixtures.bonkers')
        except Exception as e:
            self.failUnless(isinstance(e, AttributeError))
            self.assertEqual(
                e.args,
                ("'testfixtures.bonkers' could not be resolved", )
                )
        else:
            self.fail('No exception raised!')

    def test_no_name(self):
        class NoName(object):
            pass
        NoName.__name__ = ''
        NoName.__module__ = ''
        c = C(NoName)
        if PY3:
            expected = "<C:<class '.TestC.test_no_name.<locals>.NoName'>>"
        else:
            expected = "<C:<class '.'>>"
        self.assertEqual(repr(c), expected)
