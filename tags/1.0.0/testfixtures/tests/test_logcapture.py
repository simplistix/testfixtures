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

class TestLogCapture:

    def test_simple(self):
        """
        >>> l = LogCapture()
        >>> root.info('before')
        >>> l.install()
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
        >>> l.install()
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
        >>> l = LogCapture('one.child','two')
        >>> l.install()
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

def test_suite():
    return TestSuite((
        DocTestSuite(),
        ))
