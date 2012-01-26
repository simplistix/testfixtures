from __future__ import with_statement
# Copyright (c) 2008-2012 Simplistix Ltd
# See license.txt for license details.

import atexit

from doctest import DocTestSuite
from testfixtures import LogCapture, compare
from unittest import TestSuite, TestCase, makeSuite

from logging import getLogger

from .compat import catch_warnings

root = getLogger()
one = getLogger('one')
two = getLogger('two')
child = getLogger('one.child')

class DemoLogCapture:

    def test_simple(self): # pragma: no branch
        """
        >>> root.info('some logging')
        >>> print log_capture
        root INFO
          some logging
        >>> log_capture.clear()
        >>> print log_capture
        No logging captured
        >>> root.info('some more logging')
        >>> print log_capture
        root INFO
          some more logging
        """

class TestLogCapture:

    def test_simple(self): # pragma: no branch
        """
        >>> root.info('before')
        >>> l = LogCapture()
        >>> root.info('during')
        >>> l.uninstall()
        >>> root.info('after')
        >>> print l
        root INFO
          during
        """

    def test_specific_logger(self): # pragma: no branch
        """
        >>> l = LogCapture('one')
        >>> root.info('1')
        >>> one.info('2')
        >>> two.info('3')
        >>> child.info('4')
        >>> l.uninstall()
        >>> print l
        one INFO
          2
        one.child INFO
          4
        """

    def test_multiple_loggers(self): # pragma: no branch
        """
        >>> l = LogCapture(('one.child','two'))
        >>> root.info('1')
        >>> one.info('2')
        >>> two.info('3')
        >>> child.info('4')
        >>> l.uninstall()
        >>> print l
        two INFO
          3
        one.child INFO
          4
        """

    def test_simple_manual_install(self): # pragma: no branch
        """
        >>> l = LogCapture(install=False)
        >>> root.info('before')
        >>> l.install()
        >>> root.info('during')
        >>> l.uninstall()
        >>> root.info('after')
        >>> print l
        root INFO
          during
        """

    def test_uninstall(self): # pragma: no branch
        """
        Lets start off with a couple of loggers:
        
        >>> root = getLogger()
        >>> child = getLogger('child')

        Lets also record the handlers for these loggers before
        we start the test:
        
        >>> before_root = root.handlers[:]
        >>> before_child = child.handlers[:]

        Lets also record the levels for the loggers:
        
        >>> old_root_level=root.level
        >>> old_child_level=child.level
        
        Now the test:
        
        >>> try:
        ...    root.setLevel(49)
        ...    child.setLevel(69)
        ...
        ...    l1 = LogCapture()
        ...    l2 = LogCapture('child')
        ...
        ...    root = getLogger()
        ...    root.info('1')
        ...    print 'root level during test:',root.level
        ...    child = getLogger('child')
        ...    print 'child level during test:',child.level
        ...    child.info('2')
        ...    print 'l1 contents:'
        ...    print l1
        ...    print 'l2 contents:'
        ...    print l2
        ...
        ...    l2.uninstall()
        ...    l1.uninstall()
        ...
        ...    print 'root level after test:',root.level
        ...    print 'child level after test:',child.level
        ...
        ... finally:
        ...    root.setLevel(old_root_level)
        ...    child.setLevel(old_child_level)
        root level during test: 1
        child level during test: 1
        l1 contents:
        root INFO
          1
        child INFO
          2
        l2 contents:
        child INFO
          2
        root level after test: 49
        child level after test: 69

        Now we check the handlers are as they were before
        the test:

        >>> root.handlers == before_root
        True
        >>> child.handlers == before_child
        True
        """

    def test_uninstall_all(self): # pragma: no branch
        """
        For this test, it's better if we don't have any
        LogCaptures around when we start:
        
        >>> log_capture.uninstall()
        
        If you create several LogCaptures during a doctest,
        it can create clutter to uninstall them all.
        If this is the case, use the classmethod
        LogCapture.uninstall_all() as a tearDown function
        to remove them all:

        >>> before_handlers_root = root.handlers[:]
        >>> before_handlers_child = child.handlers[:]
        
        >>> l1 = LogCapture()
        >>> l2 = LogCapture('one.child')

        We can see that the LogCaptures have changed the
        handlers, removing existing ones and installing
        their own:
        
        >>> len(root.handlers)
        1
        >>> root.handlers==before_handlers_root
        False
        >>> len(child.handlers)
        1
        >>> child.handlers==before_handlers_child
        False
        
        Now we show the function in action:

        >>> LogCapture.uninstall_all()

        ...and we can see the handlers are back as
        they were beefore:
        
        >>> before_handlers_root == root.handlers
        True
        >>> before_handlers_child == child.handlers
        True
        """

    def test_two_logcaptures_on_same_logger(self): # pragma: no branch
        """
        If you create more than one LogCaptures on a single
        logger, the 2nd one installed will stop the first
        one working!
        
        >>> l1 = LogCapture()
        >>> root.info('1st message')
        >>> print l1
        root INFO
          1st message
        >>> l2 = LogCapture()
        >>> root.info('2nd message')

        So, l1 missed this message:
        
        >>> print l1
        root INFO
          1st message

        ...because l2 kicked it out and recorded the message:

        >>> print l2
        root INFO
          2nd message
        """

    def test_uninstall_more_than_once(self): # pragma: no branch
        """
        For this test, it's better if we don't have any
        LogCaptures around when we start:
        
        >>> log_capture.uninstall()

        There's no problem with uninstalling a LogCapture
        more than once:

        >>> old_level = root.level
        >>> try:
        ...    root.setLevel(49)
        ...
        ...    l = LogCapture()
        ...
        ...    print 'root level during test:',root.level
        ...    
        ...    l.uninstall()
        ...
        ...    print 'root level after uninstall:',root.level
        ...
        ...    root.setLevel(69)
        ...    
        ...    l.uninstall()
        ...
        ...    print 'root level after another uninstall:',root.level
        ...
        ... finally:
        ...    root.setLevel(old_level)
        root level during test: 1
        root level after uninstall: 49
        root level after another uninstall: 69

        And even when loggers have been uninstalled, there's
        no problem having uninstall_all as a backstop:

        >>> log_capture.uninstall_all()
        """
        
    def test_with_statement(self): # pragma: no branch
        """
        >>> root.info('before')
        >>> with LogCapture() as l:
        ...   root.info('during')
        >>> root.info('after')
        >>> print l
        root INFO
          during
        """

