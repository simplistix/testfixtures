import atexit
import logging
import warnings
from collections import defaultdict
from dataclasses import dataclass
from logging import LogRecord
from pprint import pformat
from types import TracebackType
from typing import (
    Any, Callable, Sequence, TypeAlias, TypeVar, List, Tuple, Self, Protocol, overload
)
from warnings import warn

from .comparison import SequenceComparison, compare
from .utils import wrap


class CaptureSource(Protocol):
    """
    Protocol that :class:`LogCapture` sources must implement.
    """

    def install(self, collector: Callable[['Entry'], None]) -> None:
        """
        Start capturing.

        :param collector: The destination for captured :attr:`~testfixtures.LogCapture.entries`.
        """
        ...

    def uninstall(self) -> None:
        """Stop capturing and restore any previous state."""
        ...



T = TypeVar('T')
AttributeSpec: TypeAlias = Sequence[str | Callable[[T], Any]] | Callable[[T], Any]


def build_actual_extractor(
    attributes: AttributeSpec[T],
    extract_field: Callable[[T, str], Any],
) -> Callable[[T], Any]:
    # Compile the attributes spec into a callable that extracts an entry's
    # ``actual`` value from a raw record. A bare string is treated as a single
    # attribute name (``str`` is itself a ``Sequence[str]``).
    if callable(attributes):
        return attributes
    if isinstance(attributes, str):
        attributes = (attributes,)
    attrs = tuple(attributes)
    if len(attrs) == 1:
        only = attrs[0]
        if callable(only):
            return only
        return lambda raw: extract_field(raw, only)
    return lambda raw: tuple(
        a(raw) if callable(a) else extract_field(raw, a) for a in attrs
    )


@dataclass
class Entry:
    """
    A captured log entry captured by a :class:`~testfixtures.logcapture.CaptureSource`.
    """

    #: The raw object delivered by the logging framework. This is a :class:`~logging.LogRecord`
    #: for standard library logging.
    raw: Any
    #: The extracted value used by :meth:`~testfixtures.LogCapture.check` and related methods.
    #: Its structure is determined by the ``attributes`` parameter of the source.
    actual: Any
    #: Numeric log level used by :meth:`~testfixtures.LogCapture.ensure_checked`, or ``None``
    #: if the source does not provide a comparable numeric level.
    level: int | None
    #: The exception associated with this entry if one was captured, otherwise ``None``.
    exception: BaseException | None = None
    #: Whether this entry has been marked as checked by a :meth:`~testfixtures.LogCapture.check`
    #: call.
    checked: bool = False

LogRecordAttributes: TypeAlias = AttributeSpec[LogRecord]


