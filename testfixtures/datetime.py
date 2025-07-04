from calendar import timegm
from datetime import datetime, timedelta, date, tzinfo as TZInfo
from typing import Callable, Self, Tuple, TypeVar, Generic, Mapping

T = TypeVar('T', bound=datetime | date)


class Queue(list[T]):

    delta: float
    delta_delta: float
    delta_type: str

    def __init__(self, delta: float | None, delta_delta: float, delta_type: str) -> None:
        super().__init__()
        if delta is None:
            self.delta = 0
            self.delta_delta = delta_delta
        else:
            self.delta = delta
            self.delta_delta = 0
        self.delta_type = delta_type

    def advance_next(self, delta: timedelta) -> None:
        self[-1] += delta  # type: ignore[assignment]

    def next(self) -> T:
        instance = self.pop(0)
        if not self:
            self.delta += self.delta_delta
            n = instance + timedelta(**{self.delta_type: self.delta})
            self.append(n)  # type: ignore[arg-type]
        return instance


class MockedCurrent(Generic[T]):

    _mock_queue: Queue[T]
    _mock_base_class: type
    _mock_class: type
    _mock_tzinfo: TZInfo | None
    _mock_date_type: type[date]
    _correct_mock_type: Callable[[T], Self] | None = None

    def __init_subclass__(
            cls,
            concrete: bool = False,
            queue: Queue[T] | None = None,
            strict: bool | None = None,
            tzinfo: TZInfo | None = None,
            date_type: type[date] = date,
    ) -> None:
        if concrete:
            assert not queue is None, 'queue must be passed if concrete=True'
            cls._mock_queue = queue
            cls._mock_base_class = cls.__bases__[0].__bases__[1]
            cls._mock_class = cls if strict else cls._mock_base_class
            cls._mock_tzinfo = tzinfo
            cls._mock_date_type = date_type

    @classmethod
    def add(cls, *args: int | T, **kw: int | TZInfo | None) -> None:
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
                instance = instance.replace(tzinfo=None)  # type: ignore[attr-defined]
            if cls._correct_mock_type:
                instance = cls._correct_mock_type(instance)
        else:
            instance = cls(*args, **kw)  # type: ignore[arg-type]
        cls._mock_queue.append(instance)

    @classmethod
    def set(cls, *args: int | T, **kw: int | TZInfo | None) -> None:
        cls._mock_queue.clear()
        cls.add(*args, **kw)

    @classmethod
    def tick(cls, *args: timedelta, **kw: float) -> None:
        if kw:
            delta = timedelta(**kw)
        else:
            delta, = args
        cls._mock_queue.advance_next(delta)

    def __add__(self, other: timedelta) -> Self:
        instance = super().__add__(other)  # type: ignore[misc]
        if self._correct_mock_type:
            instance = self._correct_mock_type(instance)
        return instance

    def __new__(cls, *args: int, **kw: int | TZInfo | None) -> Self:
        if cls is cls._mock_class:
            return super().__new__(cls, *args, **kw)
        else:
            return cls._mock_class(*args, **kw)


def mock_factory(
        type_name: str,
        mock_class: type[MockedCurrent[T]],
        default: Tuple[int, ...],
        args: tuple[int | T | None | TZInfo, ...],
        kw: Mapping[str, int | TZInfo | None],
        delta: float | None,
        delta_type: str,
        delta_delta: float = 1,
        date_type: type[date] | None = None,
        tzinfo: TZInfo | None = None,
        strict: bool = False
) -> type[MockedCurrent[T]]:
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
        cls.add(*args, **kw)  # type: ignore[attr-defined]

    return cls


