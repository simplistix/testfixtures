"""
Tools for helping to test applications that use Loguru.
"""
from typing import TYPE_CHECKING, Callable, Any, TypeAlias
from warnings import warn

from loguru import logger

from .logcapture import Entry, build_actual_extractor, AttributeSpec

if TYPE_CHECKING:
    from loguru import Record, Message
else:
    Record = dict

RecordAttributes: TypeAlias = AttributeSpec[Record]


def level_name(record: Record) -> str:
    return record['level'].name


class LoguruSource:
    """
    A :class:`~testfixtures.logcapture.CaptureSource` for
    `loguru <https://github.com/Delgan/loguru>`_ log records,
    for use with :class:`~testfixtures.LogCapture`.

    On :meth:`~testfixtures.logcapture.CaptureSource.install` all existing loguru handlers
    are removed and replaced with a single capture handler; on
    :meth:`~testfixtures.logcapture.CaptureSource.uninstall` the original handlers are restored.

    :param attributes: Controls the :attr:`~testfixtures.logcapture.Entry.actual` value stored
        for each entry.  May be a sequence whose elements are either a string key into the
        loguru record dict or a callable that receives the record dict and returns a value;
        or a single callable that receives the record dict and returns the full value directly.
        If only one element is given the value is stored directly; otherwise a tuple is stored.
        Defaults to ``(level_name, 'message')``, producing ``('INFO', 'the message')`` tuples.
    :param level: Minimum log level to capture, forwarded to ``logger.add``.  Defaults to
        ``0`` (capture everything).

    Additional keyword arguments are forwarded to ``logger.add``.
    """

    def __init__(
        self,
        attributes: RecordAttributes = (level_name, 'message'),
        level: int | str = 0,
        **kw: Any,
    ) -> None:
        self.attributes = attributes
        self._kw: dict[str, Any] = {'level': level, 'colorize': False, 'catch': False, **kw}
        self._collector: Callable[[Entry], None] | None = None
        self._id: int | None = None
        self._original_handlers: dict | None = None
        self._original_min_level: int | None = None
        self._compute_actual = build_actual_extractor(attributes, self.extract_field)

    def extract_field(self, raw: Record, attribute: str) -> Any:
        return raw.get(attribute)

    def write(self, message: 'Message') -> None:
        if self._collector is not None:
            record = message.record
            exc_info = record['exception']
            entry = Entry(
                raw=record,
                actual=self._compute_actual(record),
                level=record['level'].no,
                exception=exc_info.value if exc_info is not None else None,
            )
            self._collector(entry)

    def stop(self) -> None:
        if self._collector is not None:
            warn(
                'LoguruSource left installed at shutdown.\n'
                'Call uninstall() or use LogCapture as a context manager.'
            )

    def __repr__(self) -> str:
        return 'LoguruSource()'

    def install(self, collector: Callable[[Entry], None]) -> None:
        core = logger._core  # type: ignore[attr-defined]
        self._collector = collector
        self._original_handlers = dict(core.handlers)
        self._original_min_level = core.min_level
        core.handlers = {}  # hide existing sinks, don't stop them
        self._id = logger.add(self, format="{message}", **self._kw)

    def uninstall(self) -> None:
        if self._original_handlers is not None:
            self._collector = None  # suppress the shutdown warning from stop()
            core = logger._core  # type: ignore[attr-defined]
            if self._id in core.handlers:
                logger.remove(self._id)  # stop only the capture handler
            core.min_level = self._original_min_level
            core.handlers = self._original_handlers  # restore live sinks
            self._original_handlers = None
            self._id = None
