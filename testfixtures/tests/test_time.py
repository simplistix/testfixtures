from __future__ import with_statement
# Copyright (c) 2008-2012 Simplistix Ltd
# See license.txt for license details.

import sample1,sample2
from os import environ
from time import strptime
from testfixtures import test_time, replace, compare, ShouldRaise
from unittest import TestCase,TestSuite,makeSuite
from test_datetime import TestTZInfo

class TestTime(TestCase):

    @replace('time.time',test_time())
    def test_time_call(self):
        from time import time
        compare(time(),978307200.0)
        compare(time(),978307201.0)
        compare(time(),978307203.0)

    @replace('time.time',test_time(2002,1,1,1,2,3))
    def test_time_supplied(self):
        from time import time
        compare(time(),1009846923.0)

    @replace('time.time',test_time(None))
    def test_time_sequence(self,t):
        t.add(2002,1,1,1,0,0)
        t.add(2002,1,1,2,0,0)
        t.add(2002,1,1,3,0,0)
        from time import time
        compare(time(),1009846800.0)
        compare(time(),1009850400.0)
        compare(time(),1009854000.0)

    @replace('time.time',test_time(None))
    def test_add_datetime_supplied(self,t):
        from datetime import datetime
        from time import time
        t.add(datetime(2002,1,1,2))
        compare(time(),1009850400.0)
        with ShouldRaise(ValueError(
            'Cannot add datetime with tzinfo set'
            )):
            t.add(datetime(2001, 1, 1, tzinfo=TestTZInfo()))
            
    @replace('time.time',test_time(None))
    def test_now_requested_longer_than_supplied(self,t):
        t.add(2002,1,1,1,0,0)
        t.add(2002,1,1,2,0,0)
        from time import time
        compare(time(),1009846800.0)
        compare(time(),1009850400.0)
        compare(time(),1009850401.0)
        compare(time(),1009850403.0)

    @replace('time.time',test_time())
    def test_call(self,t):
        compare(t(),978307200.0)
        from time import time
        compare(time(),978307201.0)
    
    @replace('time.time',test_time())
    def test_repr_time(self):
        from time import time
        compare(repr(time),"<class 'testfixtures.tdatetime.ttime'>")

    @replace('time.time',test_time(delta=10))
    def test_delta(self):
        from time import time
        compare(time(),978307200.0)
        compare(time(),978307210.0)
        compare(time(),978307220.0)
        
    @replace('time.time',test_time(delta_type='minutes'))
    def test_delta_type(self):
        from time import time
        compare(time(),978307200.0)
        compare(time(),978307260.0)
        compare(time(),978307380.0)
        
    @replace('time.time',test_time(None))
    def test_set(self):
        from time import time
        time.set(2001,1,1,1,0,1)
        compare(time(),978310801.0)
        time.set(2002,1,1,1,0,0)
        compare(time(),1009846800.0)
        compare(time(),1009846802.0)
        
    @replace('time.time',test_time(None))
    def test_set_datetime_supplied(self,t):
        from datetime import datetime
        from time import time
        t.set(datetime(2001,1,1,1,0,1))
        compare(time(),978310801.0)
        with ShouldRaise(ValueError(
            'Cannot set datetime with tzinfo set'
            )):
            t.set(datetime(2001, 1, 1, tzinfo=TestTZInfo()))
            
    @replace('time.time',test_time(None))
    def test_set_kw(self):
        from time import time
        time.set(year=2001,month=1,day=1,hour=1,second=1)
        compare(time(),978310801.0)
        
    @replace('time.time',test_time(None))
    def test_set_kw_tzinfo(self):
        from time import time
        with ShouldRaise(TypeError('Cannot set tzinfo on ttime')):
            time.set(year=2001,tzinfo=TestTZInfo())
        
    @replace('time.time',test_time(None))
    def test_set_args_tzinfo(self):
        from time import time
        with ShouldRaise(TypeError('Cannot set tzinfo on ttime')):
            time.set(2002,1,2,3,4,5,6,TestTZInfo())
        
    @replace('time.time',test_time(None))
    def test_add_kw(self):
        from time import time
        time.add(year=2001,month=1,day=1,hour=1,second=1)
        compare(time(),978310801.0)
        
    @replace('time.time',test_time(None))
    def test_add_tzinfo_kw(self):
        from time import time
        with ShouldRaise(TypeError('Cannot add tzinfo to ttime')):
            time.add(year=2001,tzinfo=TestTZInfo())
        
    @replace('time.time',test_time(None))
    def test_add_tzinfo_args(self):
        from time import time
        with ShouldRaise(TypeError('Cannot add tzinfo to ttime')):
            time.add(2001,1,2,3,4,5,6,TestTZInfo())
        
    @replace('time.time',test_time(2001,1,2,3,4,5,6))
    def test_max_number_args(self):
        from time import time
        compare(time(),978404645.0)
        
    def test_max_number_tzinfo(self):
        with ShouldRaise(TypeError(
            "You don't want to use tzinfo with test_time"
            )):
            @replace('time.time',test_time(2001,1,2,3,4,5,6,TestTZInfo()))
            def myfunc():
                pass # pragma: no cover
        
    @replace('time.time',test_time(2001,1,2))
    def test_min_number_args(self):
        from time import time
        compare(time(),978393600.0)
        
    @replace('time.time',test_time(
        year=2001,
        month=1,
        day=2,
        hour=3,
        minute=4,
        second=5,
        microsecond=6,
        ))
    def test_all_kw(self):
        from time import time
        compare(time(),978404645.0)
        
    def test_kw_tzinfo(self):
        with ShouldRaise(TypeError(
            "You don't want to use tzinfo with test_time"
            )):
            @replace('time.time',test_time(year=2001,tzinfo=TestTZInfo()))
            def myfunc():
                pass # pragma: no cover
