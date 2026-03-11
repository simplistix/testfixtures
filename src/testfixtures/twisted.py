"""
Tools for helping to test Twisted applications.
"""
from pprint import pformat
from typing import Sequence, Callable, Any, Self
from unittest import TestCase

from constantly import NamedConstant
from twisted.logger import globalLogPublisher, formatEvent, LogLevel, ILogObserver, LogEvent

from . import compare
from .logcapture import Entry
import zope.interface


_LEVEL_MAP: dict[NamedConstant, int] = {
    LogLevel.debug: 10,
    LogLevel.info: 20,
    LogLevel.warn: 30,
    LogLevel.error: 40,
    LogLevel.critical: 50,
}


@zope.interface.implementer(ILogObserver)
class TwistedSource:
    """
    A capture source for Twisted log events, for use with :class:`~testfixtures.LogCapture`.

    :param fields:
      A sequence of field names or callables to extract from each event to form the ``actual``
      value stored in :class:`~testfixtures.logcapture.Entry`. If a single field is specified,
      the actual value is that field directly; otherwise it is a tuple.
    """

    def __init__(self, fields: Sequence[str | Callable] = ('log_level', formatEvent)) -> None:
        self.fields = fields
        self._collector: Callable[[Entry], None] | None = None
        self._original_observers: list | None = None

    def __call__(self, event: LogEvent) -> None:
        if self._collector is not None:
            failure = event.get('log_failure')
            entry = Entry(
                raw=event,
                actual=self._compute_actual(event),
                level=_LEVEL_MAP.get(event.get('log_level')),
                exception=failure.value if failure is not None else None,
            )
            self._collector(entry)

    def _compute_actual(self, event: LogEvent) -> Any:
        values = tuple(f(event) if callable(f) else event.get(f) for f in self.fields)
        return values[0] if len(values) == 1 else values

    def install(self, collector: Callable[[Entry], None]) -> None:
        self._collector = collector
        self._original_observers = globalLogPublisher._observers
        globalLogPublisher._observers = [self]

    def uninstall(self) -> None:
        if self._original_observers is not None:
            globalLogPublisher._observers = self._original_observers
            self._original_observers = None

@zope.interface.implementer(ILogObserver)
class LogCapture:
    """
    A helper for capturing stuff logged using Twisted's loggers.

    :param fields:
      A sequence of field names that :meth:`~LogCapture.check` will use to build
      "actual" events to compare against the expected events passed in.
      If items are strings, they will be treated as keys info the Twisted logging event.
      If they are callable, they will be called with the event as their only parameter.
      If only one field is specified, "actual" events will just be that one field;
      otherwise they will be a tuple of the specified fields.
    """

    def __init__(self, fields: Sequence[str | Callable] = ('log_level', formatEvent,)):
        #: The list of events captured.
        self.events: list[LogEvent] = []
        self.fields = fields

    def __call__(self, event: LogEvent) -> None:
        self.events.append(event)

    def install(self) -> None:
        "Start capturing."
        self.original_observers = globalLogPublisher._observers
        globalLogPublisher._observers = [self]

    def uninstall(self) -> None:
        "Stop capturing."
        globalLogPublisher._observers = self.original_observers

    def check(self, *expected: LogEvent, order_matters: bool = True) -> None:
        """
        Check captured events against those supplied. Please see the ``fields`` parameter
        to the constructor to see how "actual" events are built.

        :param order_matters:
          This defaults to ``True``. If ``False``, the order of expected logging versus
          actual logging will be ignored.
        """
        actual_event: Any
        actual = []
        for event in self.events:
            actual_event = tuple(field(event) if callable(field) else event.get(field)
                            for field in self.fields)
            if len(actual_event) == 1:
                actual_event = actual_event[0]
            actual.append(actual_event)
        if order_matters:
            compare(expected=expected, actual=actual)
        else:
            expected_ = list(expected)
            matched = []
            unmatched = []
            for entry in actual:
                try:
                    index = expected_.index(entry)
                except ValueError:
                    unmatched.append(entry)
                else:
                    matched.append(expected_.pop(index))
            if expected_:
                raise AssertionError((
                    'entries not as expected:\n\n'
                    'expected and found:\n%s\n\n'
                    'expected but not found:\n%s\n\n'
                    'other entries:\n%s'
                ) % (pformat(matched), pformat(expected_), pformat(unmatched)))

    def check_failure_text(self, expected: str, index: int = -1, attribute: str = 'value') -> None:
        """
        Check the string representation of an attribute of a logged ``Failure`` is as expected.

        :param expected: The expected string representation.
        :param index: The index into :attr:`events` where the failure should have been logged.
        :param attribute: The attribute of the failure of which to find the string representation.
        """
        compare(expected, actual=str(getattr(self.events[index]['log_failure'], attribute)))

    def raise_logged_failure(self, start_index: int = 0) -> None:
        """
        A debugging tool that raises the first failure encountered in captured logging.

        :param start_index: The index into :attr:`events` from where to start looking for failures.
        """
        for event in self.events[start_index:]:
            failure = event.get('log_failure')
            if failure:
                raise failure

    @classmethod
    def make(cls, testcase: TestCase, **kw: Sequence[str | Callable]) -> Self:
        """
        Instantiate, install and add a cleanup for a :class:`LogCapture`.

        :param testcase: This must be an instance of :class:`twisted.trial.unittest.TestCase`.
        :param kw: Any other parameters are passed directly to the :class:`LogCapture` constructor.
        :return: The :class:`LogCapture` instantiated by this method.
        """
        capture = cls(**kw)
        capture.install()
        testcase.addCleanup(capture.uninstall)
        return capture


#: Short reference to Twisted's ``LogLevel.debug``
DEBUG: NamedConstant = LogLevel.debug
#: Short reference to Twisted's ``LogLevel.info``
INFO: NamedConstant = LogLevel.info
#: Short reference to Twisted's ``LogLevel.warn``
WARN: NamedConstant = LogLevel.warn
#: Short reference to Twisted's ``LogLevel.error``
ERROR: NamedConstant = LogLevel.error
#: Short reference to Twisted's ``LogLevel.critical``
CRITICAL: NamedConstant = LogLevel.critical
