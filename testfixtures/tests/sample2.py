# Copyright (c) 2008-2013 Simplistix Ltd
# See license.txt for license details.
"""
A sample module containing the kind of code that
TestFixtures helps with testing
"""

from testfixtures.tests.sample1 import X, z

try:
    from guppy import hpy
    guppy = True
except ImportError:
    guppy = False


def dump(path):
    if guppy:
        hpy().heap().stat.dump(path)
