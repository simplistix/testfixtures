# Copyright (c) 2008 Simplistix Ltd
# See license.txt for license details.

import sample1,sample2
from datetime import date as d
from time import strptime
from testfixtures import test_date,replace,compare,should_raise
from unittest import TestCase,TestSuite,makeSuite

class TestDate(TestCase):

    # NB: Only the today method is currently stubbed out,
    #     if you need other methods, tests and patches
    #     greatfully received!

    @replace('datetime.date',test_date())
    def test_today(self):
        from datetime import date
        compare(date.today(),d(2001,1,1))
        compare(date.today(),d(2001,1,2))
        compare(date.today(),d(2001,1,4))

    @replace('datetime.date',test_date(2001,2,3))
    def test_today_supplied(self):
        from datetime import date
        compare(date.today(),d(2001,2,3))

    @replace('datetime.date',test_date(None))
    def test_today_sequence(self,t):
        t.add(2002,1,1)
        t.add(2002,1,2)
        t.add(2002,1,3)
        from datetime import date
        compare(date.today(),d(2002,1,1))
        compare(date.today(),d(2002,1,2))
        compare(date.today(),d(2002,1,3))

    @replace('datetime.date',test_date(None))
    def test_today_requested_longer_than_supplied(self,t):
        t.add(2002,1,1)
        t.add(2002,1,2)
        from datetime import date
        compare(date.today(),d(2002,1,1))
        compare(date.today(),d(2002,1,2))
        compare(date.today(),d(2002,1,3))
        compare(date.today(),d(2002,1,5))

    @replace('datetime.date',test_date())
    def test_call(self,t):
        compare(t(2002,1,2),d(2002,1,2))
        from datetime import date
        dt = date(2003,2,1)
        self.failIf(dt.__class__ is d)
        compare(dt,d(2003,2,1))
    
    def test_gotcha_import(self):
        # standard `replace` caveat, make sure you
        # patch all revelent places where date
        # has been imported:
        
        @replace('datetime.date',test_date())
        def test_something():
            from datetime import date
            compare(date.today(),d(2001,1,1))
            compare(sample1.str_today_1(),'2001-01-02')

        s = should_raise(test_something,AssertionError)
        s()
        # This convoluted check is because we can't stub
        # out the date, since we're testing stubbing out
        # the date ;-)
        j,dt1,j,dt2,j = s.raised.args[0].split("'")
        # check we can parse the date
        dt1 = strptime(dt1,'%Y-%m-%d')
        # check the dt2 bit was as it should be
        compare(dt2,'2001-01-02')

        # What you need to do is replace the imported type:
        @replace('testfixtures.tests.sample1.date',test_date())
        def test_something():
            compare(sample1.str_today_1(),'2001-01-01')

        test_something()
        
    def test_gotcha_import_and_obtain(self):
        # Another gotcha is where people have locally obtained
        # a class attributes, where the normal patching doesn't
        # work:
        
        @replace('testfixtures.tests.sample1.date',test_date())
        def test_something():
            compare(sample1.str_today_2(),'2001-01-01')

        s = should_raise(test_something,AssertionError)
        s()
        # This convoluted check is because we can't stub
        # out the date, since we're testing stubbing out
        # the date ;-)
        j,dt1,j,dt2,j = s.raised.args[0].split("'")
        # check we can parse the date
        dt1 = strptime(dt1,'%Y-%m-%d')
        # check the dt2 bit was as it should be
        compare(dt2,'2001-01-01')

        # What you need to do is replace the imported name:
        @replace('testfixtures.tests.sample1.today',test_date().today)
        def test_something():
            compare(sample1.str_today_2(),'2001-01-01')

        test_something()


    # if you have an embedded `today` as above, *and* you need to supply
    # a list of required dates, then it's often simplest just to
    # do a manual try-finally with a replacer:
    def test_import_and_obtain_with_lists(self):
        
        t = test_date(None)
        t.add(2002,1,1)
        t.add(2002,1,2)

        from testfixtures import Replacer
        r = Replacer()
        r.replace('testfixtures.tests.sample1.today',t.today)
        try:
            compare(sample1.str_today_2(),'2002-01-01')
            compare(sample1.str_today_2(),'2002-01-02')
        finally:
            r.restore()

    @replace('datetime.date',test_date())
    def test_repr(self):
        from datetime import date
        compare(repr(date),"<class 'testfixtures.tdate'>")

    @replace('datetime.date',test_date(delta=2))
    def test_delta(self):
        from datetime import date
        compare(date.today(),d(2001,1,1))
        compare(date.today(),d(2001,1,3))
        compare(date.today(),d(2001,1,5))
        
    @replace('datetime.date',test_date(delta_type='weeks'))
    def test_delta_type(self):
        from datetime import date
        compare(date.today(),d(2001,1,1))
        compare(date.today(),d(2001,1,8))
        compare(date.today(),d(2001,1,22))
        
    @replace('datetime.date',test_date(None))
    def test_set(self):
        from datetime import date
        date.set(2001,1,2)
        compare(date.today(),d(2001,1,2))
        date.set(2002,1,1)
        compare(date.today(),d(2002,1,1))
        compare(date.today(),d(2002,1,3))
        
def test_suite():
    return TestSuite((
        makeSuite(TestDate),
        ))
