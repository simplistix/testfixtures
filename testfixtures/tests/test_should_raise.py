from textwrap import dedent

import pytest

from testfixtures import Comparison as C, ShouldRaise, should_raise
from unittest import TestCase

from ..shouldraise import ShouldAssert, NoException


class TestShouldAssert:

    def test_no_exception(self) -> None:
        try:
            with ShouldAssert('foo'):
                pass
        except AssertionError as e:
            assert str(e) == "Expected AssertionError('foo'), None raised!"

    def test_wrong_exception(self) -> None:
        try:
            with ShouldAssert('foo'):
                raise KeyError()
        except KeyError:
            pass

    def test_wrong_text(self) -> None:
        try:
            with ShouldAssert('foo'):
                assert False, 'bar'
        except AssertionError as e:
            assert str(e) == dedent("""\
                --- expected
                +++ actual
                @@ -1 +1,2 @@
                -foo
                +bar
                +assert False""")

    def test_show_whitespace(self) -> None:
        try:
            with ShouldAssert('foo ', show_whitespace=True):
                assert False, ' foo'
        except AssertionError as e:
            assert str(e) == dedent(
                """\
                --- expected
                +++ actual
                @@ -1 +1,2 @@
                -'foo '
                +' foo\\n'
                +'assert False'"""
            )



