# Copyright (c) 2009-2013 Simplistix Ltd
#
# See license.txt for more details.

from doctest import REPORT_NDIFF, ELLIPSIS
from glob import glob
from manuel import doctest, capture
from manuel.testing import TestSuite
from nose.plugins.skip import SkipTest
from os.path import dirname, join, pardir

from . import compat

tests = glob(join(join(dirname(__file__), pardir, pardir), 'docs', '*.txt'))

if not tests:
    # tox can't find docs and installing an sdist doesn't install the docs
    raise SkipTest('No docs found to test')  # pragma: no cover


def test_suite():
    m = doctest.Manuel(optionflags=REPORT_NDIFF | ELLIPSIS,
                       checker=compat.DocTestChecker())
    m += compat.Manuel()
    m += capture.Manuel()
    return TestSuite(m, *tests)
