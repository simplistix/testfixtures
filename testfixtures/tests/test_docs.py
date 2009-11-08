# Copyright (c) 2009 Simplistix Ltd
#
# See license.txt for more details.

import unittest

from glob import glob
from os.path import dirname,join,pardir
from doctest import DocFileSuite,REPORT_NDIFF,ELLIPSIS

options = REPORT_NDIFF|ELLIPSIS

def test_suite():
    return unittest.TestSuite((
        DocFileSuite(
                *glob(join(dirname(__file__),pardir,'docs','*.txt')),
                module_relative=False,
                optionflags=options
                ),
        ))
