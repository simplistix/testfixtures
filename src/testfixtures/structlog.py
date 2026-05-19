"""
Tools for helping to test applications that use structlog.
"""

import logging
import sys
from typing import Any, Callable, Sequence, TypeAlias
from warnings import warn

import structlog
from structlog.exceptions import DropEvent
from structlog.types import EventDict, Processor

from .logcapture import Entry, build_actual_extractor, AttributeSpec

EventDictAttributes: TypeAlias = AttributeSpec[EventDict]


def level_name(event_dict: EventDict) -> str:
    """
    Extract the upper-case level name from a structlog event dict.

    Looks up the ``level`` key (as set by
    :func:`structlog.stdlib.add_log_level`) and returns its upper-case form
    so that captured entries shape the same way as those from
    :class:`~testfixtures.logcapture.LoggingSource` and
    :class:`~testfixtures.loguru.LoguruSource`.
    """
    return str(event_dict.get('level', '')).upper()


def raw(event_dict: EventDict) -> EventDict:
    """
    XXX
    """
    return event_dict


class StructlogSource:
    """
    A :class:`~testfixtures.logcapture.CaptureSource` for
    `structlog <https://www.structlog.org/>`_, for use with
    :class:`~testfixtures.LogCapture`.

    On :meth:`~testfixtures.logcapture.CaptureSource.install`, the current
    structlog configuration is saved via :func:`structlog.get_config` and
    replaced with a chain consisting of
    :func:`structlog.stdlib.add_log_level`, the supplied ``processors``,
    and a capture processor that records each event and stops the chain.
    On :meth:`~testfixtures.logcapture.CaptureSource.uninstall`, the
    saved configuration is restored.

    :param attributes:
        The sequence of attributes to return for each event dict, or a
        callable that extracts :attr:`~testfixtures.logcapture.Entry.actual`
        from the event dict.

        If a sequence is passed, each item may be a string key into the
        event dict or a callable that receives the event dict. Missing
        string keys yield ``None``.

        Defaults to ``(level_name, 'event')``, producing
        ``('INFO', 'hello world')``-shaped tuples.

    :param level:
        Minimum level to capture, as a numeric level or a structlog/stdlib
        level name (case-insensitive). Defaults to ``0`` — capture everything.

    :param processors:
        Extra processors to run before the capture processor. The default
        is ``(structlog.contextvars.merge_contextvars,)`` so that values
        bound via :func:`structlog.contextvars.bind_contextvars` and
        :func:`structlog.contextvars.bound_contextvars` appear in the
        captured event dict. Renderers (``JSONRenderer``,
        ``KeyValueRenderer``, ``ConsoleRenderer``) and noisy processors
        (``TimeStamper``, ``CallsiteParameterAdder``, ``StackInfoRenderer``,
        ``format_exc_info``) are best omitted; ``format_exc_info`` in
        particular would replace ``exc_info`` with a formatted string and
        defeat :attr:`~testfixtures.logcapture.Entry.exception` extraction.
    """

    collector: Callable[[Entry], None] | None = None
    live_processors: list[Processor] | None = None
    saved_processors: list[Processor] | None = None

    def __init__(
        self,
        attributes: EventDictAttributes = (level_name, 'event'),
        level: int | str = 0,
        processors: Sequence[Processor] = (
            structlog.stdlib.add_log_level,
            structlog.contextvars.merge_contextvars,
        ),
    ) -> None:
        self.attributes = attributes
        self.processors: tuple[Processor, ...] = tuple(processors)
        self.min_level = self.resolve_level(level)
        self.compute_actual = build_actual_extractor(attributes, self.extract_field)

    @staticmethod
    def resolve_level(level: int | str) -> int:
        match level:
            case int():
                resolved = level
            case str():
                resolved = logging.getLevelName(level.upper())
                if not isinstance(resolved, int):
                    raise ValueError(f'Unknown structlog level name: {level!r}')
        return resolved

    def extract_field(self, raw: EventDict, attribute: str) -> Any:
        return raw.get(attribute)

    def capture(
        self,
        logger: Any,
        method_name: str,
        event_dict: Any,
    ) -> EventDict:
        if self.collector is None:
            raise DropEvent

        level = self.resolve_level(method_name)
        if level < self.min_level:
            raise DropEvent

        exception: BaseException | None = None
        if isinstance(event_dict, dict):
            exc_info = event_dict.get('exc_info')
            if exc_info is True:
                exc_info = sys.exc_info()
            if isinstance(exc_info, tuple) and len(exc_info) == 3:
                exception = exc_info[1]
            elif isinstance(exc_info, BaseException):
                exception = exc_info

        actual = self.compute_actual(event_dict)

        self.collector(Entry(raw=event_dict, actual=actual, level=level, exception=exception))

        raise DropEvent

    def __repr__(self) -> str:
        return 'StructlogSource()'

    def install(self, collector: Callable[[Entry], None]) -> None:
        self.collector = collector
        # Mutate the configured processors list in place rather than swapping
        # in a new one — loggers bound (or cached) before install() hold a
        # reference to this list, and replacing it would leave them on the
        # old chain. structlog.testing.capture_logs uses the same trick.
        self.live_processors = structlog.get_config()['processors']
        self.saved_processors = list(self.live_processors)
        self.live_processors[:] = [*self.processors, self.capture]
        structlog.configure(processors=self.live_processors)

    def uninstall(self) -> None:
        if self.live_processors is None or self.saved_processors is None:
            return
        live = self.live_processors
        saved = self.saved_processors
        del self.live_processors
        del self.saved_processors
        del self.collector
        current = structlog.get_config()['processors']
        if current is not live or self.capture not in current:
            warn(
                'StructlogSource was displaced from structlog configuration before uninstall.\n'
                'Avoid calling structlog.configure() or structlog.reset_defaults() '
                'inside a LogCapture block.'
            )
            current = live
        current[:] = saved
        structlog.configure(processors=current)