class MockDateTime(MockedCurrent[datetime], datetime):

    @classmethod
    def add(cls, *args: int | datetime, **kw: int | TZInfo | None) -> None:
        """
        This will add the :class:`datetime.datetime` created from the
        supplied parameters to the queue of datetimes to be returned by
        :meth:`~MockDateTime.now` or :meth:`~MockDateTime.utcnow`. An instance
        of :class:`~datetime.datetime` may also be passed as a single
        positional argument.
        """
        return super().add(*args, **kw)

    @classmethod
    def set(cls, *args: int | datetime, **kw: int | TZInfo | None) -> None:
        """
        This will set the :class:`datetime.datetime` created from the
        supplied parameters as the next datetime to be returned by
        :meth:`~MockDateTime.now` or :meth:`~MockDateTime.utcnow`, clearing out
        any datetimes in the queue.  An instance
        of :class:`~datetime.datetime` may also be passed as a single
        positional argument.
        """
        return super().set(*args, **kw)

    @classmethod
    def tick(cls, *args: timedelta, **kw: float) -> None:
        """
        This method should be called either with a :class:`~datetime.timedelta`
        as a positional argument, or with keyword parameters that will be used
        to construct a :class:`~datetime.timedelta`.

        The  :class:`~datetime.timedelta` will be used to advance the next datetime
        to be returned by :meth:`~MockDateTime.now` or :meth:`~MockDateTime.utcnow`.
        """
        return super().tick(*args, **kw)

    @classmethod  
    def _correct_mock_type(cls, instance: datetime) -> Self:
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
    def _adjust_instance_using_tzinfo(cls, instance: datetime) -> Self:
        if cls._mock_tzinfo:
            offset = cls._mock_tzinfo.utcoffset(instance)
            if offset is None:
                raise TypeError('tzinfo with .utcoffset() returning None is not supported')
            instance = instance - offset
        return instance  # type: ignore[return-value]

    @classmethod
    def now(cls, tz: TZInfo | None = None) -> Self:
        """
        :param tz: An optional timezone to apply to the returned time.
                If supplied, it must be an instance of a
                :class:`~datetime.tzinfo` subclass.

        This will return the next supplied or calculated datetime from the
        internal queue, rather than the actual current datetime.

        If `tz` is supplied, see :ref:`timezones`.
        """
        instance = cls._mock_queue.next()
        if tz is not None:
            instance = tz.fromutc(cls._adjust_instance_using_tzinfo(instance).replace(tzinfo=tz))
        return cls._correct_mock_type(instance)

    @classmethod
    def utcnow(cls) -> Self:
        """
        This will return the next supplied or calculated datetime from the
        internal queue, rather than the actual current UTC datetime.

        If you care about timezones, see :ref:`timezones`.
        """
        instance = cls._mock_queue.next()
        return cls._adjust_instance_using_tzinfo(instance)

    def date(self) -> date:
        """
        This will return the date component of the current mock instance,
        but using the date type supplied when the mock class was created.
        """
        return self._mock_date_type(
            self.year,
            self.month,
            self.day
            )


def mock_datetime(
        *args: int | datetime | None | TZInfo,
        tzinfo: TZInfo | None = None,
        delta: float | None = None,
        delta_type: str = 'seconds',
        date_type: type[date] = date,
        strict: bool = False,
        **kw: int | TZInfo | None,
) -> type[MockDateTime]:
    """
    .. currentmodule:: testfixtures.datetime

    A function that returns a mock object that can be used in place of
    the :class:`datetime.datetime` class but where the return value of
    :meth:`~MockDateTime.now` can be controlled.

    If a single positional argument of ``None`` is passed, then the
    queue of datetimes to be returned will be empty and you will need to
    call :meth:`~MockDateTime.set` or :meth:`~MockDateTime.add` before calling
    :meth:`~MockDateTime.now` or :meth:`~MockDateTime.utcnow`.

    If an instance of :class:`~datetime.datetime` is passed as a single
    positional argument, that will be used as the first date returned by
    :meth:`~MockDateTime.now`

    :param year:
      An optional year used to create the first datetime returned by :meth:`~MockDateTime.now`.

    :param month:
      An optional month used to create the first datetime returned by :meth:`~MockDateTime.now`.

    :param day:
      An optional day used to create the first datetime returned by :meth:`~MockDateTime.now`.

    :param hour:
      An optional hour used to create the first datetime returned by :meth:`~MockDateTime.now`.

    :param minute:
      An optional minute used to create the first datetime returned by :meth:`~MockDateTime.now`.

    :param second:
      An optional second used to create the first datetime returned by :meth:`~MockDateTime.now`.

    :param microsecond:
      An optional microsecond used to create the first datetime returned by
      :meth:`~MockDateTime.now`.

    :param tzinfo:
      An optional :class:`datetime.tzinfo`, see :ref:`timezones`.

    :param delta:
      The size of the delta to use between values returned from mocked class methods.
      If not specified, it will increase by 1 with each call to :meth:`~MockDateTime.now`.

    :param delta_type:
      The type of the delta to use between values returned from mocked class methods.
      This can be any keyword parameter accepted by the :class:`~datetime.timedelta` constructor.

    :param date_type:
      The type to use for the return value of the mocked class methods.
      This can help with gotchas that occur when type checking is performed on values returned
      by the :meth:`~testfixtures.datetime.MockDateTime.date` method.

    :param strict:
      If ``True``, calling the mock class and any of its methods will result in an instance of
      the mock being returned. If ``False``, the default, an instance of
      :class:`~datetime.datetime` will be returned instead.

    The mock returned will behave exactly as the :class:`datetime.datetime` class
    as well as being a subclass of :class:`~testfixtures.datetime.MockDateTime`.
    """
    if len(args) > 7:
        tzinfo = args[7]  # type: ignore[assignment]
        args = args[:7]
    else:
        tzinfo = tzinfo or (getattr(args[0], 'tzinfo', None) if args else None)
    return mock_factory(
        'MockDateTime',
        MockDateTime,
        (2001, 1, 1, 0, 0, 0),
        args,
        kw,
        tzinfo=tzinfo,
        delta=delta,
        delta_delta=10,
        delta_type=delta_type,
        date_type=date_type,
        strict=strict,
    )  # type: ignore[return-value]