class LogCapture:
    """
    Captures log entries from one or more sources and provides methods to check what was logged.

    :param sources:
        One or more :class:`capture sources <testfixtures.logcapture.CaptureSource>`
    :param install:
        If ``True`` (the default), capturing starts immediately on construction.
        If ``False``, installation is deferred until :meth:`install` is called.
    :param recursive_check:
        If ``True``, entries are compared recursively by :meth:`check`.
    :param ensure_checks_above:
        The log level above which entries must have been checked.
        See :meth:`ensure_checked`.

    For compatibility with earlier versions, capturing only
    :any:`standard library logging <logging>` is supported by instantiating using these parameters:

    :param names:
        A string (or tuple of strings) containing the dotted name(s) of loggers to capture.
        By default, the root logger is captured.
    :param level:
        The minimum log level to capture.  Defaults to ``1``, capturing everything.
    :param propagate:
        If specified, any captured loggers will have their propagate attribute set to the supplied
        value. This can be used to prevent propagation from a child logger to a parent logger that
        has configured handlers.
    :param attributes:
        The sequence of attribute names to return for each record or a callable that extracts
        :attr:`~testfixtures.logcapture.Entry.actual` from a record.

        If a sequence of attribute names is passed, those attributes will be taken from the
        :class:`logging.LogRecord`. If an attribute is callable, the value used will be the result
        of calling it. If an attribute is missing, ``None`` will be used in its place.

        If a callable is passed, it will be called with the :class:`~logging.LogRecord` and the
        value returned will be used as :attr:`~testfixtures.logcapture.Entry.actual`.
    """

    #: The list of :class:`entries <testfixtures.logcapture.Entry>` captured so far.
    entries: list[Entry]

    @property
    def records(self) -> List[LogRecord]:
        """
        The records captured by this :class:`LogCapture`.

        .. deprecated:: 12
            Use the :attr:`entries` attribute instead.
        """
        return [e.raw for e in self.entries if isinstance(e.raw, LogRecord)]


    instances: set['LogCapture'] = set()
    atexit_setup = False
    installed = False

    ensure_checks_above: int | None
    #: Class-level default for :meth:`ensure_checked`. Set this to apply a level
    #: threshold to all :class:`LogCapture` instances that do not override it explicitly.
    default_ensure_checks_above: int | None = None

    @overload
    def __init__(
        self,
        *sources: CaptureSource,
        install: bool = True,
        recursive_check: bool = False,
        ensure_checks_above: int | None = None,
    ) -> None: ...

    @overload
    def __init__(
        self,
        names: str | Tuple[str | None, ...] | None = None,
        *,
        install: bool = True,
        level: int = 1,
        propagate: bool | None = None,
        attributes: LogRecordAttributes = ...,
        recursive_check: bool = False,
        ensure_checks_above: int | None = None,
    ) -> None: ...

    def __init__(  # type: ignore[misc]
        self,
        *args: Any,
        install: bool = True,
        level: int = 1,
        propagate: bool | None = None,
        attributes: LogRecordAttributes = (
            'name',
            'levelname',
            'getMessage',
        ),
        recursive_check: bool = False,
        ensure_checks_above: int | None = None,
    ) -> None:
        if args and hasattr(args[0], 'install'):
            self._sources = list(args)
        else:
            names: str | Tuple[str | None, ...] | None = args[0] if args else None
            if not isinstance(names, tuple):
                names = (names,)
            self._sources = [LoggingSource(attributes, level, names=names, propagate=propagate)]
        self.recursive_check = recursive_check
        if ensure_checks_above is None:
            self.ensure_checks_above = self.default_ensure_checks_above
        else:
            self.ensure_checks_above = ensure_checks_above
        self.clear()
        if install:
            self.install()

    @classmethod
    def atexit(cls) -> None:
        if cls.instances:
            warnings.warn(
                'LogCapture instances not uninstalled by shutdown, '
                'loggers captured:\n'
                '%s' % ('\n'.join((', '.join(repr(s) for s in i._sources) for i in cls.instances)))
            )

    def __len__(self) -> int:
        return len(self.entries)

    def __getitem__(self, index: int) -> Any:
        return self.entries[index].actual

    def __contains__(self, what: Any) -> bool:
        for i, entry in enumerate(self.entries):
            if what == entry.actual:
                self.entries[i].checked = True
                return True
        return False

    def clear(self) -> None:
        """Clear any entries that have been captured."""
        self.entries: list[Entry] = []

    def mark_all_checked(self) -> None:
        """
        Mark all captured events as checked.
        This should be called if you have made assertions about logging
        other than through :class:`LogCapture` methods.
        """
        for entry in self.entries:
            entry.checked = True

    def ensure_checked(self, level: int | None = None) -> None:
        """
        Ensure every entry logged above the specified `level` has been checked.
        Raises an :class:`AssertionError` if this is not the case.

        :param level:
           This defaults to the level passed during :class:`LogCapture` instantiation.
        """
        threshold: int | None = level if level is not None else self.ensure_checks_above
        if threshold is None:
            return
        un_checked = []
        for entry in self.entries:
            if entry.level is not None and entry.level >= threshold and not entry.checked:
                un_checked.append(entry.actual)
        if un_checked:
            raise AssertionError(('Not asserted ERROR log(s): %s') % (pformat(un_checked)))

    def _collect_entry(self, entry: Entry) -> None:
        self.entries.append(entry)

    def install(self) -> Self | None:
        """
        Install this :class:`LogCapture`, enabling all configured sources to begin capturing.
        """
        for source in self._sources:
            source.install(self._collect_entry)
        self.instances.add(self)
        if not self.__class__.atexit_setup:
            atexit.register(self.atexit)
            self.__class__.atexit_setup = True
        return None

    def uninstall(self) -> None:
        """
        Uninstall this :class:`LogCapture`, restoring all sources to their previous state.
        """
        if self in self.instances:
            for source in self._sources:
                source.uninstall()
            self.instances.remove(self)

    @classmethod
    def uninstall_all(cls) -> None:
        "This will uninstall all existing :class:`LogCapture` objects."
        for i in tuple(cls.instances):
            i.uninstall()

    def actual(self) -> list[Any]:
        """
        The sequence of :attr:`~testfixtures.logcapture.Entry.actual` items captured.

        This can be useful for making more complex assertions about captured logging.
        The full :class:`~testfixtures.logcapture.Entry` objects captured for each logging call
        can be accessed through :attr:`entries`.
        """
        return [e.actual for e in self.entries]

    def __str__(self) -> str:
        if not self.entries:
            return 'No logging captured'
        tuples = (r if isinstance(r, tuple) else (r,) for r in self.actual())
        return '\n'.join(' '.join(str(e) for e in t) for t in tuples)

    def check(self, *expected: Any, order_matters: bool = True, raises: bool = True) -> str | None:
        """
        This will compare the captured entries with the expected
        entries provided and raise an :class:`AssertionError` if they
        do not match.

        :param expected:

          A sequence of expected :attr:`~testfixtures.logcapture.Entry.actual` items.

        :param order_matters:

          A keyword-only parameter that controls whether the order of the
          captured entries is required to match those of the expected entries.
          Defaults to ``True``.

        :param raises: If ``False``, the message that would be raised in the
                       :class:`AssertionError` will be returned instead of the
                       exception being raised.
        """
        __tracebackhide__ = True

        result = None
        if order_matters:
            result = compare(
                expected, actual=self.actual(), recursive=self.recursive_check, raises=False
            )
        else:
            actual = self.actual()
            expected_ = SequenceComparison(
                *expected, ordered=False, partial=False, recursive=self.recursive_check
            )
            if expected_ != actual:
                result = expected_.failed
        if result and raises:
            raise AssertionError(result)
        self.mark_all_checked()
        return result

    def raise_first_exception(self, start_index: int = 0) -> None:
        """
        Raise the first captured exception from ``start_index`` onwards.

        :param start_index: The index into :attr:`entries` from where to start looking.
        """
        for entry in self.entries[start_index:]:
            if entry.exception is not None:
                raise entry.exception

    def check_exception_str(self, expected: str, index: int = -1) -> None:
        """
        Check the string representation of a captured exception.

        :param expected: The expected string.
        :param index: The index into :attr:`entries` where the exception should have been captured.
        """
        compare(expected, actual=str(self.entries[index].exception))

    def check_present(
            self, *expected: Any, order_matters: bool = True, raises: bool = True
    ) -> str | None:
        """
        This will check if the captured attr:`entries` contain all of the expected
        entries provided and raise an :class:`AssertionError` if not.
        This will ignore entries that have been captured but that do not
        match those in ``expected``.

        :param expected:

          A sequence of expected :attr:`~testfixtures.logcapture.Entry.actual` items.

        :param order_matters:

          A keyword-only parameter that controls whether the order of the
          captured entries is required to match those of the expected entries.
          Defaults to ``True``.

        :param raises: If ``False``, the message that would be raised in the
                       :class:`AssertionError` will be returned instead of the
                       exception being raised.
        """
        __tracebackhide__ = True
        actual = self.actual()
        expected_ = SequenceComparison(
            *expected, ordered=order_matters, partial=True, recursive=self.recursive_check
        )
        if expected_ != actual:
            if raises:
                raise AssertionError(expected_.failed)
            return expected_.failed
        for index in expected_.checked_indices:
            self.entries[index].checked = True
        return None

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.uninstall()
        self.ensure_checked()


