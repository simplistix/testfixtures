from doctest import REPORT_NDIFF, ELLIPSIS

from sybil import Sybil, DocTestParser, CodeBlockParser, parse_captures
from sybil.parsers.doctest import FIX_BYTE_UNICODE_REPR

from testfixtures.sybil import FileParser

pytest_collect_file = Sybil(
    parsers=[
        DocTestParser(optionflags=REPORT_NDIFF|ELLIPSIS|FIX_BYTE_UNICODE_REPR),
        CodeBlockParser(['print_function']),
        parse_captures,
        FileParser('tempdir'),
    ],
    pattern='*.txt',
).pytest()
