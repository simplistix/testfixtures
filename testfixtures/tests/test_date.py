from datetime import date as d, timedelta, date
from time import strptime
from typing import cast

from testfixtures import ShouldRaise, mock_date, replace, compare
from testfixtures.datetime import MockDate
from testfixtures.tests import sample1, sample2
from unittest import TestCase


class TestDate(TestCase):

    # NB: Only the today method is currently stubbed out,
    #     if you need other methods, tests and patches
    #     greatfully received!

    @replace('datetime.date', mock_date())
    def test_today(self) -> None:
        from datetime import date
        compare(date.today(), d(2001, 1, 1))
        compare(date.today(), d(2001, 1, 2))
        compare(date.today(), d(2001, 1, 4))

    @replace('datetime.date', mock_date(2001, 2, 3))
    def test_today_supplied(self) -> None:
        from datetime import date
        compare(date.today(), d(2001, 2, 3))

    @replace('datetime.date', mock_date(year=2001, month=2, day=3))
    def test_today_all_kw(self) -> None:
        from datetime import date
        compare(date.today(), d(2001, 2, 3))

    @replace('datetime.date', mock_date(None))
    def test_today_sequence(self, t: type[MockDate]) -> None:
        t.add(2002, 1, 1)
        t.add(2002, 1, 2)
        t.add(2002, 1, 3)
        from datetime import date
        compare(date.today(), d(2002, 1, 1))
        compare(date.today(), d(2002, 1, 2))
        compare(date.today(), d(2002, 1, 3))

    @replace('datetime.date', mock_date(None))
    def test_today_requested_longer_than_supplied(self, t: type[MockDate]) -> None:
        t.add(2002, 1, 1)
        t.add(2002, 1, 2)
        from datetime import date
        compare(date.today(), d(2002, 1, 1))
        compare(date.today(), d(2002, 1, 2))
        compare(date.today(), d(2002, 1, 3))
        compare(date.today(), d(2002, 1, 5))

    @replace('datetime.date', mock_date(None))
    def test_add_date_supplied(self) -> None:
        from datetime import date
        date_mock = cast(type[MockDate], date)
        date_mock.add(d(2001, 1, 2))
        date_mock.add(date(2001, 1, 3))
        compare(date.today(), d(2001, 1, 2))
        compare(date.today(), d(2001, 1, 3))

    def test_instantiate_with_date(self) -> None:
        from datetime import date
        t = mock_date(date(2002, 1, 1))
        compare(t.today(), d(2002, 1, 1))

    @replace('datetime.date', mock_date(strict=True))
    def test_call(self, t: type[MockDate]) -> None:
        compare(t(2002, 1, 2), d(2002, 1, 2))
        from datetime import date
        dt = date(2003, 2, 1)
        self.assertFalse(dt.__class__ is d)
        compare(dt, d(2003, 2, 1))

    def test_gotcha_import(self) -> None:
        # standard `replace` caveat, make sure you
        # patch all relevant places where date
        # has been imported:

        @replace('datetime.date', mock_date())
        def test_something() -> None:
            from datetime import date
            compare(date.today(), d(2001, 1, 1))
            compare(sample1.str_today_1(), '2001-01-02')

        with ShouldRaise(AssertionError) as s:
            test_something()
        # This convoluted check is because we can't stub
        # out the date, since we're testing stubbing out
        # the date ;-)
        assert s.raised is not None
        j, dt1, j, dt2, j = s.raised.args[0].split("'")
        # check we can parse the date
        strptime(dt1, '%Y-%m-%d')
        # check the dt2 bit was as it should be
        compare(dt2, '2001-01-02')

        # What you need to do is replace the imported type:
        @replace('testfixtures.tests.sample1.date', mock_date())
        def test_something_fixed() -> None:
            compare(sample1.str_today_1(), '2001-01-01')

        test_something_fixed()

    def test_gotcha_import_and_obtain(self) -> None:
        # Another gotcha is where people have locally obtained
        # a class attributes, where the normal patching doesn't
        # work:

        @replace('testfixtures.tests.sample1.date', mock_date())
        def test_something() -> None:
            compare(sample1.str_today_2(), '2001-01-01')

        with ShouldRaise(AssertionError) as s:
            test_something()
        # This convoluted check is because we can't stub
        # out the date, since we're testing stubbing out
        # the date ;-)
        assert s.raised is not None
        j, dt1, j, dt2, j = s.raised.args[0].split("'")
        # check we can parse the date
        dt1 = strptime(dt1, '%Y-%m-%d')
        # check the dt2 bit was as it should be
        compare(dt2, '2001-01-01')

        # What you need to do is replace the imported name:
        @replace('testfixtures.tests.sample1.today', mock_date().today)
        def test_something_fixed() -> None:
            compare(sample1.str_today_2(), '2001-01-01')

        test_something_fixed()

    # if you have an embedded `today` as above, *and* you need to supply
    # a list of required dates, then it's often simplest just to
    # do a manual try-finally with a replacer:
    def test_import_and_obtain_with_lists(self) -> None:

        t = mock_date(None)
        t.add(2002, 1, 1)
        t.add(2002, 1, 2)

        from testfixtures import Replacer
        r = Replacer()
        r.replace('testfixtures.tests.sample1.today', t.today)
        try:
            compare(sample1.str_today_2(), '2002-01-01')
            compare(sample1.str_today_2(), '2002-01-02')
        finally:
            r.restore()

    @replace('datetime.date', mock_date())
    def test_repr(self) -> None:
        from datetime import date
        compare(repr(date), "<class 'testfixtures.datetime.MockDate'>")

    @replace('datetime.date', mock_date(delta=2))
    def test_delta(self) -> None:
        from datetime import date
        compare(date.today(), d(2001, 1, 1))
        compare(date.today(), d(2001, 1, 3))
        compare(date.today(), d(2001, 1, 5))

    @replace('datetime.date', mock_date(delta_type='weeks'))
    def test_delta_type(self) -> None:
        from datetime import date
        compare(date.today(), d(2001, 1, 1))
        compare(date.today(), d(2001, 1, 8))
        compare(date.today(), d(2001, 1, 22))

    @replace('datetime.date', mock_date(None))
    def test_set(self) -> None:
        from datetime import date
        date_mock = cast(type[MockDate], date)
        date_mock.set(2001, 1, 2)
        compare(date.today(), d(2001, 1, 2))
        date_mock.set(2002, 1, 1)
        compare(date.today(), d(2002, 1, 1))
        compare(date.today(), d(2002, 1, 3))

    @replace('datetime.date', mock_date(None))
    def test_set_date_supplied(self) -> None:
        from datetime import date
        date_mock = cast(type[MockDate], date)
        date_mock.set(d(2001, 1, 2))
        compare(date.today(), d(2001, 1, 2))
        date_mock.set(date(2001, 1, 3))
        compare(date.today(), d(2001, 1, 3))

    @replace('datetime.date', mock_date(None))
    def test_set_kw(self) -> None:
        from datetime import date
        date_mock = cast(type[MockDate], date)
        date_mock.set(year=2001, month=1, day=2)
        compare(date.today(), d(2001, 1, 2))

    @replace('datetime.date', mock_date(None))
    def test_add_kw(self, t: type[MockDate]) -> None:
        t.add(year=2002, month=1, day=1)
        from datetime import date
        compare(date.today(), d(2002, 1, 1))

    @replace('datetime.date', mock_date(strict=True))
    def test_isinstance_strict_true(self) -> None:
        from datetime import date
        date_mock = cast(type[MockDate], date)
        to_check = []
        to_check.append(date_mock(1999, 1, 1))
        to_check.append(date_mock.today())
        date_mock.set(2001, 1, 2)
        to_check.append(date_mock.today())
        date_mock.add(2001, 1, 3)
        to_check.append(date_mock.today())
        to_check.append(date_mock.today())
        date_mock.set(date_mock(2001, 1, 4))
        to_check.append(date_mock.today())
        date_mock.add(date_mock(2001, 1, 5))
        to_check.append(date_mock.today())
        to_check.append(date_mock.today())
        date_mock.set(d(2001, 1, 4))
        to_check.append(date_mock.today())
        date_mock.add(d(2001, 1, 5))
        to_check.append(date_mock.today())
        to_check.append(date_mock.today())

        for inst in to_check:
            self.assertTrue(isinstance(inst, date_mock), inst)
            self.assertTrue(inst.__class__ is date_mock, inst)
            self.assertTrue(isinstance(inst, d), inst)
            self.assertFalse(inst.__class__ is d, inst)

    def test_strict_addition(self) -> None:
        mock_d = mock_date(strict=True)
        dt = mock_d(2001, 1, 1) + timedelta(days=1)
        assert type(dt) is mock_d

    def test_non_strict_addition(self) -> None:
        from datetime import date
        mock_d = mock_date(strict=False)
        dt = mock_d(2001, 1, 1) + timedelta(days=1)
        assert type(dt) is date

    def test_strict_add(self) -> None:
        mock_d = mock_date(None, strict=True)
        mock_d.add(2001, 1, 1)
        assert type(mock_d.today()) is mock_d

    def test_non_strict_add(self) -> None:
        from datetime import date
        mock_d = mock_date(None, strict=False)
        mock_d.add(2001, 1, 1)
        assert type(mock_d.today()) is date

    @replace('datetime.date', mock_date())
    def test_isinstance_default(self) -> None:
        from datetime import date
        date_mock = cast(type[MockDate], date)
        to_check = []
        to_check.append(date_mock(1999, 1, 1))
        to_check.append(date_mock.today())
        date_mock.set(2001, 1, 2)
        to_check.append(date_mock.today())
        date_mock.add(2001, 1, 3)
        to_check.append(date_mock.today())
        to_check.append(date_mock.today())
        date_mock.set(date_mock(2001, 1, 4))
        to_check.append(date_mock.today())
        date_mock.add(date_mock(2001, 1, 5))
        to_check.append(date_mock.today())
        to_check.append(date_mock.today())
        date_mock.set(d(2001, 1, 4))
        to_check.append(date_mock.today())
        date_mock.add(d(2001, 1, 5))
        to_check.append(date_mock.today())
        to_check.append(date_mock.today())

        for inst in to_check:
            self.assertFalse(isinstance(inst, date_mock), inst)
            self.assertFalse(inst.__class__ is date_mock, inst)
            self.assertTrue(isinstance(inst, d), inst)
            self.assertTrue(inst.__class__ is d, inst)

    def test_tick_when_static(self) -> None:
        date = mock_date(delta=0)
        compare(date.today(), expected=d(2001, 1, 1))
        date.tick(days=1)
        compare(date.today(), expected=d(2001, 1, 2))

    def test_tick_when_dynamic(self) -> None:
        # hopefully not that common?
        date = mock_date()
        compare(date.today(), expected=d(2001, 1, 1))
        date.tick(days=1)
        compare(date.today(), expected=d(2001, 1, 3))

    def test_tick_with_timedelta_instance(self) -> None:
        date = mock_date(delta=0)
        compare(date.today(), expected=d(2001, 1, 1))
        date.tick(timedelta(days=1))
        compare(date.today(), expected=d(2001, 1, 2))

    def test_old_import(self) -> None:
        from testfixtures import test_date
        assert test_date is mock_date

    def test_add_timedelta_not_strict(self) -> None:
        mock_class = mock_date()
        value = mock_class.today() + timedelta(days=1)
        assert isinstance(value, date)
        assert type(value) is date

    def test_add_timedelta_strict(self) -> None:
        mock_class = mock_date(strict=True)
        value = mock_class.today() + timedelta(days=1)
        assert isinstance(value, date)
        assert type(value) is mock_class
