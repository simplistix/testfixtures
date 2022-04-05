from calendar import timegm
from datetime import datetime, timedelta, date, tzinfo
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
        r = self.pop(0)
        if not self:
            self.delta += self.delta_delta
            n = r + timedelta(**{self.delta_type: self.delta})
            self.append(n)
        return r


class MockedCurrent:

    _q: Queue
    _base_cls: Type
    _cls: Type
    _tzta: Optional[tzinfo]
    _date_type: Type[date]
    _ct: Callable = None

    def __init_subclass__(
            cls, concrete=False, strict=None, tz=None, queue=None, date_type=None
    ):
        if concrete:
            cls._q = queue
            cls._base_cls = cls.__bases__[0].__bases__[1]
            cls._cls = cls if strict else cls._base_cls
            cls._tzta = tz
            cls._date_type = date_type

    @classmethod
    def add(cls, *args, **kw):
        if 'tzinfo' in kw or len(args) > 7:
            raise TypeError('Cannot add using tzinfo on %s' % cls.__name__)
        if args and isinstance(args[0], cls._base_cls):
            inst = args[0]
            tzinfo = getattr(inst, 'tzinfo', None)
            if tzinfo:
                if tzinfo != cls._tzta:
                    raise ValueError(
                        'Cannot add %s with tzinfo of %s as configured to use %s' % (
                            inst.__class__.__name__, tzinfo, cls._tzta
                        ))
                inst = inst.replace(tzinfo=None)
            if cls._ct is not None:
                inst = cls._ct(inst)
        else:
            inst = cls(*args, **kw)
        cls._q.append(inst)

    @classmethod
    def set(cls, *args, **kw):
        cls._q.clear()
        cls.add(*args, **kw)

    @classmethod
    def tick(cls, *args, **kw):
        if kw:
            delta = timedelta(**kw)
        else:
            delta, = args
        cls._q.advance_next(delta)

    def __add__(self, other):
        r = super().__add__(other)
        if self._ct:
            r = self._ct(r)
        return r

    def __new__(cls, *args, **kw):
        if cls is cls._cls:
            return super().__new__(cls, *args, **kw)
        else:
            return cls._cls(*args, **kw)


def mock_factory(
        n, mock_class, default, args, kw,
        delta, delta_type, delta_delta=1,
        date_type=None, tz=None, strict=False
):
    cls = type(
        n,
        (mock_class,),
        {},
        concrete=True,
        queue=Queue(delta, delta_delta, delta_type),
        strict=strict,
        tz=tz,
        date_type=date_type,
    )

    if args != (None,):
        if not (args or kw):
            args = default
        cls.add(*args, **kw)

    return cls


class MockDateTime(MockedCurrent, datetime):

    @classmethod
    def _ct(cls, dt):
        return cls._cls(
            dt.year,
            dt.month,
            dt.day,
            dt.hour,
            dt.minute,
            dt.second,
            dt.microsecond,
            dt.tzinfo,
        )

    @classmethod
    def now(cls, tz=None):
        r = cls._q.next()
        if tz is not None:
            if cls._tzta:
                r = r - cls._tzta.utcoffset(r)
            r = tz.fromutc(r.replace(tzinfo=tz))
        return cls._ct(r)

    @classmethod
    def utcnow(cls):
        r = cls._q.next()
        if cls._tzta is not None:
            r = r - cls._tzta.utcoffset(r)
        return r

    def date(self):
        return self._date_type(
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
        tz = args[7]
        args = args[:7]
    else:
        tz = tzinfo or (getattr(args[0], 'tzinfo', None) if args else None)
    return mock_factory(
        'tdatetime', MockDateTime, (2001, 1, 1, 0, 0, 0), args, kw,
        tz=tz,
        delta=delta,
        delta_delta=10,
        delta_type=delta_type,
        date_type=date_type,
        strict=strict,
        )


test_datetime.__test__ = False


class MockDate(MockedCurrent, date):

    @classmethod
    def _ct(cls, d):
        return cls._cls(
            d.year,
            d.month,
            d.day,
        )

    @classmethod
    def today(cls):
        return cls._q.next()


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
            val = cls._q.next()
            t = timegm(val.utctimetuple())
            t += (float(val.microsecond)/ms)
            return t


def test_time(*args, delta=None, delta_type='seconds', **kw):
    if 'tzinfo' in kw or len(args) > 7 or (args and getattr(args[0], 'tzinfo', None)):
        raise TypeError("You don't want to use tzinfo with test_time")
    return mock_factory(
        'ttime', MockTime, (2001, 1, 1, 0, 0, 0), args, kw,
        delta=delta,
        delta_type=delta_type,
        )


test_time.__test__ = False
