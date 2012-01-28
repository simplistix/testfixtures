# Copyright (c) 2009-2012 Simplistix Ltd
#
# See license.txt for more details.

from doctest import REPORT_NDIFF,ELLIPSIS
from glob import glob
from manuel import doctest, capture
from manuel.testing import TestSuite
from nose.plugins.skip import SkipTest
from os.path import dirname, join, pardir

import os

from . import compat

workspace = os.environ.get('WORKSPACE', join(dirname(__file__), pardir, pardir))
tests = glob(join(workspace,'docs', '*.txt'))

if not tests:
    raise SkipTest('No docs found to test') # pragma: no cover

def test_suite():
    m =  doctest.Manuel(optionflags=REPORT_NDIFF|ELLIPSIS)
    m += compat.Manuel()
    m += capture.Manuel()
    return TestSuite(m, *tests)