class TestShouldRaise(TestCase):

    def test_no_params(self) -> None:
        def to_test() -> None:
            raise ValueError('wrong value supplied')
        should_raise(ValueError('wrong value supplied'))(to_test)()

    def test_no_exception(self) -> None:
        def to_test() -> None:
            pass
        with ShouldAssert('ValueError() (expected) != None (raised)'):
            should_raise(ValueError())(to_test)()

    def test_wrong_exception(self) -> None:
        def to_test() -> None:
            raise ValueError('bar')
        expected = "ValueError('foo') (expected) != ValueError('bar') (raised)"
        with ShouldAssert(expected):
            should_raise(ValueError('foo'))(to_test)()

    def test_only_exception_class(self) -> None:
        def to_test() -> None:
            raise ValueError('bar')
        should_raise(ValueError)(to_test)()

    def test_wrong_exception_class(self) -> None:
        expected_exception = ValueError('bar')
        def to_test() -> None:
            raise expected_exception
        try:
            should_raise(KeyError)(to_test)()
        except ValueError as actual_exception:
            assert actual_exception is expected_exception
        else:  # pragma: no cover
            self.fail(('Wrong exception raised'))

    def test_wrong_exception_type(self) -> None:
        expected_exception = ValueError('bar')
        def to_test() -> None:
            raise expected_exception
        try:
            should_raise(KeyError('foo'))(to_test)()
        except ValueError as actual_exception:
            assert actual_exception is expected_exception
        else:  # pragma: no cover
            self.fail(('Wrong exception raised'))

    def test_no_supplied_or_raised(self) -> None:
        # effectively we're saying "something should be raised!"
        # but we want to inspect s.raised rather than making
        # an up-front assertion
        def to_test() -> None:
            pass
        with ShouldAssert("No exception raised!"):
            should_raise()(to_test)()

    def test_args(self) -> None:
        def to_test(*args: object) -> None:
            raise ValueError('%s' % repr(args))
        should_raise(ValueError('(1,)'))(to_test)(1)

    def test_kw_to_args(self) -> None:
        def to_test(x: object) -> None:
            raise ValueError('%s' % x)
        should_raise(ValueError('1'))(to_test)(x=1)

    def test_kw(self) -> None:
        def to_test(**kw: object) -> None:
            raise ValueError('%r' % kw)
        should_raise(ValueError("{'x': 1}"))(to_test)(x=1)

    def test_both(self) -> None:
        def to_test(*args: object, **kw: object) -> None:
            raise ValueError('%r %r' % (args, kw))
        should_raise(ValueError("(1,) {'x': 2}"))(to_test)(1, x=2)

    def test_method_args(self) -> None:
        class X:
            def to_test(self, *args: object) -> None:
                self.args = args
                raise ValueError()
        x = X()
        should_raise(ValueError)(x.to_test)(1, 2, 3)
        self.assertEqual(x.args, (1, 2, 3))

    def test_method_kw(self) -> None:
        class X:
            def to_test(self, **kw: object) -> None:
                self.kw = kw
                raise ValueError()
        x = X()
        should_raise(ValueError)(x.to_test)(x=1, y=2)
        self.assertEqual(x.kw, {'x': 1, 'y': 2})

    def test_method_both(self) -> None:
        class X:
            def to_test(self, *args: object, **kw: object) -> None:
                self.args = args
                self.kw = kw
                raise ValueError()
        x = X()
        should_raise(ValueError)(x.to_test)(1, y=2)
        self.assertEqual(x.args, (1, ))
        self.assertEqual(x.kw, {'y': 2})

    def test_class_class(self) -> None:
        class Test:
            def __init__(self, x: object) -> None:
                # The TypeError is raised due to the mis-matched parameters
                # so the pass never gets executed
                pass  # pragma: no cover
        should_raise(TypeError)(Test)()  # type: ignore[call-arg]

    def test_raised(self) -> None:
        with ShouldRaise() as s:
            raise ValueError('wrong value supplied')
        self.assertEqual(s.raised, C(ValueError('wrong value supplied')))

    def test_catch_baseexception_1(self) -> None:
        with ShouldRaise(SystemExit):
            raise SystemExit()

    def test_catch_baseexception_2(self) -> None:
        with ShouldRaise(KeyboardInterrupt):
            raise KeyboardInterrupt()

    def test_with_exception_class_supplied(self) -> None:
        with ShouldRaise(ValueError):
            raise ValueError('foo bar')

    def test_with_exception_supplied(self) -> None:
        with ShouldRaise(ValueError('foo bar')):
            raise ValueError('foo bar')

    def test_with_exception_supplied_wrong_args(self) -> None:
        expected = "ValueError('foo') (expected) != ValueError('bar') (raised)"
        with ShouldAssert(expected):
            with ShouldRaise(ValueError('foo')):
                raise ValueError('bar')

    def test_neither_supplied(self) -> None:
        with ShouldRaise():
            raise ValueError('foo bar')

    def test_with_no_exception_when_expected(self) -> None:
        expected = "ValueError('foo') (expected) != None (raised)"
        with ShouldAssert(expected):
            with ShouldRaise(ValueError('foo')):
                pass

    def test_with_no_exception_when_expected_by_type(self) -> None:
        with ShouldAssert("<class 'ValueError'> (expected) != None (raised)"):
            with ShouldRaise(ValueError):
                pass

    def test_with_no_exception_when_neither_expected(self) -> None:
        with ShouldAssert("No exception raised!"):
            with ShouldRaise():
                pass

    def test_with_getting_raised_exception(self) -> None:
        e = ValueError('foo bar')
        with ShouldRaise() as s:
            raise e
        assert e is s.raised

    def test_import_errors_1(self) -> None:
        with ShouldRaise(ModuleNotFoundError("No module named 'textfixtures'")):
            import textfixtures.foo.bar  # type: ignore[import-not-found]

    def test_import_errors_2(self) -> None:
        with ShouldRaise(ImportError('X')):
            raise ImportError('X')

    def test_custom_exception(self) -> None:

        class FileTypeError(Exception):
            def __init__(self, value: object) -> None:
                self.value = value

        with ShouldRaise(FileTypeError('X')):
            raise FileTypeError('X')

    def test_decorator_usage(self) -> None:

        @should_raise(ValueError('bad'))
        def to_test() -> None:
            raise ValueError('bad')

        to_test()

    def test_unless_false_okay(self) -> None:
        with ShouldRaise(unless=False):
            raise AttributeError()

    def test_unless_false_bad(self) -> None:
        with ShouldAssert("No exception raised!"):
            with ShouldRaise(unless=False):
                pass

    def test_unless_true_okay(self) -> None:
        with ShouldRaise(unless=True) as s:
            pass
        # This documents the value of .raised in the rare care where it isn't
        # the exception raised within the context manager:
        assert isinstance(s.raised, NoException)

    def test_unless_true_not_okay(self) -> None:
        expected_exception = AttributeError('foo')
        try:
            with ShouldRaise(unless=True):
                raise expected_exception
        except AttributeError as actual_exception:
            assert actual_exception is expected_exception
        else:  # pragma: no cover
            self.fail('Wrong exception raised')

    def test_unless_decorator_usage(self) -> None:

        @should_raise(unless=True)
        def to_test() -> None:
            pass

        to_test()

    def test_identical_reprs(self) -> None:
        class AnnoyingException(Exception):
            def __init__(self, **kw: object) -> None:
                self.other = kw.get('other')

        with ShouldAssert(
            "AnnoyingException not as expected:\n\n"
            'attributes same:\n'
            "['args']\n\n"
            "attributes differ:\n"
            "'other': 'bar' (expected) != 'baz' (raised)\n\n"
            "While comparing .other: 'bar' (expected) != 'baz' (raised)"
        ):
            with ShouldRaise(AnnoyingException(other='bar')):
                raise AnnoyingException(other='baz')

    def test_identical_reprs_but_args_different(self) -> None:

        class MessageError(Exception):
           def __init__(self, message: object, type: object = None) -> None:
               self.message = message
               self.type = type
           def __repr__(self) -> str:
               return 'MessageError({!r}, {!r})'.format(self.message, self.type)

        with ShouldAssert(
            "MessageError not as expected:\n\n"
            'attributes same:\n'
            "['message', 'type']\n\n"
            "attributes differ:\n"
            "'args': ('foo',) (expected) != ('foo', None) (raised)\n\n"
            "While comparing .args: sequence not as expected:\n\n"
            "same:\n"
            "('foo',)\n\n"
            "expected:\n"
            "()\n\n"
            "raised:\n"
            "(None,)"
        ):
            with ShouldRaise(MessageError('foo')):
                raise MessageError('foo', None)

    def test_exception_group_okay(self) -> None:
        with ShouldRaise(ExceptionGroup('foo', [Exception('bar')])):
            raise ExceptionGroup('foo', [Exception('bar')])

    def test_exception_group_different(self) -> None:
        with ShouldAssert(
                "exception group not as expected:\n\n"
                "While comparing msg: 'fob' (expected) != 'foo' (raised)\n\n"
                "While comparing excs: sequence not as expected:\n\n"
                "same:\n"
                "[]\n\n"
                "expected:\n"
                "[Exception('baz')]\n\n"
                "raised:\n"
                "[Exception('bar')]\n\n"
                "While comparing excs[0]: "
                "Exception('baz') (expected) != Exception('bar') (raised)"
        ):
            with ShouldRaise(ExceptionGroup('fob', [Exception('baz')])):
                raise ExceptionGroup('foo', [Exception('bar')])

    def test_check_notes_on_raised_exception(self) -> None:
        exception = ValueError('foo')
        exception.add_note('bar')
        with ShouldRaise(ValueError) as s:
            raise exception
        assert s.raised.__notes__ == ['bar']
