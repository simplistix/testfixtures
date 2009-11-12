# Copyright (c) 2008 Simplistix Ltd
# See license.txt for license details.
"""
A sample module containing the kind of code that
TestFixtures helps with testing
"""

from sample1 import X
from sample1 import z

try:
    from guppy import hpy
    guppy = True
except ImportError:
    guppy = False

def dump(path):
    if guppy:
        hpy().heap().stat.dump(path)
