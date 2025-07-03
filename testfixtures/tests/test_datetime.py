from datetime import date, datetime
from datetime import datetime as d
from datetime import timedelta
from datetime import tzinfo
from typing import cast

from testfixtures import (
    Replacer,
    ShouldRaise,
    compare,
    mock_datetime,
    mock_date,
    replace,
)
from testfixtures.datetime import MockDateTime
from testfixtures.tests import sample1
from unittest import TestCase


class SampleTZInfo(tzinfo):

    def tzname(self, dt: datetime | None) -> str:
        return "SAMPLE"

    def utcoffset(self, dt: datetime | None) -> timedelta | None:
        return timedelta(minutes=3) + self.dst(dt)

    def dst(self, dt: datetime | None) -> timedelta:
        return timedelta(minutes=1)


class SampleTZInfo2(tzinfo):

    def tzname(self, dt: datetime | None) -> str:
        return "SAMPLE2"

    def utcoffset(self, dt: datetime | None) -> timedelta | None:
        return timedelta(minutes=5)

    def dst(self, dt: datetime | None) -> timedelta:
        return timedelta(minutes=0)


class WeirdTZInfo(tzinfo):

    def tzname(self, dt: datetime | None) -> str:
        return "WEIRD"

    def utcoffset(self, dt: datetime | None) -> timedelta | None:
        return None

    def dst(self, dt: datetime | None) -> timedelta | None:
        return None


def test_sample_tzinfos() -> None:
    compare(SampleTZInfo().tzname(None), expected='SAMPLE')
    compare(SampleTZInfo2().tzname(None), expected='SAMPLE2')
    compare(WeirdTZInfo().tzname(None), expected='WEIRD')
    compare(WeirdTZInfo().utcoffset(datetime(1, 2, 3)), expected=None)
    compare(WeirdTZInfo().dst(datetime(1, 2, 3)), expected=None)