class LogCaptureTests(TestCase):

    def test_remove_existing_handlers(self):
        logger = getLogger()
        # get original handlers
        original_handlers = logger.handlers
        # put in a stub which will blow up if used
        try:
            logger.handlers = start = [object()]

            with LogCapture() as l:
                logger.info('during')  # pragma: no branch

            l.check(('root', 'INFO', 'during'))
                
            compare(logger.handlers,start)

        finally:
            # only executed if the test fails
            logger.handlers = original_handlers

    def test_atexit(self):
        l = LogCapture()
        self.assertTrue(
            LogCapture.atexit in [t[0] for t in atexit._exithandlers]
            )
        with catch_warnings(record=True) as w:
            l.atexit()
            self.assertTrue(len(w), 1)
            compare(str(w[0].message), (
                "LogCapture instances not uninstalled by shutdown, "
                "loggers captured:\n"
                "(None,)"
                ))
        l.uninstall()
        # check running it again has no ill effects
        l.atexit()
        
# using a set up and teardown function
# gets rid of the need for the imports in
# doc tests

def setUp(test):
    test.globs['log_capture']=LogCapture()

def tearDown(test):
    test.globs['log_capture'].uninstall_all()
    
def test_suite():
    return TestSuite((
        DocTestSuite(setUp=setUp,tearDown=tearDown),
        makeSuite(LogCaptureTests),        
        ))
