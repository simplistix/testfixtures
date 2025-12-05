from datetime import timedelta
from unittest import TestCase

from testfixtures import mock_time, replace, compare, ShouldRaise
from testfixtures.datetime import MockTime
from .test_datetime import SampleTZInfo


class TestTime(TestCase):

    @replace('time.time', mock_time())
    def test_time_call(self) -> None:
        from time import time
        compare(time(), 978307200.0)
        compare(time(), 978307201.0)
        compare(time(), 978307203.0)

    @replace('time.time', mock_time(2002, 1, 1, 1, 2, 3))
    def test_time_supplied(self) -> None:
        from time import time
        compare(time(), 1009846923.0)

    @replace('time.time', mock_time(None))
    def test_time_sequence(self, t: MockTime) -> None:
        t.add(2002, 1, 1, 1, 0, 0)
        t.add(2002, 1, 1, 2, 0, 0)
        t.add(2002, 1, 1, 3, 0, 0)
        from time import time
        compare(time(), 1009846800.0)
        compare(time(), 1009850400.0)
        compare(time(), 1009854000.0)

    @replace('time.time', mock_time(None))
    def test_add_datetime_supplied(self, t: MockTime) -> None:
        from datetime import datetime
        from time import time
        t.add(datetime(2002, 1, 1, 2))
        compare(time(), 1009850400.0)
        tzinfo = SampleTZInfo()
        tzrepr = repr(tzinfo)
        with ShouldRaise(ValueError(
            'Cannot add datetime with tzinfo of %s as configured to use None' %(
                tzrepr
            ))):
            t.add(datetime(2001, 1, 1, tzinfo=tzinfo))

    def test_instantiate_with_datetime(self) -> None:
        from datetime import datetime
        t = mock_time(datetime(2002, 1, 1, 2))
        compare(t(), 1009850400.0)

    @replace('time.time', mock_time(None))
    def test_now_requested_longer_than_supplied(self, t: MockTime) -> None:
        t.add(2002, 1, 1, 1, 0, 0)
        t.add(2002, 1, 1, 2, 0, 0)
        from time import time
        compare(time(), 1009846800.0)
        compare(time(), 1009850400.0)
        compare(time(), 1009850401.0)
        compare(time(), 1009850403.0)

    @replace('time.time', mock_time())
    def test_call(self, t: MockTime) -> None:
        compare(t(), 978307200.0)
        from time import time
        compare(time(), 978307201.0)

    @replace('time.time', mock_time())
    def test_repr_time(self) -> None:
        from time import time
        assert repr(time).startswith('<testfixtures.datetime.MockTime object at ')

    @replace('time.time', mock_time(delta=10))
    def test_delta(self) -> None:
        from time import time
        compare(time(), 978307200.0)
        compare(time(), 978307210.0)
        compare(time(), 978307220.0)

    @replace('time.time', mock_time(delta_type='minutes'))
    def test_delta_type(self) -> None:
        from time import time
        compare(time(), 978307200.0)
        compare(time(), 978307260.0)
        compare(time(), 978307380.0)

    @replace('time.time', mock_time(None))
    def test_set(self, time_mock: MockTime) -> None:
        from time import time
        time_mock.set(2001, 1, 1, 1, 0, 1)
        compare(time(), 978310801.0)
        time_mock.set(2002, 1, 1, 1, 0, 0)
        compare(time(), 1009846800.0)
        compare(time(), 1009846802.0)

    @replace('time.time', mock_time(None))
    def test_set_datetime_supplied(self, t: MockTime) -> None:
        from datetime import datetime
        from time import time
        t.set(datetime(2001, 1, 1, 1, 0, 1))
        compare(time(), 978310801.0)
        tzinfo = SampleTZInfo()
        tzrepr = repr(tzinfo)
        with ShouldRaise(ValueError(
            'Cannot add datetime with tzinfo of %s as configured to use None' %(
                tzrepr
            ))):
            t.set(datetime(2001, 1, 1, tzinfo=tzinfo))

    @replace('time.time', mock_time(None))
    def test_set_kw(self, time_mock: MockTime) -> None:
        from time import time
        time_mock.set(year=2001, month=1, day=1, hour=1, second=1)
        compare(time(), 978310801.0)

    @replace('time.time', mock_time(None))
    def test_set_kw_tzinfo(self, time_mock: MockTime) -> None:
        with ShouldRaise(TypeError('Cannot add using tzinfo on MockTime')):
            time_mock.set(year=2001, tzinfo=SampleTZInfo())

    @replace('time.time', mock_time(None))
    def test_set_args_tzinfo(self, time_mock: MockTime) -> None:
        with ShouldRaise(TypeError('Cannot add using tzinfo on MockTime')):
            time_mock.set(2002, 1, 2, 3, 4, 5, 6, SampleTZInfo())  # type: ignore[arg-type]

    @replace('time.time', mock_time(None))
    def test_add_kw(self, time_mock: MockTime) -> None:
        from time import time
        time_mock.add(year=2001, month=1, day=1, hour=1, second=1)
        compare(time(), 978310801.0)

    @replace('time.time', mock_time(None))
    def test_add_tzinfo_kw(self, time_mock: MockTime) -> None:
        with ShouldRaise(TypeError('Cannot add using tzinfo on MockTime')):
            time_mock.add(year=2001, tzinfo=SampleTZInfo())

    @replace('time.time', mock_time(None))
    def test_add_tzinfo_args(self, time_mock: MockTime) -> None:
        with ShouldRaise(TypeError('Cannot add using tzinfo on MockTime')):
            time_mock.add(2001, 1, 2, 3, 4, 5, 6, SampleTZInfo())  # type: ignore[arg-type]

    @replace('time.time', mock_time(2001, 1, 2, 3, 4, 5, 600000))
    def test_max_number_args(self) -> None:
        from time import time
        compare(time(), 978404645.6)

    def test_max_number_tzinfo(self) -> None:
        with ShouldRaise(TypeError(
            "You don't want to use tzinfo with test_time"
                )):
            mock_time(2001, 1, 2, 3, 4, 5, 6, SampleTZInfo())  # type: ignore[arg-type]

    @replace('time.time', mock_time(2001, 1, 2))
    def test_min_number_args(self) -> None:
        from time import time
        compare(time(), 978393600.0)

    @replace('time.time', mock_time(
        year=2001,
        month=1,
        day=2,
        hour=3,
        minute=4,
        second=5,
        microsecond=6,
        ))
    def test_all_kw(self) -> None:
        from time import time
        compare(time(), 978404645.000006)

    def test_kw_tzinfo(self) -> None:
        with ShouldRaise(TypeError(
            "You don't want to use tzinfo with test_time"
                )):
            mock_time(year=2001, tzinfo=SampleTZInfo())  # type: ignore[arg-type]

    def test_instance_tzinfo(self) -> None:
        from datetime import datetime
        with ShouldRaise(TypeError(
            "You don't want to use tzinfo with test_time"
                )):
            mock_time(datetime(2001, 1, 1, tzinfo=SampleTZInfo()))

    def test_subsecond_deltas(self) -> None:
        time = mock_time(delta=0.5)
        compare(time(), 978307200.0)
        compare(time(), 978307200.5)
        compare(time(), 978307201.0)

    def test_ms_deltas(self) -> None:
        time = mock_time(delta=1000, delta_type='microseconds')
        compare(time(), 978307200.0)
        compare(time(), 978307200.001)
        compare(time(), 978307200.002)

    def test_tick_when_static(self) -> None:
        time = mock_time(delta=0)
        compare(time(), expected=978307200.0)
        time.tick(seconds=1)
        compare(time(), expected=978307201.0)

    def test_tick_when_dynamic(self) -> None:
        # hopefully not that common?
        time = mock_time()
        compare(time(), expected=978307200.0)
        time.tick(seconds=1)
        compare(time(), expected=978307202.0)

    def test_tick_with_timedelta_instance(self) -> None:
        time = mock_time(delta=0)
        compare(time(), expected=978307200.0)
        time.tick(timedelta(seconds=1))
        compare(time(), expected=978307201.0)

    def test_old_import(self) -> None:
        from testfixtures import test_time
        assert test_time is mock_time

    def test_addition_to_no_params_call_indirect(self) -> None:
        mock = mock_time()
        # Calling the mock without any parameters definitely gives you a float:
        value = mock()
        assert isinstance(value, float)
        compare(value + 3600, expected=978307200.0 + 3600.0)

    def test_addition_to_no_params_call_direct(self) -> None:
        mock = mock_time()
        # ...but if if you do it in one step, mypy gets confused:
        compare(mock() + 3600, expected=978307200.0 + 3600.0)