class MockDate(MockedCurrent[date], date):

    @classmethod
    def _correct_mock_type(cls, instance: date) -> Self:
        return cls._mock_class(
            instance.year,
            instance.month,
            instance.day,
        )

    @classmethod
    def add(cls, *args: int | date, **kw: int | TZInfo | None) -> None:
        """
        This will add the :class:`datetime.date` created from the
        supplied parameters to the queue of dates to be returned by
        :meth:`~MockDate.today`.  An instance
        of :class:`~datetime.date` may also be passed as a single
        positional argument.
        """
        return super().add(*args, **kw)

    @classmethod
    def set(cls, *args: int | date, **kw: int | TZInfo | None) -> None:
        """
        This will set the :class:`datetime.date` created from the
        supplied parameters as the next date to be returned by
        :meth:`~MockDate.today`, regardless of any dates in the
        queue.   An instance
        of :class:`~datetime.date` may also be passed as a single
        positional argument.
        """
        return super().set(*args, **kw)

    @classmethod
    def tick(cls, *args: timedelta, **kw: float) -> None:
        """
        This method should be called either with a :class:`~datetime.timedelta`
        as a positional argument, or with keyword parameters that will be used
        to construct a :class:`~datetime.timedelta`.

        The  :class:`~datetime.timedelta` will be used to advance the next date
        to be returned by :meth:`~MockDate.today`.
        """
        return super().tick(*args, **kw)

    @classmethod
    def today(cls) -> Self:
        """
        This will return the next supplied or calculated date from the
        internal queue, rather than the actual current date.

        """
        return cls._mock_queue.next()  # type: ignore[return-value]


def mock_date(
        *args: int | date | None,
        delta: float | None = None,
        delta_type: str = 'days',
        strict: bool = False,
        **kw: int
) -> type[MockDate]:
    """
    .. currentmodule:: testfixtures.datetime

    A function that returns a mock object that can be used in place of
    the :class:`datetime.date` class but where the return value of
    :meth:`~datetime.date.today` can be controlled.

    If a single positional argument of ``None`` is passed, then the
    queue of dates to be returned will be empty and you will need to
    call :meth:`~MockDate.set` or :meth:`~MockDate.add` before calling
    :meth:`~MockDate.today`.

    If an instance of :class:`~datetime.date` is passed as a single
    positional argument, that will be used as the first date returned by
    :meth:`~datetime.date.today`

    :param year:
      An optional year used to create the first date returned by :meth:`~datetime.date.today`.

    :param month:
      An optional month used to create the first date returned by :meth:`~datetime.date.today`.

    :param day:
      An optional day used to create the first date returned by :meth:`~datetime.date.today`.

    :param delta:
      The size of the delta to use between values returned from :meth:`~datetime.date.today`.
      If not specified, it will increase by 1 with each call to :meth:`~datetime.date.today`.

    :param delta_type:
      The type of the delta to use between values returned from :meth:`~datetime.date.today`.
      This can be any keyword parameter accepted by the :class:`~datetime.timedelta` constructor.

    :param strict:
      If ``True``, calling the mock class and any of its methods will result in an instance of
      the mock being returned. If ``False``, the default, an instance of :class:`~datetime.date`
      will be returned instead.

    The mock returned will behave exactly as the :class:`datetime.date` class
    as well as being a subclass of :class:`~testfixtures.datetime.MockDate`.
    """
    return mock_factory(
        'MockDate', MockDate, (2001, 1, 1), args, kw,
        delta=delta,
        delta_type=delta_type,
        strict=strict,
    )  # type: ignore[return-value]


