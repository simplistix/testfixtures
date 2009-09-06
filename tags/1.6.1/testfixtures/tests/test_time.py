# Copyright (c) 2008 Simplistix Ltd
# See license.txt for license details.

import sample1,sample2
from time import strptime
from testfixtures import test_time,replace,compare,should_raise
from unittest import TestCase,TestSuite,makeSuite

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
    
    def test_gotcha_import(self):
        # standard `replace` caveat, make sure you
        # patch all revelent places where time
        # has been imported:
        
        @replace('time.time',test_time())
        def test_something():
            from time import time
            compare(time(),978307200.0)
            compare(sample1.str_time(),'978307201.0')

        s = should_raise(test_something,AssertionError)
        s()
        # This convoluted check is because we can't stub
        # out time, since we're testing stubbing out time ;-)
        j,t1,j,t2,j = s.raised.args[0].split("'")
        
        # check we can parse the time
        t1 = float(t1)
        # check the t2 bit was as it should be
        compare(t2,'978307201.0')

        # What you need to do is replace the imported type:
        @replace('testfixtures.tests.sample1.time',test_time())
        def test_something():
            compare(sample1.str_time(),'978307200.0')

        test_something()
        
    @replace('time.time',test_time())
    def test_repr_time(self):
        from time import time
        compare(repr(time),"<class 'testfixtures.ttime'>")

def test_suite():
    return TestSuite((
        makeSuite(TestTime),
        ))
