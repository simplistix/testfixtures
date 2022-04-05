from calendar import timegm
from datetime import datetime, timedelta, date, tzinfo as TZInfo
from typing import Optional, Callable, Type


class Queue(list):

    def __init__(self, delta: Optional[int], delta_delta: int, delta_type: str):
        super().__init__()
        if delta is None:
            self.delta = 0
            self.delta_delta = delta_delta
        else:
            self.delta = delta
            self.delta_delta = 0
        self.delta_type = delta_type

    def advance_next(self, delta: timedelta):
        self[-1] += delta

    def next(self):
        instance = self.pop(0)
        if not self:
            self.delta += self.delta_delta
            n = instance + timedelta(**{self.delta_type: self.delta})
            self.append(n)
        return instance


class MockedCurrent:

    _mock_queue: Queue
    _mock_base_class: Type
    _mock_class: Type
    _mock_tzinfo: Optional[TZInfo]
    _mock_date_type: Type[date]
    _correct_mock_type: Callable = None

    def __init_subclass__(
            cls, concrete=False, queue=None, strict=None, tzinfo=None, date_type=None
    ):
        if concrete:
            cls._mock_queue = queue
            cls._mock_base_class = cls.__bases__[0].__bases__[1]
            cls._mock_class = cls if strict else cls._mock_base_class
            cls._mock_tzinfo = tzinfo
            cls._mock_date_type = date_type

    @classmethod
    def add(cls, *args, **kw):
        if 'tzinfo' in kw or len(args) > 7:
            raise TypeError('Cannot add using tzinfo on %s' % cls.__name__)
        if args and isinstance(args[0], cls._mock_base_class):
            instance = args[0]
            instance_tzinfo = getattr(instance, 'tzinfo', None)
            if instance_tzinfo:
                if instance_tzinfo != cls._mock_tzinfo:
                    raise ValueError(
                        'Cannot add %s with tzinfo of %s as configured to use %s' % (
                            instance.__class__.__name__, instance_tzinfo, cls._mock_tzinfo
                        ))
                instance = instance.replace(tzinfo=None)
            if cls._correct_mock_type:
                instance = cls._correct_mock_type(instance)
        else:
            instance = cls(*args, **kw)
        cls._mock_queue.append(instance)

    @classmethod
    def set(cls, *args, **kw):
        cls._mock_queue.clear()
        cls.add(*args, **kw)

    @classmethod
    def tick(cls, *args, **kw):
        if kw:
            delta = timedelta(**kw)
        else:
            delta, = args
        cls._mock_queue.advance_next(delta)

    def __add__(self, other):
        instance = super().__add__(other)
        if self._correct_mock_type:
            instance = self._correct_mock_type(instance)
        return instance

    def __new__(cls, *args, **kw):
        if cls is cls._mock_class:
            return super().__new__(cls, *args, **kw)
        else:
            return cls._mock_class(*args, **kw)


def mock_factory(
        type_name, mock_class, default, args, kw,
        delta, delta_type, delta_delta=1,
        date_type=None, tzinfo=None, strict=False
):
    cls = type(
        type_name,
        (mock_class,),
        {},
        concrete=True,
        queue=Queue(delta, delta_delta, delta_type),
        strict=strict,
        tzinfo=tzinfo,
        date_type=date_type,
    )

    if args != (None,):
        if not (args or kw):
            args = default
        cls.add(*args, **kw)

    return cls


class MockDateTime(MockedCurrent, datetime):

    @classmethod
    def _correct_mock_type(cls, instance):
        return cls._mock_class(
            instance.year,
            instance.month,
            instance.day,
            instance.hour,
            instance.minute,
            instance.second,
            instance.microsecond,
            instance.tzinfo,
        )

    @classmethod
    def now(cls, tz=None):
        instance = cls._mock_queue.next()
        if tz is not None:
            if cls._mock_tzinfo:
                instance = instance - cls._mock_tzinfo.utcoffset(instance)
            instance = tz.fromutc(instance.replace(tzinfo=tz))
        return cls._correct_mock_type(instance)

    @classmethod
    def utcnow(cls):
        instance = cls._mock_queue.next()
        if cls._mock_tzinfo is not None:
            instance = instance - cls._mock_tzinfo.utcoffset(instance)
        return instance

    def date(self):
        return self._mock_date_type(
            self.year,
            self.month,
            self.day
            )


def test_datetime(
        *args,
        tzinfo=None,
        delta=None,
        delta_type='seconds',
        date_type=date,
        strict=False,
        **kw
):
    if len(args) > 7:
        tzinfo = args[7]
        args = args[:7]
    else:
        tzinfo = tzinfo or (getattr(args[0], 'tzinfo', None) if args else None)
    return mock_factory(
        'tdatetime', MockDateTime, (2001, 1, 1, 0, 0, 0), args, kw,
        tzinfo=tzinfo,
        delta=delta,
        delta_delta=10,
        delta_type=delta_type,
        date_type=date_type,
        strict=strict,
        )


test_datetime.__test__ = False


class MockDate(MockedCurrent, date):

    @classmethod
    def _correct_mock_type(cls, instance):
        return cls._mock_class(
            instance.year,
            instance.month,
            instance.day,
        )

    @classmethod
    def today(cls):
        return cls._mock_queue.next()


def test_date(*args, delta=None, delta_type='days', strict=False, **kw):
    return mock_factory(
        'tdate', MockDate, (2001, 1, 1), args, kw,
        delta=delta,
        delta_type=delta_type,
        strict=strict,
        )


test_date.__test__ = False


ms = 10**6


class MockTime(MockedCurrent, datetime):

    def __new__(cls, *args, **kw):
        if args or kw:
            # Used when adding stuff to the queue
            return super().__new__(cls, *args, **kw)
        else:
            instance = cls._mock_queue.next()
            time = timegm(instance.utctimetuple())
            time += (float(instance.microsecond)/ms)
            return time


def test_time(*args, delta=None, delta_type='seconds', **kw):
    if 'tzinfo' in kw or len(args) > 7 or (args and getattr(args[0], 'tzinfo', None)):
        raise TypeError("You don't want to use tzinfo with test_time")
    return mock_factory(
        'ttime', MockTime, (2001, 1, 1, 0, 0, 0), args, kw,
        delta=delta,
        delta_type=delta_type,
        )


test_time.__test__ = False
