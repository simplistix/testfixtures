# Copyright (c) 2008-2010 Simplistix Ltd
# See license.txt for license details.

from testfixtures import log_capture,compare,Comparison as C, LogCapture
from unittest import TestCase,TestSuite,makeSuite

from logging import getLogger

root = getLogger()
one = getLogger('one')
two = getLogger('two')
child = getLogger('one.child')

class TestLog_Capture(TestCase):

    
    @log_capture('two','one.child')
    @log_capture('one')
    @log_capture()
    def test_logging(self,l1,l2,l3):
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
        compare(l3.records,[
            C('logging.LogRecord'),
            C('logging.LogRecord'),
            ])

    def test_uninstall_properly(self):
        root = getLogger()
        child = getLogger('child')
        before_root = root.handlers[:]
        before_child = child.handlers[:]
        try:
            old_root_level=root.level
            root.setLevel(49)
            old_child_level=child.level
            child.setLevel(69)
            
            @log_capture('child')
            @log_capture()
            def test_method(l1,l2):
                root = getLogger()
                root.info('1')
                self.assertEqual(root.level,1)
                child = getLogger('child')
                self.assertEqual(child.level,1)
                child.info('2')
                l1.check(
                    ('root', 'INFO', '1'),
                    ('child', 'INFO', '2'),
                    )
                l2.check(
                    ('child', 'INFO', '2'),
                    )

            test_method()
            
            self.assertEqual(root.level,49)
            self.assertEqual(child.level,69)

            self.assertEqual(root.handlers,before_root)
            self.assertEqual(child.handlers,before_child)
            
        finally:
            root.setLevel(old_root_level)
            child.setLevel(old_child_level)
            
    @log_capture()
    def test_decorator_returns_logcapture(self,l):
        # check for what we get, so we only have to write
        # tests in test_logcapture.py
        self.failUnless(isinstance(l,LogCapture))


    def test_remove_existing_handlers(self):
        logger = getLogger()
        # get original handlers
        original_handlers = logger.handlers
        # put in a stub which will blow up if used
        original = logger.handlers
        try:
            logger.handlers = start = [object()]

            @log_capture()
            def test_method(l):
                logger.info('during')
                l.check(('root', 'INFO', 'during'))

            test_method()
            
            compare(logger.handlers, start)
            
        finally:
            logger.handlers = original
