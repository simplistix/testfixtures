# Copyright (c) 2008-2011 Simplistix Ltd
# See license.txt for license details.

## import sys

## from calendar import timegm
## from cStringIO import StringIO
## from datetime import datetime,timedelta,date
## from difflib import unified_diff
## from functools import partial,wraps
## from new import classobj
## from pprint import pformat
## 
## from types import ClassType,GeneratorType,MethodType

class singleton(object):
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return '<%s>' % self.name
    __str__ = __repr__
    
identity = singleton('identity')
not_there = singleton('not_there')

from testfixtures.comparison import Comparison, StringComparison, compare, diff
from testfixtures.tdatetime import test_datetime, test_date, test_time
from testfixtures.logcapture import LogCapture, log_capture
from testfixtures.outputcapture import OutputCapture
from testfixtures.resolve import resolve
from testfixtures.replace import Replacer, replace
from testfixtures.shouldraise import ShouldRaise, should_raise
from testfixtures.tempdirectory import TempDirectory, tempdir
from testfixtures.utils import wrap, generator
