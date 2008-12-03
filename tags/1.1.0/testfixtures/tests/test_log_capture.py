# Copyright (c) 2008 Simplistix Ltd
# See license.txt for license details.

from testfixtures import log_capture,compare,Comparison as C
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

def test_suite():
    return TestSuite((
        makeSuite(TestLog_Capture),
        ))