class TestDateTime(TestCase):

    @replace('datetime.datetime', mock_datetime())
    def test_now(self) -> None:
        from datetime import datetime
        compare(datetime.now(), d(2001, 1, 1, 0, 0, 0))
        compare(datetime.now(), d(2001, 1, 1, 0, 0, 10))
        compare(datetime.now(), d(2001, 1, 1, 0, 0, 30))

    @replace('datetime.datetime', mock_datetime())
    def test_now_with_tz_supplied(self) -> None:
        from datetime import datetime
        info = SampleTZInfo()
        compare(datetime.now(info), d(2001, 1, 1, 0, 4, tzinfo=SampleTZInfo()))

    @replace('datetime.datetime', mock_datetime(tzinfo=SampleTZInfo()))
    def test_now_with_tz_setup(self) -> None:
        from datetime import datetime
        compare(datetime.now(), d(2001, 1, 1))

    @replace('datetime.datetime', mock_datetime(tzinfo=WeirdTZInfo()))
    def test_now_with_werid_tz_setup(self) -> None:
        from datetime import datetime
        with ShouldRaise(TypeError('tzinfo with .utcoffset() returning None is not supported')):
            datetime.now(tz=SampleTZInfo())

    @replace('datetime.datetime', mock_datetime(tzinfo=SampleTZInfo()))
    def test_now_with_tz_setup_and_supplied(self) -> None:
        from datetime import datetime
        info = SampleTZInfo2()
        compare(datetime.now(info), d(2001, 1, 1, 0, 1, tzinfo=info))

    @replace('datetime.datetime', mock_datetime(tzinfo=SampleTZInfo()))
    def test_now_with_tz_setup_and_same_supplied(self) -> None:
        from datetime import datetime
        info = SampleTZInfo()
        compare(datetime.now(info), d(2001, 1, 1, tzinfo=info))

    def test_now_with_tz_instance(self) -> None:
        dt = mock_datetime(d(2001, 1, 1, tzinfo=SampleTZInfo()))
        compare(dt.now(), d(2001, 1, 1))

    def test_now_with_tz_instance_and_supplied(self) -> None:
        dt = mock_datetime(d(2001, 1, 1, tzinfo=SampleTZInfo()))
        info = SampleTZInfo2()
        compare(dt.now(info), d(2001, 1, 1, 0, 1, tzinfo=info))

    def test_now_with_tz_instance_and_same_supplied(self) -> None:
        dt = mock_datetime(d(2001, 1, 1, tzinfo=SampleTZInfo()))
        info = SampleTZInfo()
        compare(dt.now(info), d(2001, 1, 1, tzinfo=info))

    @replace('datetime.datetime', mock_datetime(2002, 1, 1, 1, 2, 3))
    def test_now_supplied(self) -> None:
        from datetime import datetime
        compare(datetime.now(), d(2002, 1, 1, 1, 2, 3))

    @replace('datetime.datetime', mock_datetime(None))
    def test_now_sequence(self, t: type[MockDateTime]) -> None:
        t.add(2002, 1, 1, 1, 0, 0)
        t.add(2002, 1, 1, 2, 0, 0)
        t.add(2002, 1, 1, 3, 0, 0)
        from datetime import datetime
        compare(datetime.now(), d(2002, 1, 1, 1, 0, 0))
        compare(datetime.now(), d(2002, 1, 1, 2, 0, 0))
        compare(datetime.now(), d(2002, 1, 1, 3, 0, 0))

    @replace('datetime.datetime', mock_datetime())
    def test_add_and_set(self, t: type[MockDateTime]) -> None:
        t.add(2002, 1, 1, 1, 0, 0)
        t.add(2002, 1, 1, 2, 0, 0)
        t.set(2002, 1, 1, 3, 0, 0)
        from datetime import datetime
        compare(datetime.now(), d(2002, 1, 1, 3, 0, 0))
        compare(datetime.now(), d(2002, 1, 1, 3, 0, 10))
        compare(datetime.now(), d(2002, 1, 1, 3, 0, 30))

    @replace('datetime.datetime', mock_datetime(None))
    def test_add_datetime_supplied(self, t: type[MockDateTime]) -> None:
        from datetime import datetime
        t.add(d(2002, 1, 1, 1))
        t.add(datetime(2002, 1, 1, 2))
        compare(datetime.now(), d(2002, 1, 1, 1, 0, 0))
        compare(datetime.now(), d(2002, 1, 1, 2, 0, 0))
        tzinfo = SampleTZInfo()
        tzrepr = repr(tzinfo)
        with ShouldRaise(ValueError(
            'Cannot add datetime with tzinfo of %s as configured to use None' %(
                tzrepr
            ))):
            t.add(d(2001, 1, 1, tzinfo=tzinfo))

    def test_instantiate_with_datetime(self) -> None:
        from datetime import datetime
        t = mock_datetime(datetime(2002, 1, 1, 1))
        compare(t.now(), d(2002, 1, 1, 1, 0, 0))

    @replace('datetime.datetime', mock_datetime(None))
    def test_now_requested_longer_than_supplied(self, t: type[MockDateTime]) -> None:
        t.add(2002, 1, 1, 1, 0, 0)
        t.add(2002, 1, 1, 2, 0, 0)
        from datetime import datetime
        compare(datetime.now(), d(2002, 1, 1, 1, 0, 0))
        compare(datetime.now(), d(2002, 1, 1, 2, 0, 0))
        compare(datetime.now(), d(2002, 1, 1, 2, 0, 10))
        compare(datetime.now(), d(2002, 1, 1, 2, 0, 30))

    @replace('datetime.datetime', mock_datetime(strict=True))
    def test_call(self, t: type[MockDateTime]) -> None:
        compare(t(2002, 1, 2, 3, 4, 5), d(2002, 1, 2, 3, 4, 5))
        from datetime import datetime
        dt = datetime(2001, 1, 1, 1, 0, 0)
        self.assertFalse(dt.__class__ is d)
        compare(dt, d(2001, 1, 1, 1, 0, 0))

    def test_date_return_type(self) -> None:
        with Replacer() as r:
            r.replace('datetime.datetime', mock_datetime())
            from datetime import datetime
            dt = datetime(2001, 1, 1, 1, 0, 0)
            d = dt.date()
            compare(d, date(2001, 1, 1))
            self.assertTrue(d.__class__ is date)

    def test_date_return_type_picky(self) -> None:
        # type checking is a bitch :-/
        date_type = mock_date(strict=True)
        with Replacer() as r:
            r.replace('datetime.datetime', mock_datetime(date_type=date_type,
                                                         strict=True,
                                                         ))
            from datetime import datetime
            dt = datetime(2010, 8, 26, 14, 33, 13)
            d = dt.date()
            compare(d, date_type(2010, 8, 26))
            self.assertTrue(d.__class__ is date_type)

    # if you have an embedded `now` as above, *and* you need to supply
    # a list of required datetimes, then it's often simplest just to
    # do a manual try-finally with a replacer:
    def test_import_and_obtain_with_lists(self) -> None:

        t = mock_datetime(None)
        t.add(2002, 1, 1, 1, 0, 0)
        t.add(2002, 1, 1, 2, 0, 0)

        from testfixtures import Replacer
        r = Replacer()
        r.replace('testfixtures.tests.sample1.now', t.now)
        try:
            compare(sample1.str_now_2(), '2002-01-01 01:00:00')
            compare(sample1.str_now_2(), '2002-01-01 02:00:00')
        finally:
            r.restore()

    @replace('datetime.datetime', mock_datetime())
    def test_repr(self) -> None:
        from datetime import datetime
        compare(repr(datetime), "<class 'testfixtures.datetime.MockDateTime'>")

    @replace('datetime.datetime', mock_datetime(delta=1))
    def test_delta(self) -> None:
        from datetime import datetime
        compare(datetime.now(), d(2001, 1, 1, 0, 0, 0))
        compare(datetime.now(), d(2001, 1, 1, 0, 0, 1))
        compare(datetime.now(), d(2001, 1, 1, 0, 0, 2))

    @replace('datetime.datetime', mock_datetime(delta_type='minutes'))
    def test_delta_type(self) -> None:
        from datetime import datetime
        compare(datetime.now(), d(2001, 1, 1, 0, 0, 0))
        compare(datetime.now(), d(2001, 1, 1, 0, 10, 0))
        compare(datetime.now(), d(2001, 1, 1, 0, 30, 0))

    @replace('datetime.datetime', mock_datetime(None))
    def test_set(self) -> None:
        from datetime import datetime
        dt_mock = cast(type[MockDateTime], datetime)
        dt_mock.set(2001, 1, 1, 1, 0, 1)
        compare(datetime.now(), d(2001, 1, 1, 1, 0, 1))
        dt_mock.set(2002, 1, 1, 1, 0, 0)
        compare(datetime.now(), d(2002, 1, 1, 1, 0, 0))
        compare(datetime.now(), d(2002, 1, 1, 1, 0, 20))

    @replace('datetime.datetime', mock_datetime(None))
    def test_set_datetime_supplied(self, t: type[MockDateTime]) -> None:
        from datetime import datetime
        t.set(d(2002, 1, 1, 1))
        compare(datetime.now(), d(2002, 1, 1, 1, 0, 0))
        t.set(datetime(2002, 1, 1, 2))
        compare(datetime.now(), d(2002, 1, 1, 2, 0, 0))
        tzinfo = SampleTZInfo()
        tzrepr = repr(tzinfo)
        with ShouldRaise(ValueError(
            'Cannot add datetime with tzinfo of %s as configured to use None' %(
                tzrepr
            ))):
            t.set(d(2001, 1, 1, tzinfo=tzinfo))

    @replace('datetime.datetime', mock_datetime(None, tzinfo=SampleTZInfo()))
    def test_set_tz_setup(self) -> None:
        from datetime import datetime
        dt_mock = cast(type[MockDateTime], datetime)
        dt_mock.set(year=2002, month=1, day=1)
        compare(datetime.now(), d(2002, 1, 1))

    @replace('datetime.datetime', mock_datetime(None))
    def test_set_kw(self) -> None:
        from datetime import datetime
        dt_mock = cast(type[MockDateTime], datetime)
        dt_mock.set(year=2002, month=1, day=1)
        compare(datetime.now(), d(2002, 1, 1))

    @replace('datetime.datetime', mock_datetime(None))
    def test_set_tzinfo_kw(self) -> None:
        from datetime import datetime
        dt_mock = cast(type[MockDateTime], datetime)
        with ShouldRaise(TypeError('Cannot add using tzinfo on MockDateTime')):
            dt_mock.set(year=2002, month=1, day=1, tzinfo=SampleTZInfo())

    @replace('datetime.datetime', mock_datetime(None))
    def test_set_tzinfo_args(self) -> None:
        from datetime import datetime
        dt_mock = cast(type[MockDateTime], datetime)
        with ShouldRaise(TypeError('Cannot add using tzinfo on MockDateTime')):
            dt_mock.set(2002, 1, 2, 3, 4, 5, 6, SampleTZInfo())  # type: ignore[arg-type]

    @replace('datetime.datetime', mock_datetime(None))
    def test_add_kw(self, t: type[MockDateTime]) -> None:
        from datetime import datetime
        t.add(year=2002, day=1, month=1)
        compare(datetime.now(), d(2002, 1, 1))

    @replace('datetime.datetime', mock_datetime(None))
    def test_add_tzinfo_kw(self, t: type[MockDateTime]) -> None:
        with ShouldRaise(TypeError('Cannot add using tzinfo on MockDateTime')):
            t.add(year=2002, month=1, day=1, tzinfo=SampleTZInfo())

    @replace('datetime.datetime', mock_datetime(None))
    def test_add_tzinfo_args(self, t: type[MockDateTime]) -> None:
        with ShouldRaise(TypeError('Cannot add using tzinfo on MockDateTime')):
            t.add(2002, 1, 2, 3, 4, 5, 6, SampleTZInfo())  # type: ignore[arg-type]

    @replace('datetime.datetime',
             mock_datetime(2001, 1, 2, 3, 4, 5, 6, SampleTZInfo()))
    def test_max_number_args(self) -> None:
        from datetime import datetime
        compare(datetime.now(), d(2001, 1, 2, 3, 4, 5, 6))

    @replace('datetime.datetime', mock_datetime(2001, 1, 2))
    def test_min_number_args(self) -> None:
        from datetime import datetime
        compare(datetime.now(), d(2001, 1, 2))

    @replace('datetime.datetime', mock_datetime(
        year=2001,
        month=1,
        day=2,
        hour=3,
        minute=4,
        second=5,
        microsecond=6,
        tzinfo=SampleTZInfo()
        ))
    def test_all_kw(self) -> None:
        from datetime import datetime
        compare(datetime.now(), d(2001, 1, 2, 3, 4, 5, 6))

    @replace('datetime.datetime', mock_datetime(2001, 1, 2))
    def test_utc_now(self) -> None:
        from datetime import datetime
        compare(datetime.utcnow(), d(2001, 1, 2))

    @replace('datetime.datetime',
             mock_datetime(2001, 1, 2, tzinfo=SampleTZInfo()))
    def test_utc_now_with_tz(self) -> None:
        from datetime import datetime
        compare(datetime.utcnow(), d(2001, 1, 1, 23, 56))

    @replace('datetime.datetime', mock_datetime(strict=True))
    def test_isinstance_strict(self) -> None:
        from datetime import datetime
        dt_mock = cast(type[MockDateTime], datetime)
        to_check = []
        to_check.append(dt_mock(1999, 1, 1))
        to_check.append(dt_mock.now())
        to_check.append(dt_mock.now(SampleTZInfo()))
        to_check.append(dt_mock.utcnow())
        dt_mock.set(2001, 1, 1, 20)
        to_check.append(dt_mock.now())
        dt_mock.add(2001, 1, 1, 21)
        to_check.append(dt_mock.now())
        to_check.append(dt_mock.now())
        dt_mock.set(dt_mock(2001, 1, 1, 22))
        to_check.append(dt_mock.now())
        to_check.append(dt_mock.now(SampleTZInfo()))
        dt_mock.add(dt_mock(2001, 1, 1, 23))
        to_check.append(dt_mock.now())
        to_check.append(dt_mock.now())
        to_check.append(dt_mock.now(SampleTZInfo()))
        dt_mock.set(d(2001, 1, 1, 22))
        to_check.append(dt_mock.now())
        dt_mock.add(d(2001, 1, 1, 23))
        to_check.append(dt_mock.now())
        to_check.append(dt_mock.now())
        to_check.append(dt_mock.now(SampleTZInfo()))

        for inst in to_check:
            self.assertTrue(isinstance(inst, dt_mock), inst)
            self.assertTrue(inst.__class__ is dt_mock, inst)
            self.assertTrue(isinstance(inst, d), inst)
            self.assertFalse(inst.__class__ is d, inst)

    def test_strict_addition(self) -> None:
        mock_dt = mock_datetime(strict=True)
        dt = mock_dt(2001, 1, 1) + timedelta(days=1)
        assert type(dt) is mock_dt

    def test_non_strict_addition(self) -> None:
        from datetime import datetime
        mock_dt = mock_datetime(strict=False)
        dt = mock_dt(2001, 1, 1) + timedelta(days=1)
        assert type(dt) is datetime

    def test_strict_add(self) -> None:
        mock_dt = mock_datetime(None, strict=True)
        mock_dt.add(2001, 1, 1)
        assert type(mock_dt.now()) is mock_dt

    def test_non_strict_add(self) -> None:
        from datetime import datetime
        mock_dt = mock_datetime(None, strict=False)
        mock_dt.add(2001, 1, 1)
        assert type(mock_dt.now()) is datetime

    @replace('datetime.datetime', mock_datetime())
    def test_isinstance_default(self) -> None:
        from datetime import datetime
        dt_mock = cast(type[MockDateTime], datetime)
        to_check = []
        to_check.append(dt_mock(1999, 1, 1))
        to_check.append(dt_mock.now())
        to_check.append(dt_mock.now(SampleTZInfo()))
        to_check.append(dt_mock.utcnow())
        dt_mock.set(2001, 1, 1, 20)
        to_check.append(dt_mock.now())
        dt_mock.add(2001, 1, 1, 21)
        to_check.append(dt_mock.now())
        to_check.append(dt_mock.now(SampleTZInfo()))
        dt_mock.set(dt_mock(2001, 1, 1, 22))
        to_check.append(dt_mock.now())
        dt_mock.add(dt_mock(2001, 1, 1, 23))
        to_check.append(dt_mock.now())
        to_check.append(dt_mock.now())
        to_check.append(dt_mock.now(SampleTZInfo()))
        dt_mock.set(d(2001, 1, 1, 22))
        to_check.append(dt_mock.now())
        dt_mock.add(d(2001, 1, 1, 23))
        to_check.append(dt_mock.now())
        to_check.append(dt_mock.now())
        to_check.append(dt_mock.now(SampleTZInfo()))

        for inst in to_check:
            self.assertFalse(isinstance(inst, dt_mock), inst)
            self.assertFalse(inst.__class__ is dt_mock, inst)
            self.assertTrue(isinstance(inst, d), inst)
            self.assertTrue(inst.__class__ is d, inst)

    def test_subsecond_deltas(self) -> None:
        mock_dt = mock_datetime(delta=0.5)
        compare(mock_dt.now(), d(2001, 1, 1, 0, 0, 0, 0))
        compare(mock_dt.now(), d(2001, 1, 1, 0, 0, 0, 500000))
        compare(mock_dt.now(), d(2001, 1, 1, 0, 0, 1, 0))

    def test_ms_delta(self) -> None:
        mock_dt = mock_datetime(delta=100, delta_type='microseconds')
        compare(mock_dt.now(), d(2001, 1, 1, 0, 0, 0, 0))
        compare(mock_dt.now(), d(2001, 1, 1, 0, 0, 0, 100))
        compare(mock_dt.now(), d(2001, 1, 1, 0, 0, 0, 200))

    def test_tick_when_static(self) -> None:
        mock_dt = mock_datetime(delta=0)
        compare(mock_dt.now(), expected=d(2001, 1, 1))
        mock_dt.tick(hours=1)
        compare(mock_dt.now(), expected=d(2001, 1, 1, 1))

    def test_tick_when_dynamic(self) -> None:
        # hopefully not that common?
        mock_dt = mock_datetime()
        compare(mock_dt.now(), expected=d(2001, 1, 1))
        mock_dt.tick(hours=1)
        compare(mock_dt.now(), expected=d(2001, 1, 1, 1, 0, 10))

    def test_tick_with_timedelta_instance(self) -> None:
        mock_dt = mock_datetime(delta=0)
        compare(mock_dt.now(), expected=d(2001, 1, 1))
        mock_dt.tick(timedelta(hours=1))
        compare(mock_dt.now(), expected=d(2001, 1, 1, 1))

    def test_old_import(self) -> None:
        from testfixtures import test_datetime
        assert test_datetime is mock_datetime

    def test_add_timedelta_not_strict(self) -> None:
        mock_class = mock_datetime()
        value = mock_class.now() + timedelta(seconds=10)
        assert isinstance(value, datetime)
        assert type(value) is datetime

    def test_add_timedelta_strict(self) -> None:
        mock_class = mock_datetime(strict=True)
        value = mock_class.now() + timedelta(seconds=10)
        assert isinstance(value, datetime)
        assert type(value) is mock_class
