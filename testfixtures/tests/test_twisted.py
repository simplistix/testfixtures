from twisted.logger import Logger, formatEvent
from twisted.python.failure import Failure
from twisted.trial.unittest import TestCase

from testfixtures import compare, ShouldRaise
from testfixtures.twisted import LogCapture, INFO

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
        compare(capture.events[0]['log_namespace'], expected='testfixtures.tests.test_twisted')

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
