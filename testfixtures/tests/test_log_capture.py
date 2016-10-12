# Copyright (c) 2008-2013 Simplistix Ltd
# See license.txt for license details.

from testfixtures import log_capture, compare, Comparison as C, LogCapture
from unittest import TestCase

from logging import getLogger

root = getLogger()
one = getLogger('one')
two = getLogger('two')
child = getLogger('one.child')


class TestLog_Capture(TestCase):

    @log_capture('two', 'one.child')
    @log_capture('one')
    @log_capture()
    def test_logging(self, l1, l2, l3):
        # we can now log as normal
        root.info('1')
        one.info('2')
        two.info('3')
        child.info('4')
        # and later check what was logged
        l1.check(
            ('root', 'INFO', '1'),
            ('one', 'INFO', '2'),
            ('two', 'INFO', '3'),
            ('one.child', 'INFO', '4'),
            )
        l2.check(
            ('one', 'INFO', '2'),
            ('one.child', 'INFO', '4')
            )
        l3.check(
            ('two', 'INFO', '3'),
            ('one.child', 'INFO', '4')
            )
        # each logger also exposes the real
        # log records should anything else be neeeded
        compare(l3.records, [
            C('logging.LogRecord'),
            C('logging.LogRecord'),
            ])

    def test_uninstall_properly(self):
        root = getLogger()
        child = getLogger('child')
        before_root = root.handlers[:]
        before_child = child.handlers[:]
        try:
            old_root_level = root.level
            root.setLevel(49)
            old_child_level = child.level
            child.setLevel(69)

            @log_capture('child')
            @log_capture()
            def test_method(l1, l2):
                root = getLogger()
                root.info('1')
                self.assertEqual(root.level, 1)
                child = getLogger('child')
                self.assertEqual(child.level, 1)
                child.info('2')
                l1.check(
                    ('root', 'INFO', '1'),
                    ('child', 'INFO', '2'),
                    )
                l2.check(
                    ('child', 'INFO', '2'),
                    )

            test_method()

            self.assertEqual(root.level, 49)
            self.assertEqual(child.level, 69)

            self.assertEqual(root.handlers, before_root)
            self.assertEqual(child.handlers, before_child)

        finally:
            root.setLevel(old_root_level)
            child.setLevel(old_child_level)

    @log_capture()
    def test_decorator_returns_logcapture(self, l):
        # check for what we get, so we only have to write
        # tests in test_logcapture.py
        self.failUnless(isinstance(l, LogCapture))

    def test_remove_existing_handlers(self):
        logger = getLogger()
        # get original handlers
        original = logger.handlers
        try:
            # put in a stub which will blow up if used
            logger.handlers = start = [object()]

            @log_capture()
            def test_method(l):
                logger.info('during')
                l.check(('root', 'INFO', 'during'))

            test_method()

            compare(logger.handlers, start)

        finally:
            logger.handlers = original

    def test_clear_global_state(self):
        from logging import _handlers, _handlerList
        capture = LogCapture()
        capture.uninstall()
        self.assertFalse(capture in _handlers)
        self.assertFalse(capture in _handlerList)

    def test_no_propogate(self):
        logger = getLogger('child')
        # paranoid check
        compare(logger.propagate, True)

        @log_capture('child', propagate=False)
        def test_method(l):
            logger.info('a log message')
            l.check(('child', 'INFO', 'a log message'))

        with LogCapture() as global_log:
            test_method()

        global_log.check()
        compare(logger.propagate, True)

    def test_different_attributes(self):
        with LogCapture(attributes=('funcName', 'processName')) as log:
            getLogger().info('oh hai')
        log.check(
            ('test_different_attributes', 'MainProcess')
        )

    def test_missing_attribute(self):
        with LogCapture(attributes=('msg', 'lolwut')) as log:
            getLogger().info('oh %s', 'hai')
        log.check(
            ('oh %s', None)
        )

    def test_single_attribute(self):
        # one which isn't a string, to boot!
        with LogCapture(attributes=['msg']) as log:
            getLogger().info(dict(foo='bar', baz='bob'))
        log.check(
            dict(foo='bar', baz='bob'),
        )

    def test_msg_is_none(self):
        with LogCapture(attributes=('msg', 'foo')) as log:
            getLogger().info(None, extra=dict(foo='bar'))
        log.check(
            (None, 'bar')
        )
