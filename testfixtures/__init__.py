class singleton:

    def __init__(self, name: str) -> None:
        self.name = name

    def __repr__(self) -> str:
        return '<%s>' % self.name

    __str__ = __repr__


not_there: singleton = singleton('not_there')


from testfixtures.comparison import (
    Comparison, StringComparison, RoundComparison, compare, diff, RangeComparison,
    SequenceComparison, Subset, Permutation, MappingComparison
)
from testfixtures.datetime import mock_datetime, mock_date, mock_time
from testfixtures.logcapture import LogCapture, log_capture
from testfixtures.outputcapture import OutputCapture
from testfixtures.resolve import resolve
from testfixtures.replace import (
    Replacer,
    Replace,
    replace,
    replace_in_environ,
    replace_on_class,
    replace_in_module,
)
from testfixtures.shouldraise import ShouldRaise, should_raise, ShouldAssert
from testfixtures.shouldwarn import ShouldWarn, ShouldNotWarn
from testfixtures.tempdirectory import TempDirectory, tempdir
from testfixtures.utils import wrap, generator


# backwards compatibility for the old names
test_datetime = mock_datetime
test_datetime.__test__ = False  # type: ignore[attr-defined]
test_date = mock_date
test_date.__test__ = False  # type: ignore[attr-defined]
test_time = mock_time
test_time.__test__ = False  # type: ignore[attr-defined]

__all__ = [
    'Comparison',
    'LogCapture',
    'MappingComparison',
    'OutputCapture',
    'Permutation',
    'RangeComparison',
    'Replace',
    'Replacer',
    'RoundComparison',
    'SequenceComparison',
    'ShouldAssert',
    'ShouldRaise',
    'ShouldNotWarn',
    'ShouldWarn',
    'Subset',
    'StringComparison',
    'TempDirectory',
    'compare',
    'diff',
    'generator',
    'log_capture',
    'mock_date',
    'mock_datetime',
    'mock_time',
    'not_there',
    'replace',
    'replace_in_environ',
    'replace_on_class',
    'replace_in_module',
    'resolve',
    'should_raise',
    'singleton',
    'tempdir',
    'test_date',
    'test_datetime',
    'test_time',
    'wrap',
]
