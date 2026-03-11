import pytest

pytest.importorskip("twisted")

from twisted.logger import Logger, formatEvent
from twisted.python.failure import Failure
from twisted.trial.unittest import TestCase

from testfixtures import compare, ShouldRaise, StringComparison as S, ShouldAssert
from testfixtures import LogCapture as UnifiedLogCapture
from testfixtures.twisted import LogCapture, INFO, TwistedSource

log = Logger()


class TestLogCapture(TestCase):

    def test_simple(self):
        capture = LogCapture.make(self)
        log.info('er, {greeting}', greeting='hi')
        capture.check((INFO, 'er, hi'))

    def test_captured(self):
        capture = LogCapture.make(self)
        log.info('er, {greeting}', greeting='hi')
        assert len(capture.events) == 1
        compare(capture.events[0]['log_namespace'], expected='tests.test_twisted')

    def test_fields(self):
        capture = LogCapture.make(self, fields=('a', 'b'))
        log.info('{a}, {b}', a=1, b=2)
        log.info('{a}, {b}', a=3, b=4)
        capture.check(
            [1, 2],
            [3, 4],
        )

    def test_field(self):
        capture = LogCapture.make(self, fields=(formatEvent,))
        log.info('er, {greeting}', greeting='hi')
        capture.check('er, hi')

    def test_check_failure_test_minimal(self):
        capture = LogCapture.make(self)
        try:
            raise Exception('all gone wrong')
        except:
            log.failure('oh dear')
        capture.check_failure_text('all gone wrong')
        self.flushLoggedErrors()

    def test_check_failure_test_maximal(self):
        capture = LogCapture.make(self)
        try:
            raise TypeError('all gone wrong')
        except:
            log.failure('oh dear')
        log.info("don't look at me...")
        capture.check_failure_text(str(TypeError), index=0, attribute='type')
        self.flushLoggedErrors()
        self.flushLoggedErrors()

    def test_raise_logged_failure(self):
        capture = LogCapture.make(self)
        try:
            raise TypeError('all gone wrong')
        except:
            log.failure('oh dear')
        with ShouldRaise(Failure) as s:
            capture.raise_logged_failure()
        compare(s.raised.value, expected=TypeError('all gone wrong'))
        self.flushLoggedErrors()

    def test_raise_later_logged_failure(self):
        capture = LogCapture.make(self)
        try:
            raise ValueError('boom!')
        except:
            log.failure('oh dear')
        try:
            raise TypeError('all gone wrong')
        except:
            log.failure('what now?!')
        with ShouldRaise(Failure) as s:
            capture.raise_logged_failure(start_index=1)
        compare(s.raised.value, expected=TypeError('all gone wrong'))
        self.flushLoggedErrors()

    def test_order_doesnt_matter_ok(self):
        capture = LogCapture.make(self)
        log.info('Failed to send BAR')
        log.info('Sent FOO, length 1234')
        log.info('Sent 1 Messages')
        capture.check(
            (INFO, S(r'Sent FOO, length \d+')),
            (INFO, 'Failed to send BAR'),
            (INFO, 'Sent 1 Messages'),
            order_matters=False
        )

    def test_order_doesnt_matter_failure(self):
        capture = LogCapture.make(self)
        log.info('Failed to send BAR')
        log.info('Sent FOO, length 1234')
        log.info('Sent 1 Messages')
        with ShouldAssert(
            "same:\n"
            "[(<LogLevel=info>, 'Failed to send BAR'), (<LogLevel=info>, 'Sent 1 Messages')]\n"
            "\n"
            "in expected but not actual:\n"
            "[(<LogLevel=info>, <S:Sent FOO, length abc>)]\n"
            "\n"
            "in actual but not expected:\n"
            "[(<LogLevel=info>, 'Sent FOO, length 1234')]"
        ):
            capture.check(
                (INFO, S('Sent FOO, length abc')),
                (INFO, 'Failed to send BAR'),
                (INFO, 'Sent 1 Messages'),
                order_matters=False
            )

    def test_order_doesnt_matter_extra_in_expected(self):
        capture = LogCapture.make(self)
        log.info('Failed to send BAR')
        log.info('Sent FOO, length 1234')
        with ShouldAssert(
            "same:\n"
            "[(<LogLevel=info>, 'Sent FOO, length 1234'),\n"
            " (<LogLevel=info>, 'Failed to send BAR')]\n"
            "\n"
            "in expected but not actual:\n"
            "[(<LogLevel=info>, 'Sent 1 Messages')]"
        ):
            capture.check(
                (INFO, S('Sent FOO, length 1234')),
                (INFO, 'Failed to send BAR'),
                (INFO, 'Sent 1 Messages'),
                order_matters=False
            )

    def test_order_doesnt_matter_extra_in_actual(self):
        capture = LogCapture.make(self)
        log.info('Failed to send BAR')
        log.info('Sent FOO, length 1234')
        log.info('Sent 1 Messages')
        with ShouldAssert(
            "same:\n"
            "[(<LogLevel=info>, 'Failed to send BAR'), (<LogLevel=info>, 'Sent 1 Messages')]\n"
            "\n"
            "in expected but not actual:\n"
            "[(<LogLevel=info>, <S:Sent FOO, length abc>)]\n"
            "\n"
            "in actual but not expected:\n"
            "[(<LogLevel=info>, 'Sent FOO, length 1234')]"
        ):
            capture.check(
                (INFO, S('Sent FOO, length abc')),
                (INFO, 'Failed to send BAR'),
                (INFO, 'Sent 1 Messages'),
                order_matters=False
            )


