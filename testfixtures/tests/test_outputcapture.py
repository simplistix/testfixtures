from __future__ import with_statement
# Copyright (c) 2010 Simplistix Ltd
# See license.txt for license details.

from doctest import DocTestSuite
from testfixtures import OutputCapture
from unittest import TestSuite

class TestOutputCapture:

    def test_simple(self):
        """
        Capture output from stdout and stderr within a block.

        >>> with OutputCapture() as o:
        ...    print 'Foo!'
        ...    o.compare('Foo!')

        >>> with OutputCapture() as o:
        ...    print 'Bar!'
        ...    o.compare('Foo!')
        Traceback (most recent call last):
        ...
        AssertionError: 'Foo!' != 'Bar!'

        Both the actual and expected output are stripped of leading
        and trailing whilespace:

        >>> with OutputCapture() as o:
        ...    print '  Bar! '
        ...    o.compare(' Foo!  ')
        Traceback (most recent call last):
        ...
        AssertionError: 'Foo!' != 'Bar!'

        ``stdout`` and ``stderr`` are both captured,
        but the source of the information is not preserved:

        >>> import sys
        >>> with OutputCapture() as o:
        ...    print >>sys.stdout,'hello'
        ...    print >>sys.stderr,'out'
        ...    print >>sys.stdout,'there'
        ...    print >>sys.stderr,'now'
        ...    o.compare("hello\\nout\\nthere\\nnow\\n")

        The originals are restored from what they were:
        >>> from cStringIO import StringIO
        >>> out,err = StringIO(),StringIO()
        >>> try:
        ...   o_out,o_err=sys.stdout,sys.stderr
        ...   sys.stdout,sys.stderr=out,err
        ...   print >>sys.stdout,'1'
        ...   print >>sys.stderr,'2'
        ...   with OutputCapture() as o:
        ...     print >>sys.stdout,'3'
        ...     print >>sys.stderr,'4'
        ...   print >>sys.stdout,'5'
        ...   print >>sys.stderr,'6'
        ... finally:
        ...   sys.stdout,sys.stderr=o_out,o_err
        >>> print repr(out.getvalue())
        '1\\n5\\n'
        >>> print repr(err.getvalue())
        '2\\n6\\n'
        >>> print repr(o.output.getvalue())
        '3\\n4\\n'
        """

def test_suite():
    return TestSuite((
        DocTestSuite(),
        ))
