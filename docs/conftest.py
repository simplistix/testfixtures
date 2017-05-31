from doctest import REPORT_NDIFF, ELLIPSIS

from sybil import Sybil
from sybil.parsers.doctest import DocTestParser, FIX_BYTE_UNICODE_REPR
from sybil.parsers.codeblock import CodeBlockParser
from sybil.parsers.capture import parse_captures

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
