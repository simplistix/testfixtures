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

# using a set up and teardown function
# gets rid of the need for the imports in
# doc tests

def setUp(test):
    test.globs['log_capture']=LogCapture()

def tearDown(test):
    test.globs['log_capture'].uninstall()
    
def test_suite():
    return TestSuite((
        DocTestSuite(setUp=setUp,tearDown=tearDown),
        ))
