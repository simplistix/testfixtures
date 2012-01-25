# Copyright (c) 2009-2012 Simplistix Ltd
#
# See license.txt for more details.

from doctest import REPORT_NDIFF,ELLIPSIS
from glob import glob
from manuel import doctest, capture
from manuel.testing import TestSuite
from os.path import dirname,join,pardir

from . import compat

def test_suite():
    m =  doctest.Manuel(optionflags=REPORT_NDIFF|ELLIPSIS)
    m += compat.Manuel()
    m += capture.Manuel()
    return TestSuite(
        m,
        *glob(join(dirname(__file__),pardir,pardir,'docs','*.txt'))
        )
