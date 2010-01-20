from __future__ import with_statement
# Copyright (c) 2008 Simplistix Ltd
# See license.txt for license details.

from doctest import DocTestSuite
from testfixtures import LogCapture
from unittest import TestSuite

from logging import getLogger

root = getLogger()
one = getLogger('one')
two = getLogger('two')
child = getLogger('one.child')

class DemoLogCapture:

    def test_simple(self):
        """
        >>> root.info('some logging')
        >>> print log_capture
        root INFO
          some logging
        >>> log_capture.clear()
        >>> print log_capture
        <BLANKLINE>
        >>> root.info('some more logging')
        >>> print log_capture
        root INFO
          some more logging
        """

class TestLogCapture:

    def test_simple(self):
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

    def test_specific_logger(self):
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

    def test_multiple_loggers(self):
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

    def test_simple_manual_install(self):
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

    def test_uninstall(self):
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

    def test_uninstall_all(self):
        """
        For this test, it's better if we don't have any
        LogCaptures around when we start:
        
        >>> log_capture.uninstall()
        
        If you create several LogCaptures during a doctest,
        it can create clutter to uninstall them all.
        If this is the case, use the classmethod
        LogCapture.uninstall_all() as a tearDown function
        to remove them all:

        >>> before_handlers = root.handlers[:]
        >>> l1 = LogCapture()
        >>> after_1_handlers = root.handlers[:]
        >>> l2 = LogCapture()
        >>> after_2_handlers = root.handlers[:]

        Some sanity checks:

        >>> len(after_1_handlers)-len(before_handlers)
        1
        >>> len(after_2_handlers)-len(before_handlers)
        2

        Now we show the function in action:

        >>> LogCapture.uninstall_all()

        >>> before_handlers == root.handlers
        True
        """

    def test_uninstall_more_than_onces(self):
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
        
    def test_with_statement(self):
        """
        >>> root.info('before')
        >>> with LogCapture() as l:
        ...   root.info('during')
        >>> root.info('after')
        >>> print l
        root INFO
          during
        """

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
        ))
