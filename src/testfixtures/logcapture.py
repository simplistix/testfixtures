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
    Protocol that capture sources must implement to be used with :class:`LogCapture`.
    """

    def install(self, collector: Callable[['Entry'], None]) -> None:
        """Start capturing, delivering entries to ``collector``."""
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
    """A captured log entry, with pre-computed extraction."""

    raw: Any
    actual: Any
    level: int | None  # numeric level for ensure_checked; None means not level-checkable
    exception: BaseException | None = None
    checked: bool = False

LogRecordAttributes: TypeAlias = AttributeSpec[LogRecord]


class LogCapture:
    """
    These are used to capture entries logged to the Python logging
    framework and make assertions about what was logged.

    :param names: A string (or tuple of strings) containing the dotted name(s)
                  of loggers to capture. By default, the root logger is
                  captured.

    :param install: If `True`, the :class:`LogCapture` will be
                    installed as part of its instantiation.

    :param propagate: If specified, any captured loggers will have their
                      `propagate` attribute set to the supplied value. This can
                      be used to prevent propagation from a child logger to a
                      parent logger that has configured handlers.

    :param attributes:

      The sequence of attribute names to return for each record or a callable
      that extracts a row from a record.

      If a sequence of attribute names, those attributes will be taken from the
      :class:`~logging.LogRecord`. If an attribute is callable, the value
      used will be the result of calling it. If an attribute is missing,
      ``None`` will be used in its place.

      If a callable, it will be called with the :class:`~logging.LogRecord`
      and the value returned will be used as the row.

    :param recursive_check:

      If ``True``, log messages will be compared recursively by
      :meth:`LogCapture.check`.

    :param ensure_checks_above:

      The log level above which checks must be made for logged events.
      See :meth:`ensure_checked`.

    """

    #: The log level above which checks must be made for logged events.
    ensure_checks_above: int | None

    #: The list of :class:`~testfixtures.logcapture.Entry` objects captured so far.
    entries: list[Entry]

    instances: set['LogCapture'] = set()
    atexit_setup = False
    installed = False
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

    @property
    def records(self) -> List[LogRecord]:
        """
        The records captured by this :class:`LogCapture`.

        .. deprecated:: 12
            Use the ``entries`` attribute instead.
        """
        return [e.raw for e in self.entries if isinstance(e.raw, LogRecord)]

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

        :param level: the logging level, defaults to :attr:`ensure_checks_above`.
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
        Install this :class:`LogCapture` into the Python logging
        framework for the named loggers.

        This will remove any existing handlers for those loggers and
        drop their level to that specified on this :class:`LogCapture` in order
        to capture all logging.
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
        Un-install this :class:`LogCapture` from the Python logging
        framework for the named loggers.

        This will re-instate any existing handlers for those loggers
        that were removed during installation and restore their level
        that prior to installation.
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
        The sequence of actual records logged, having had their attributes
        extracted as specified by the ``attributes`` parameter to the
        :class:`LogCapture` constructor.

        This can be useful for making more complex assertions about logged
        records. The actual records logged can also be inspected by using the
        ``entries`` attribute.
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

          A sequence of entries of the structure specified by the ``attributes``
          passed to the constructor.

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
        This will check if the captured entries contain all of the expected
        entries provided and raise an :class:`AssertionError` if not.
        This will ignore entries that have been captured but that do not
        match those in ``expected``.

        :param expected:

          A sequence of entries of the structure specified by the ``attributes``
          passed to the constructor.

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
    A :class:`logging.Handler` that captures log records into :class:`Entry` objects
    and delivers them to a collector callback.

    All ``logging``-module knowledge lives here; :class:`~testfixtures.LogCapture`
    never inspects framework-specific fields directly.
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