ms = 10**6


class MockTimeFactory(MockedCurrent[datetime], datetime):
    pass


class MockTime:

    def __init__(self, factory: type[MockedCurrent[datetime]]):
        self.factory = factory

    def add(self, *args: int | datetime, **kw: int | TZInfo | None) -> None:
        """
        This will add the time specified by the supplied parameters to the
        queue of times to be returned by calls to the mock. The
        parameters are the same as the :class:`datetime.datetime`
        constructor. An instance of :class:`~datetime.datetime` may also
        be passed as a single positional argument.
        """
        self.factory.add(*args, **kw)

    def set(self, *args: int | datetime, **kw: int | TZInfo | None) -> None:
        """
        This will set the time specified by the supplied parameters as
        the next time to be returned by a call to the mock, regardless of
        any times in the queue.  The parameters are the same as the
        :class:`datetime.datetime` constructor.  An instance of
        :class:`~datetime.datetime` may also be passed as a single
        positional argument.
        """
        self.factory.set(*args, **kw)

    def tick(self, *args: timedelta, **kw: float) -> None:
        """
        This method should be called either with a :class:`~datetime.timedelta`
        as a positional argument, or with keyword parameters that will be used
        to construct a :class:`~datetime.timedelta`.

        The  :class:`~datetime.timedelta` will be used to advance the next time
        to be returned by a call to the mock.
        """
        self.factory.tick(*args, **kw)

    def __call__(self) -> float:
        instance = self.factory._mock_queue.next()
        time: float = timegm(instance.utctimetuple())
        time += (float(instance.microsecond) / ms)
        return time


def mock_time(
        *args: int | datetime | None,
        delta: float | None = None,
        delta_type: str = 'seconds',
        **kw: int,
) -> MockTime:
    """
    .. currentmodule:: testfixtures.datetime

    A function that returns a :class:`mock object <testfixtures.datetime.MockTime>` that can be
    used in place of the :func:`time.time` function but where the return value can be
    controlled.

    If a single positional argument of ``None`` is passed, then the
    queue of times to be returned will be empty and you will need to
    call :meth:`~MockTime.set` or :meth:`~MockTime.add` before calling
    the mock.

    If an instance of :class:`~datetime.datetime` is passed as a single
    positional argument, that will be used to create the first time returned.

    :param year: An optional year used to create the first time returned.

    :param month: An optional month used to create the first time.

    :param day: An optional day used to create the first time.

    :param hour: An optional hour used to create the first time.

    :param minute: An optional minute used to create the first time.

    :param second: An optional second used to create the first time.

    :param microsecond: An optional microsecond used to create the first time.

    :param delta:
      The size of the delta to use between values returned.
      If not specified, it will increase by 1 with each call to the mock.

    :param delta_type:
      The type of the delta to use between values returned.
      This can be any keyword parameter accepted by the :class:`~datetime.timedelta` constructor.

    The :meth:`~testfixtures.datetime.MockTime.add`, :meth:`~testfixtures.datetime.MockTime.set`
    and :meth:`~testfixtures.datetime.MockTime.tick` methods on the mock can be used to
    control the return values.
    """
    if 'tzinfo' in kw or len(args) > 7 or (args and getattr(args[0], 'tzinfo', None)):
        raise TypeError("You don't want to use tzinfo with test_time")
    factory = mock_factory(
        'MockTime',
        MockTimeFactory,
        (2001, 1, 1, 0, 0, 0),
        args,
        kw,
        delta=delta,
        delta_type=delta_type,
    )
    return MockTime(factory)
