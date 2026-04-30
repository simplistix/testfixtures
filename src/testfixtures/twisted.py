"""
Tools for helping to test Twisted applications.
"""
from typing import Sequence, Callable, Any, Self, TypeAlias

from constantly import NamedConstant
from twisted.logger import globalLogPublisher, formatEvent, LogLevel, ILogObserver, LogEvent
from twisted.trial.unittest import TestCase

from . import compare
from .logcapture import Entry, LogCapture as _LogCapture, build_actual_extractor, AttributeSpec
import zope.interface


LEVEL_MAP: dict[NamedConstant, int] = {
    LogLevel.debug: 10,
    LogLevel.info: 20,
    LogLevel.warn: 30,
    LogLevel.error: 40,
    LogLevel.critical: 50,
}

LEVEL_NAME_MAP: dict[str, int] = {level.name: numeric for level, numeric in LEVEL_MAP.items()}


def level_name(event: LogEvent) -> str:
    return event['log_level'].name.upper()

LogEventAttributes: TypeAlias = AttributeSpec[LogEvent]

@zope.interface.implementer(ILogObserver)
class TwistedSource:
    """
    A :class:`~testfixtures.logcapture.CaptureSource` for Twisted log events,
    for use with :class:`~testfixtures.LogCapture`.

    On :meth:`~testfixtures.logcapture.CaptureSource.install` all existing observers on
    ``twisted.logger.globalLogPublisher`` are replaced with this source; on
    :meth:`~testfixtures.logcapture.CaptureSource.uninstall` the original observers are
    restored.

    :param attributes:
        The sequence of attributes to return for each :class:`!LogEvent` or a callable that extracts
        :attr:`~testfixtures.logcapture.Entry.actual` from a record.

        If a sequence of attribute names is passed, for each item, a key of that name will
        be obtained from the :class:`!LogEvent`. If the key is missing, ``None`` will be used in its
        place.

        If a callable is passed, it will be called with the :class:`!LogEvent` and the
        value returned will be used as :attr:`~testfixtures.logcapture.Entry.actual`.

    :param level:
        The minimum log level to capture.
        Accepts an :class:`int`, a Twisted :class:`!LogLevel` constant, or a level name
        string such as ``'warn'``. The module-level constants :data:`DEBUG`, :data:`INFO`,
        :data:`WARN`, :data:`ERROR`, :data:`CRITICAL` can also be used.

        Defaults to ``0`` (capture everything).
    """

    def __init__(
        self,
        attributes: LogEventAttributes = (level_name, formatEvent),
        level: int | str | NamedConstant = 0,
    ) -> None:
        self.attributes = attributes
        if isinstance(level, str):
            self.level: int = LEVEL_NAME_MAP[level.lower()]
        elif isinstance(level, int):
            self.level = level
        else:
            self.level = LEVEL_MAP[level]
        self._collector: Callable[[Entry], None] | None = None
        self._original_observers: list | None = None
        self._compute_actual = build_actual_extractor(attributes, self.extract_field)

    def extract_field(self, raw: LogEvent, attribute: str) -> Any:
        return raw.get(attribute)

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

    def install(self, collector: Callable[[Entry], None]) -> None:
        self._collector = collector
        self._original_observers = globalLogPublisher._observers
        globalLogPublisher._observers = [self]

    def uninstall(self) -> None:
        if self._original_observers is not None:
            globalLogPublisher._observers = self._original_observers
            self._original_observers = None


DEFAULT_ATTRIBUTES = ('log_level', formatEvent)


class LogCapture(_LogCapture):
    """
    A helper for capturing stuff logged using Twisted's loggers.

    :param fields:
        The sequence of fields to return for each :class:`!LogEvent` or a callable that extracts
        :attr:`~testfixtures.logcapture.Entry.actual` from a record.

        If a sequence of attribute names is passed, for each item, a key of that name will
        be obtained from the :class:`!LogEvent`. If the key is missing, ``None`` will be used in its
        place.

        If a callable is passed, it will be called with the :class:`!LogEvent` and the
        value returned will be used as :attr:`~testfixtures.logcapture.Entry.actual`.
    """

    def __init__(
            self,
            fields: LogEventAttributes = DEFAULT_ATTRIBUTES,
            install: bool = False
    ) -> None:
        super().__init__(TwistedSource(fields), install=install)

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
    def make(
            cls,
            testcase: TestCase,
            fields: LogEventAttributes = DEFAULT_ATTRIBUTES
    ) -> Self:
        """
        Instantiate, install and add a cleanup for a :class:`LogCapture`.

        :param testcase: This must be an instance of :class:`twisted.trial.unittest.TestCase`.

        Any other parameters are passed directly to the :class:`LogCapture` constructor.

        :return: The :class:`LogCapture` instantiated by this method.
        """
        capture = cls(fields)
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
