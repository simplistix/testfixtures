"""
Tools for helping to test applications that use Loguru.
"""
from typing import Sequence, Callable, Any
from warnings import warn

from loguru import logger

from .logcapture import Entry, build_actual_extractor


def level_name(record: dict) -> str:
    return record['level'].name


class LoguruSource:
    """
    A capture source for loguru log records, for use with :class:`~testfixtures.LogCapture`.

    :param fields:
      A sequence of field names (keys into the loguru record dict) or callables to extract
      from each record to form the ``actual`` value stored in
      :class:`~testfixtures.logcapture.Entry`. If a single field is specified, the actual
      value is that field directly; otherwise it is a tuple.

    :param level: The minimum log level to capture (passed to ``logger.add``).

    Additional keyword arguments are forwarded to ``logger.add``.
    """

    def __init__(
        self,
        attributes: Sequence[str | Callable] | Callable = (level_name, 'message'),
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

    def extract_field(self, raw: dict, attribute: str) -> Any:
        return raw.get(attribute)

    def write(self, message: Any) -> None:
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
