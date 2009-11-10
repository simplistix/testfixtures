# Copyright (c) 2009 Simplistix Ltd
#
# See license.txt for more details.

from glob import glob
from manuel import doctest,codeblock
from manuel.testing import TestSuite
from os.path import dirname,join,pardir
from doctest import REPORT_NDIFF,ELLIPSIS

def test_suite():
    m =  doctest.Manuel(optionflags=REPORT_NDIFF|ELLIPSIS)
    m += codeblock.Manuel()
    return TestSuite(
        m,
        *glob(join(dirname(__file__),pardir,pardir,'docs','*.txt'))
        )
