# Copyright (c) 2008-2010 Simplistix Ltd
# See license.txt for license details.

import sample1,sample2
from datetime import date
from datetime import datetime as d, tzinfo
from time import strptime
from testfixtures import test_datetime,test_date
from testfixtures import replace,Replacer,compare,should_raise
from unittest import TestCase,TestSuite,makeSuite

class atzinfo(tzinfo):
    def utcoffset(self,dt): return
    def dst(self,dt): return
    
class TestDateTime(TestCase):

    # NB: Only the now method is currently stubbed out,
    #     if you need other methods, tests and patches
    #     greatfully received!

    @replace('datetime.datetime',test_datetime())
    def test_now(self):
        from datetime import datetime
        compare(datetime.now(),d(2001,1,1,0,0,0))
        compare(datetime.now(),d(2001,1,1,0,0,10))
        compare(datetime.now(),d(2001,1,1,0,0,30))

    @replace('datetime.datetime',test_datetime(2002,1,1,1,2,3))
    def test_now_supplied(self):
        from datetime import datetime
        compare(datetime.now(),d(2002,1,1,1,2,3))

    @replace('datetime.datetime',test_datetime(None))
    def test_now_sequence(self,t):
        t.add(2002,1,1,1,0,0)
        t.add(2002,1,1,2,0,0)
        t.add(2002,1,1,3,0,0)
        from datetime import datetime
        compare(datetime.now(),d(2002,1,1,1,0,0))
        compare(datetime.now(),d(2002,1,1,2,0,0))
        compare(datetime.now(),d(2002,1,1,3,0,0))

    @replace('datetime.datetime',test_datetime(None))
    def test_now_requested_longer_than_supplied(self,t):
        t.add(2002,1,1,1,0,0)
        t.add(2002,1,1,2,0,0)
        from datetime import datetime
        compare(datetime.now(),d(2002,1,1,1,0,0))
        compare(datetime.now(),d(2002,1,1,2,0,0))
        compare(datetime.now(),d(2002,1,1,2,0,10))
        compare(datetime.now(),d(2002,1,1,2,0,30))

    @replace('datetime.datetime',test_datetime())
    def test_call(self,t):
        compare(t(2002,1,2,3,4,5),d(2002,1,2,3,4,5))
        from datetime import datetime
        dt = datetime(2001,1,1,1,0,0)
        self.failIf(dt.__class__ is d)
        compare(dt,d(2001,1,1,1,0,0))
    
    def test_date_return_type(self):
        with Replacer() as r:
            r.replace('datetime.datetime',test_datetime())
            from datetime import datetime
            dt = datetime(2001,1,1,1,0,0)
            d = dt.date()
            compare(d,date(2001,1,1))
            self.failUnless(d.__class__ is date)
    
    def test_date_return_type_picky(self):
        # type checking is a bitch :-/
        date_type = test_date()
        with Replacer() as r:
            r.replace('datetime.datetime',test_datetime(
                    date_type=date_type
                    ))
            from datetime import datetime
            dt = datetime(2010,8,26,14,33,13)
            d = dt.date()
            compare(d,date_type(2010,8,26))
            self.failUnless(d.__class__ is date_type)
    
    def test_gotcha_import(self):
        # standard `replace` caveat, make sure you
        # patch all revelent places where datetime
        # has been imported:
        
        @replace('datetime.datetime',test_datetime())
        def test_something():
            from datetime import datetime
            compare(datetime.now(),d(2001,1,1,0,0,0))
            compare(sample1.str_now_1(),'2001-01-01 00:00:10')

        s = should_raise(test_something,AssertionError)
        s()
        # This convoluted check is because we can't stub
        # out the datetime, since we're testing stubbing out
        # the datetime ;-)
        j,dt1,j,dt2,j = s.raised.args[0].split("'")
        if '.' in dt1:
            dt1,ms = dt1.split('.')
            # check ms is just an int
            int(ms)
        # check we can parse the date
        dt1 = strptime(dt1,'%Y-%m-%d %H:%M:%S')
        # check the dt2 bit was as it should be
        compare(dt2,'2001-01-01 00:00:10')

        # What you need to do is replace the imported type:
        @replace('testfixtures.tests.sample1.datetime',test_datetime())
        def test_something():
            compare(sample1.str_now_1(),'2001-01-01 00:00:00')

        test_something()
        
    def test_gotcha_import_and_obtain(self):
        # Another gotcha is where people have locally obtained
        # a class attributes, where the normal patching doesn't
        # work:
        
        @replace('testfixtures.tests.sample1.datetime',test_datetime())
        def test_something():
            compare(sample1.str_now_2(),'2001-01-01 00:00:00')

        s = should_raise(test_something,AssertionError)
        s()
        # This convoluted check is because we can't stub
        # out the datetime, since we're testing stubbing out
        # the datetime ;-)
        j,dt1,j,dt2,j = s.raised.args[0].split("'")
        if '.' in dt1:
            dt1,ms = dt1.split('.')
            # check ms is just an int
            int(ms)
        # check we can parse the date
        dt1 = strptime(dt1,'%Y-%m-%d %H:%M:%S')
        # check the dt2 bit was as it should be
        compare(dt2,'2001-01-01 00:00:00')

        # What you need to do is replace the imported name:
        @replace('testfixtures.tests.sample1.now',test_datetime().now)
        def test_something():
            compare(sample1.str_now_2(),'2001-01-01 00:00:00')

        test_something()


    # if you have an embedded `now` as above, *and* you need to supply
    # a list of required datetimes, then it's often simplest just to
    # do a manual try-finally with a replacer:
    def test_import_and_obtain_with_lists(self):
        
        t = test_datetime(None)
        t.add(2002,1,1,1,0,0)
        t.add(2002,1,1,2,0,0)

        from testfixtures import Replacer
        r = Replacer()
        r.replace('testfixtures.tests.sample1.now',t.now)
        try:
            compare(sample1.str_now_2(),'2002-01-01 01:00:00')
            compare(sample1.str_now_2(),'2002-01-01 02:00:00')
        finally:
            r.restore()
        
    @replace('datetime.datetime',test_datetime())
    def test_repr(self):
        from datetime import datetime
        compare(repr(datetime),"<class 'testfixtures.tdatetime'>")


    @replace('datetime.datetime',test_datetime(delta=1))
    def test_delta(self):
        from datetime import datetime
        compare(datetime.now(),d(2001,1,1,0,0,0))
        compare(datetime.now(),d(2001,1,1,0,0,1))
        compare(datetime.now(),d(2001,1,1,0,0,2))
        
    @replace('datetime.datetime',test_datetime(delta_type='minutes'))
    def test_delta_type(self):
        from datetime import datetime
        compare(datetime.now(),d(2001,1,1,0,0,0))
        compare(datetime.now(),d(2001,1,1,0,10,0))
        compare(datetime.now(),d(2001,1,1,0,30,0))
        
    @replace('datetime.datetime',test_datetime(None))
    def test_set(self):
        from datetime import datetime
        datetime.set(2001,1,1,1,0,1)
        compare(datetime.now(),d(2001,1,1,1,0,1))
        datetime.set(2002,1,1,1,0,0)
        compare(datetime.now(),d(2002,1,1,1,0,0))
        compare(datetime.now(),d(2002,1,1,1,0,20))
        
    @replace('datetime.datetime',test_datetime(2001,1,2,3,4,5,6,atzinfo()))
    def test_max_number_args(self):
        from datetime import datetime
        compare(datetime.now(),d(2001,1,2,3,4,5,6,atzinfo()))
        
    @replace('datetime.datetime',test_datetime(2001,1,2))
    def test_min_number_args(self):
        from datetime import datetime
        compare(datetime.now(),d(2001,1,2))
        
def test_suite():
    return TestSuite((
        makeSuite(TestDateTime),
        ))
