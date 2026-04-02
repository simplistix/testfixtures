"""
Tools for helping to test Twisted applications.
"""
from typing import Sequence, Callable, Any, Self

from constantly import NamedConstant
from twisted.logger import globalLogPublisher, formatEvent, LogLevel, ILogObserver, LogEvent
from twisted.trial.unittest import TestCase

from . import compare
from .logcapture import Entry, LogCapture as _LogCapture
import zope.interface


LEVEL_MAP: dict[NamedConstant, int] = {
    LogLevel.debug: 10,
    LogLevel.info: 20,
    LogLevel.warn: 30,
    LogLevel.error: 40,
    LogLevel.critical: 50,
}


def level_name(event: LogEvent) -> str:
    return event['log_level'].name.upper()


@zope.interface.implementer(ILogObserver)
class TwistedSource:
    """
    A capture source for Twisted log events, for use with :class:`~testfixtures.LogCapture`.

    :param fields:
      A sequence of field names or callables to extract from each event to form the ``actual``
      value stored in :class:`~testfixtures.logcapture.Entry`. If a single field is specified,
      the actual value is that field directly; otherwise it is a tuple.
    """

    def __init__(
        self,
        attributes: Sequence[str | Callable] | Callable = (level_name, formatEvent),
        level: int = 0,
    ) -> None:
        self.attributes = attributes
        self.level = level
        self._collector: Callable[[Entry], None] | None = None
        self._original_observers: list | None = None

    def __call__(self, event: LogEvent) -> None:
        if self._collector is not None:
            if self.level:
                event_level = LEVEL_MAP.get(event.get('log_level'))
                if event_level is None or event_level < self.level:
                    return
            failure = event.get('log_failure')
            entry = Entry(
                raw=event,
                actual=self._compute_actual(event),
                level=LEVEL_MAP.get(event.get('log_level')),
                exception=failure.value if failure is not None else None,
            )
            self._collector(entry)

    def _compute_actual(self, event: LogEvent) -> Any:
        if callable(self.attributes):
            return self.attributes(event)
        values = tuple(f(event) if callable(f) else event.get(f) for f in self.attributes)
        return values[0] if len(values) == 1 else values

    def install(self, collector: Callable[[Entry], None]) -> None:
        self._collector = collector
        self._original_observers = globalLogPublisher._observers
        globalLogPublisher._observers = [self]

    def uninstall(self) -> None:
        if self._original_observers is not None:
            globalLogPublisher._observers = self._original_observers
            self._original_observers = None


DEFAULT_FIELDS = ('log_level', formatEvent)


class LogCapture(_LogCapture):
    """
    A helper for capturing stuff logged using Twisted's loggers.

    :param fields:
      A sequence of field names that :meth:`~testfixtures.LogCapture.check` will use to build
      "actual" events to compare against the expected events passed in.
      If items are strings, they will be treated as keys info the Twisted logging event.
      If they are callable, they will be called with the event as their only parameter.
      If only one field is specified, "actual" events will just be that one field;
      otherwise they will be a tuple of the specified fields.
    """

    def __init__(
            self,
            attributes: Sequence[str | Callable] | Callable = ('log_level', formatEvent),
            install: bool = False
    ) -> None:
        super().__init__(TwistedSource(attributes), install=install)

    @property
    def events(self) -> list[LogEvent]:
        """The list of raw Twisted log events captured."""
        return [e.raw for e in self.entries]

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
    def make(cls, testcase: TestCase, attributes: Sequence[str | Callable] | Callable = DEFAULT_ATTRIBUTES) -> Self:
        """
        Instantiate, install and add a cleanup for a :class:`LogCapture`.

        :param testcase: This must be an instance of :class:`twisted.trial.unittest.TestCase`.

        Any other parameters are passed directly to the :class:`LogCapture` constructor.

        :return: The :class:`LogCapture` instantiated by this method.
        """
        capture = cls(attributes)
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
