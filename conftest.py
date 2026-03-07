from doctest import REPORT_NDIFF, ELLIPSIS
from typing import Any

try:
    from sybil import Sybil
except ImportError:
    pass
else:
    from sybil.parsers.doctest import DocTestParser
    from sybil.parsers.codeblock import PythonCodeBlockParser
    from sybil.parsers.capture import parse_captures
    from sybil.parsers.skip import skip

    from testfixtures import TempDirectory
    from testfixtures.sybil import FileParser


    def sybil_setup(namespace: dict[str, Any]) -> None:
        # _tempdir is in case it's overwritten by a test.
        namespace['tempdir'] = namespace['_tempdir'] = TempDirectory()


    def sybil_teardown(namespace: dict[str, Any]) -> None:
        namespace['_tempdir'].cleanup()


    pytest_collect_file = Sybil(
        parsers=[
            DocTestParser(optionflags=REPORT_NDIFF|ELLIPSIS),
            PythonCodeBlockParser(),
            parse_captures,
            FileParser('tempdir'),
            skip,
        ],
        patterns=['*.rst', '*.py'],
        setup=sybil_setup, teardown=sybil_teardown,
        fixtures=['tmp_path'],
        exclude='tests/*.py'
    ).pytest()