class TestUnifiedLogCapture(TestCase):

    def make_capture(self, **kw):
        capture = UnifiedLogCapture(sources=[TwistedSource(**kw)], install=False)
        capture.install()
        self.addCleanup(capture.uninstall)
        return capture

    def test_basic_capture(self):
        capture = self.make_capture()
        log.info('hello {name}', name='world')
        capture.check((INFO, 'hello world'))

    def test_check_order_doesnt_matter_ok(self):
        capture = self.make_capture()
        log.info('first')
        log.info('second')
        capture.check(
            (INFO, 'second'),
            (INFO, 'first'),
            order_matters=False,
        )

    def test_check_order_doesnt_matter_failure(self):
        capture = self.make_capture()
        log.info('first')
        log.info('second')
        with ShouldAssert(
            "same:\n"
            "[(<LogLevel=info>, 'second')]\n\n"
            "in expected but not actual:\n"
            "[(<LogLevel=info>, 'nope')]\n\n"
            "in actual but not expected:\n"
            "[(<LogLevel=info>, 'first')]"
        ):
            capture.check(
                (INFO, 'second'),
                (INFO, 'nope'),
                order_matters=False,
            )

    def test_raise_first_exception(self):
        capture = self.make_capture()
        try:
            raise ValueError('boom')
        except Exception:
            log.failure('oh no')
        with ShouldRaise(ValueError('boom')):
            capture.raise_first_exception()
        self.flushLoggedErrors()

    def test_raise_first_exception_with_start_index(self):
        capture = self.make_capture()
        try:
            raise ValueError('first')
        except Exception:
            log.failure('first failure')
        try:
            raise TypeError('second')
        except Exception:
            log.failure('second failure')
        with ShouldRaise(TypeError('second')):
            capture.raise_first_exception(start_index=1)
        self.flushLoggedErrors()

    def test_check_exception_str(self):
        capture = self.make_capture()
        try:
            raise ValueError('expected message')
        except Exception:
            log.failure('logged')
        capture.check_exception_str('expected message')
        self.flushLoggedErrors()

    def test_single_field(self):
        capture = self.make_capture(fields=(formatEvent,))
        log.info('hello {name}', name='world')
        capture.check('hello world')
