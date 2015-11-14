# Copyright (c) 2010-2012 Simplistix Ltd
#
# See license.txt for more details.
from os.path import dirname
path_to_your_docs = dirname(__file__)

from glob import glob
from manuel import doctest, capture
from manuel.testing import TestSuite
from os.path import join
from testfixtures import TempDirectory
from testfixtures.manuel import Files

from . import compat


def setUp(test):
    test.globs['tempdir'] = TempDirectory()


def tearDown(test):
    test.globs['tempdir'].cleanup()


def test_suite():
    m = doctest.Manuel()
    m += compat.Manuel()
    m += capture.Manuel()
    m += Files('tempdir')
    return TestSuite(
        m,
        setUp=setUp,
        tearDown=tearDown,
        *glob(join(path_to_your_docs, '*.txt'))
        )
