# Copyright (c) 2009-2010 Simplistix Ltd
#
# See license.txt for more details.

from doctest import REPORT_NDIFF,ELLIPSIS
from glob import glob
from manuel import doctest,codeblock,capture
from manuel.testing import TestSuite
from os.path import dirname,join,pardir

def test_suite():
    m =  doctest.Manuel(optionflags=REPORT_NDIFF|ELLIPSIS)
    m += codeblock.Manuel()
    m += capture.Manuel()
    return TestSuite(
        m,
        *glob(join(dirname(__file__),pardir,pardir,'docs','*.txt'))
        )
