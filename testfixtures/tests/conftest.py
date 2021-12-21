from sybil import Sybil
from sybil.parsers.doctest import  DocTestParser
try:
    from sybil.parsers.codeblock import PythonCodeBlockParser
except ImportError:
    # sybil < 3 has it under the old name
    from sybil.parsers.codeblock import CodeBlockParser as PythonCodeBlockParser
from sybil.parsers.capture import parse_captures

from testfixtures import TempDirectory
from testfixtures.sybil import FileParser


def sybil_setup(namespace):
    namespace['tempdir'] = TempDirectory()


def sybil_teardown(namespace):
    namespace['tempdir'].cleanup()


pytest_collect_file = Sybil(
    parsers=[
        DocTestParser(),
        PythonCodeBlockParser(),
        parse_captures,
        FileParser('tempdir'),
    ],
    pattern='*.txt',
    setup=sybil_setup, teardown=sybil_teardown,
).pytest()
