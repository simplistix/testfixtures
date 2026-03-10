import atexit
import logging
import warnings
from collections import defaultdict
from dataclasses import dataclass
from logging import LogRecord
from pprint import pformat
from types import TracebackType
from typing import List, Tuple, Sequence, Callable, Any, Self
from warnings import warn

from .comparison import SequenceComparison, compare
from .utils import wrap


@dataclass
class Entry:
    """A captured log entry, with pre-computed extraction."""

    raw: Any
    actual: Any
    checked: bool = False


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
    ensure_checks_above: int

    instances: set['LogCapture'] = set()
    atexit_setup = False
    installed = False
    default_ensure_checks_above = logging.NOTSET

    def __init__(
        self,
        names: str | Tuple[str | None, ...] | None = None,
        install: bool = True,
        level: int = 1,
        propagate: bool | None = None,
        attributes: Sequence[str] | Callable[[LogRecord], Any] = (
            'name',
            'levelname',
            'getMessage',
        ),
        recursive_check: bool = False,
        ensure_checks_above: int | None = None,
    ):
        if not isinstance(names, tuple):
            names = (names,)
        self._source = LoggingSource(names, level, propagate, attributes)
        self._source.on_close = self._handle_close
        self.recursive_check = recursive_check
        if ensure_checks_above is None:
            self.ensure_checks_above = self.default_ensure_checks_above
        else:
            self.ensure_checks_above = ensure_checks_above
        self.clear()
        if install:
            self.install()

    def _handle_close(self) -> None:
        if self in self.instances:
            warn(
                'LogCapture instance closed while still installed, '
                'loggers captured:\n'
                '%s' % ('\n'.join((str(i._source.names) for i in self.instances)))
            )

    @classmethod
    def atexit(cls) -> None:
        if cls.instances:
            warnings.warn(
                'LogCapture instances not uninstalled by shutdown, '
                'loggers captured:\n'
                '%s' % ('\n'.join((str(i.names) for i in cls.instances)))
            )

    def __bool__(self) -> bool:
        # Some logging internals check boolean rather than identity for handlers :-(r
        return True

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
        if level is None:
            level = self.ensure_checks_above
        if level == logging.NOTSET:
            return
        un_checked = []
        for entry in self.entries:
            if (
                isinstance(entry.raw, LogRecord)
                and entry.raw.levelno >= level
                and not entry.checked
            ):
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
        self._source.install(self._collect_entry)
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
            self._source.uninstall()
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
        return '\n'.join(["%s %s\n  %s" % r for r in self.actual()])

    def check(self, *expected: Any, raises: bool = True) -> str | None:
        """
        This will compare the captured entries with the expected
        entries provided and raise an :class:`AssertionError` if they
        do not match.

        :param expected:

          A sequence of entries of the structure specified by the ``attributes``
          passed to the constructor.

        :param raises: If ``False``, the message that would be raised in the
                       :class:`AssertionError` will be returned instead of the
                       exception being raised.
        """
        __tracebackhide__ = True

        result = compare(
            expected,
            actual=self.actual(),
            recursive=self.recursive_check,
            raises=raises,
        )
        if result is None:
            self.mark_all_checked()
        return result

    def check_present(self, *expected: Any, order_matters: bool = True, raises: bool = True) -> str | None:
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


class LoggingSource(logging.Handler):
    """
    A :class:`logging.Handler` that captures log records into :class:`Entry` objects
    and delivers them to a collector callback.

    All ``logging``-module knowledge lives here; :class:`~testfixtures.LogCapture`
    never inspects framework-specific fields directly.
    """

    def __init__(
        self,
        names: Tuple[str | None, ...] = (None,),
        level: int = 1,
        propagate: bool | None = None,
        attributes: Sequence[str] | Callable[[LogRecord], Any] = ('levelname', 'getMessage'),
    ) -> None:
        logging.Handler.__init__(self)
        self.names = names
        self.level = level
        self.propagate = propagate
        self.attributes = attributes
        self.old: dict[str, dict[str | None, Any]] = defaultdict(dict)
        self._collector: Callable[[Entry], None] | None = None
        self.on_close: Callable[[], None] | None = None

    def __bool__(self) -> bool:
        # Some logging internals check boolean rather than identity for handlers :-(
        return True

    def emit(self, record: LogRecord) -> None:
        entry = Entry(raw=record, actual=self._compute_actual(record))
        if self._collector is not None:
            self._collector(entry)

    def _compute_actual(self, record: LogRecord) -> Any:
        if callable(self.attributes):
            return self.attributes(record)
        values = []
        for a in self.attributes:
            value = getattr(record, a, None)
            if callable(value):
                value = value()
            values.append(value)
        if len(values) == 1:
            return values[0]
        return tuple(values)

    def install(self, collector: Callable[[Entry], None]) -> None:
        self._collector = collector
        for name in self.names:
            logger = logging.getLogger(name)
            self.old['levels'][name] = logger.level
            self.old['filters'][name] = logger.filters
            self.old['handlers'][name] = logger.handlers
            self.old['disabled'][name] = logger.disabled
            self.old['propagate'][name] = logger.propagate
            logger.setLevel(self.level)
            logger.filters = []
            logger.handlers = [self]
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

    def close(self) -> None:
        super().close()
        if self.on_close is not None:
            self.on_close()