class LogCaptureForDecorator(LogCapture):
    def install(self) -> Self:
        LogCapture.install(self)
        self.clear()
        return self


def log_capture(*names: str, **kw: Any) -> Callable:
    """
    A decorator for making a :class:`LogCapture` installed and
    available for the duration of a test function.

    :param names: An optional sequence of names specifying the loggers
                  to be captured. If not specified, the root logger
                  will be captured.

    Keyword parameters other than ``install`` may also be supplied and will be
    passed on to the :class:`LogCapture` constructor.
    """
    l = LogCaptureForDecorator(names or None, install=False, **kw)
    return wrap(l.install, l.uninstall)


class LoggingHandler(logging.Handler):
    """Minimal handler that forwards records to a :class:`LoggingSource`."""

    def __init__(self, source: 'LoggingSource') -> None:
        super().__init__()
        self._source = source

    def __bool__(self) -> bool:
        # Some logging internals check boolean rather than identity for handlers :-(
        return True

    def emit(self, record: LogRecord) -> None:
        self._source._handle_record(record)

    def close(self) -> None:
        super().close()
        self._source._handler_closed()


class LoggingSource:
    """
    A :class:`~testfixtures.logcapture.CaptureSource` for the standard-library
    :mod:`logging` framework, for use with :class:`~testfixtures.LogCapture`.

    :param attributes:
        The sequence of attribute names to return for each record or a callable that extracts
        :attr:`~testfixtures.logcapture.Entry.actual` from a record.

        If a sequence of attribute names is passed, those attributes will be taken from the
        :class:`logging.LogRecord`. If an attribute is callable, the value used will be the result
        of calling it. If an attribute is missing, ``None`` will be used in its place.

        If a callable is passed, it will be called with the :class:`~logging.LogRecord` and the
        value returned will be used as :attr:`~testfixtures.logcapture.Entry.actual`.
    :param level:
        The minimum log level to capture.  Defaults to ``1``, capturing everything.
    :param names:
        A string (or tuple of strings) containing the dotted name(s) of loggers to capture.
        By default, the root logger is captured.
    :param propagate:
        If specified, any captured loggers will have their propagate attribute set to the supplied
        value. This can be used to prevent propagation from a child logger to a parent logger that
        has configured handlers.
    """

    def __init__(
        self,
        attributes: LogRecordAttributes = ('levelname', 'getMessage'),
        level: int = 1,
        *,
        names: Tuple[str | None, ...] = (None,),
        propagate: bool | None = None,
    ) -> None:
        self.attributes = attributes
        self.level = level
        self.names = names
        self.propagate = propagate
        self.old: dict[str, dict[str | None, Any]] = defaultdict(dict)
        self._collector: Callable[[Entry], None] | None = None
        self._handler: LoggingHandler | None = None
        self._compute_actual = build_actual_extractor(attributes, self.extract_field)

    def extract_field(self, raw: LogRecord, attribute: str) -> Any:
        value = getattr(raw, attribute, None)
        if callable(value):
            value = value()
        return value

    def __repr__(self) -> str:
        return f'LoggingSource({self.names!r})'

    def _handler_closed(self) -> None:
        if self._collector is not None:
            warn(
                f'LoggingSource closed while still capturing loggers: {self.names!r}\n'
                'Call uninstall() or use LogCapture as a context manager.'
            )

    def _handle_record(self, record: LogRecord) -> None:
        if self._collector is None:
            return
        exception = record.exc_info[1] if record.exc_info else None
        self._collector(Entry(
            raw=record,
            actual=self._compute_actual(record),
            level=record.levelno,
            exception=exception,
        ))

    def install(self, collector: Callable[[Entry], None]) -> None:
        self._collector = collector
        self._handler = LoggingHandler(self)
        for name in self.names:
            logger = logging.getLogger(name)
            self.old['levels'][name] = logger.level
            self.old['filters'][name] = logger.filters
            self.old['handlers'][name] = logger.handlers
            self.old['disabled'][name] = logger.disabled
            self.old['propagate'][name] = logger.propagate
            logger.setLevel(self.level)
            logger.filters = []
            logger.handlers = [self._handler]
            logger.disabled = False
            if self.propagate is not None:
                logger.propagate = self.propagate

    def uninstall(self) -> None:
        for name in self.names:
            logger = logging.getLogger(name)
            logger.setLevel(self.old['levels'][name])
            logger.filters = self.old['filters'][name]
            logger.handlers = self.old['handlers'][name]
            logger.disabled = self.old['disabled'][name]
            logger.propagate = self.old['propagate'][name]
        self._handler = None
        self._collector = None
