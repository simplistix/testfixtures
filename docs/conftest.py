from doctest import REPORT_NDIFF, ELLIPSIS

from sybil import Sybil
from sybil.parsers.doctest import DocTestParser
try:
    from sybil.parsers.doctest import FIX_BYTE_UNICODE_REPR
except ImportError:
    # sybil 3 removed the optionflag
    FIX_BYTE_UNICODE_REPR = 0
try:
    from sybil.parsers.codeblock import PythonCodeBlockParser
except ImportError:
    from sybil.parsers.codeblock import CodeBlockParser as PythonCodeBlockParser
from sybil.parsers.capture import parse_captures

from testfixtures.compat import PY3
from testfixtures.sybil import FileParser


if PY3:
    pytest_collect_file = Sybil(
        parsers=[
            DocTestParser(optionflags=REPORT_NDIFF|ELLIPSIS|FIX_BYTE_UNICODE_REPR),
            PythonCodeBlockParser(['print_function']),
            parse_captures,
            FileParser('tempdir'),
        ],
        pattern='*.txt',
    ).pytest()
