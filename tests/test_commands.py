import logging
import sys
from argparse import ArgumentParser
from dataclasses import dataclass
from functools import partial
from typing import assert_type
from testfixtures.mock import Mock, call

import click
import pytest
from loguru import logger as loguru_logger

from testfixtures import (
    LogCapture,
    LoggingSource,
    OutputCapture,
    Replacer,
    ShouldAssert,
    compare,
)
from testfixtures.command import (
    AbstractResult,
    CheckResult,
    Command,
    Result as DefaultResult,
    check_logging,
    check_mock_calls,
    check_return_code,
)
from testfixtures.loguru import LoguruSource


def sample_main_minimal() -> None:
    pass


def sample_main_streams() -> None:
    return_code = int(sys.argv[1])
    print('stdout 1', file=sys.stdout)
    print('stderr 1', file=sys.stderr)
    print('stdout 2', file=sys.stdout)
    print('stderr 2', file=sys.stderr)
    sys.exit(return_code)


def setup_logging(level: int) -> None: ...


def sample_main_logging() -> None:
    parser = ArgumentParser()
    parser.add_argument('-l', '--log-level', type=int)
    args, _ = parser.parse_known_args()
    setup_logging(args.log_level)
    logging.info(f'argv: {sys.argv!r}')


def sample_main_loguru() -> None:
    loguru_logger.info('hello loguru')


def sample_argparse_main() -> None:
    parser = ArgumentParser(prog='sample_argparse_main')
    parser.add_argument('--name', default='world')
    args = parser.parse_args()
    print(f'hello {args.name}')


def check_argv_first() -> None:
    compare(sys.argv[0], expected='main')


def test_minimal_success() -> None:
    Command(sample_main_minimal)().check()


def test_result_typing() -> None:
    result = Command(sample_main_minimal)()
    # check __call__ type
    assert_type(result, DefaultResult)
    assert isinstance(result, DefaultResult)
    # check run type
    result = Command(sample_main_minimal).run()
    assert_type(result, DefaultResult)
    assert isinstance(result, DefaultResult)


def test_output_matches() -> None:
    def main() -> None:
        print("hello")

    Command(main)().check("hello")


def test_output_fails() -> None:
    def main() -> None:
        print("hello")

    with ShouldAssert("output: 'goodbye' (expected) != 'hello' (actual)"):
        Command(main)().check("goodbye")


def test_text_systemexit() -> None:
    class SplitResult(DefaultResult):
        @classmethod
        def setup_output(cls) -> OutputCapture:
            return OutputCapture(separate=True)

    def main() -> None:
        raise SystemExit("foo!")

    result = Command(main, result_type=SplitResult)()
    result.output.compare(stdout="", stderr="foo!")
    compare(result.return_code, expected=1)


def test_multi_line_output_matches() -> None:
    def main() -> None:
        print("line 1")
        print("line 2")
        print("line 3")

    Command(main)().check(output="line 1\nline 2\nline 3")


def test_multi_line_output_fails() -> None:
    def main() -> None:
        print("line 1")
        print("line 2")
        print("line 3")

    with ShouldAssert(
        'output: \n'
        '--- expected\n'
        '+++ actual\n'
        '@@ -1,3 +1,3 @@\n'
        ' line 1\n'
        ' line 2\n'
        '-line X\n'
        '+line 3'
    ):
        Command(main)().check(output="line 1\nline 2\nline X")


class StrictResult(DefaultResult):
    @classmethod
    def setup_output(cls) -> OutputCapture:
        return OutputCapture(strip_whitespace=False)


def test_multi_line_output_strict_matches() -> None:
    def main() -> None:
        print("line 1")
        print("line 2")

    Command(main, result_type=StrictResult)().check(output="line 1\nline 2\n")


def test_multi_line_output_strict_fails() -> None:
    def main() -> None:
        print("line 1")
        print("line 2")

    with ShouldAssert(
        'output: \n'
        '--- expected\n'
        '+++ actual\n'
        '@@ -1,2 +1,3 @@\n'
        ' line 1\n'
        ' line 2\n'
        '+'
    ):
        Command(main, result_type=StrictResult)().check(output="line 1\nline 2")


def test_return_code_failure() -> None:
    runner = Command(sample_main_streams)
    with ShouldAssert(
        'output: \n'
        '--- expected\n'
        '+++ actual\n'
        '@@ -1 +1,4 @@\n'
        '-\n'
        '+stdout 1\n'
        '+stderr 1\n'
        '+stdout 2\n'
        '+stderr 2\n\n'
        'return_code: 0 (expected) != 1 (actual)'
    ):
        runner.run('1').check()


def test_everything_failure() -> None:
    runner = Command(sample_main_streams)
    with ShouldAssert(
        'output: \n'
        '--- expected\n'
        '+++ actual\n'
        '@@ -1 +1,4 @@\n'
        '-nope\n'
        '+stdout 1\n'
        '+stderr 1\n'
        '+stdout 2\n'
        '+stderr 2\n\n'
        'return_code: 2 (expected) != 1 (actual)'
    ):
        runner.run('1').check(return_code=2, output='nope')


def test_non_zero_return_code_expected() -> None:
    runner = Command(sample_main_streams)
    with ShouldAssert(
        'output: \n'
        '--- expected\n'
        '+++ actual\n'
        '@@ -1 +1,4 @@\n'
        '-\n'
        '+stdout 1\n'
        '+stderr 1\n'
        '+stdout 2\n'
        '+stderr 2'
    ):
        runner.run('1').check(return_code=1)


def test_stdlib_logging() -> None:
    Command(sample_main_logging).run('-l', '0').check(
        logging=[
            ('INFO', "argv: ['sample_main_logging', '-l', '0']"),
        ]
    )


def test_capture_setup_logging_call() -> None:
    class MockingResult(DefaultResult):
        @classmethod
        def setup_mocks(cls, replace: Replacer) -> Mock:
            mock = Mock()
            replace.in_module(setup_logging, mock)
            return mock

    Command(sample_main_logging, result_type=MockingResult).run('-l', '10').check(
        logging=[
            ('INFO', "argv: ['sample_main_logging', '-l', '10']"),
        ],
        mock_calls=[call(10)],
    )


def test_systemexit_none() -> None:
    def main() -> None:
        raise SystemExit()

    result = Command(main)()
    compare(result.return_code, expected=1)


def test_callable_without_name() -> None:
    Command(partial(check_argv_first))()


def test_loguru_logging() -> None:
    class LoguruResult(DefaultResult):
        @classmethod
        def setup_logging(cls) -> LogCapture:
            return LogCapture(LoguruSource())

    Command(sample_main_loguru, result_type=LoguruResult)().check(
        logging=[('INFO', 'hello loguru')],
    )


def test_click() -> None:
    pytest.importorskip("click")

    @click.command()
    @click.option('--name', default='world')
    def sample_click(name: str) -> None:
        click.echo(f'hello {name}')

    Command(sample_click).run('--name', 'chris').check(output='hello chris')


def test_argparse() -> None:
    Command(sample_argparse_main).run('--name', 'chris').check(output='hello chris')


def test_maximal_override() -> None:
    @dataclass
    class Result(AbstractResult):
        @classmethod
        def setup_output(cls) -> OutputCapture:
            return OutputCapture(separate=True)

        @classmethod
        def setup_logging(cls) -> LogCapture:
            return LogCapture(LoggingSource('getMessage', level=logging.WARNING))

        @classmethod
        def setup_mocks(cls, replace: Replacer) -> Mock:
            mocks = Mock()
            replace.in_module(setup_logging, mocks.setup_logging)
            return mocks

        def check(
            self,
            stdout: str = '',
            stderr: str = '',
            return_code: int = 0,
        ) -> None:
            output = self.output.compare(stdout=stdout, stderr=stderr, raises=False)
            self.assert_check_results(
                CheckResult('output', output),
                check_return_code(return_code, self.return_code),
                check_logging(['warning message'], self.logging),
                check_mock_calls([call.setup_logging(logging.WARNING)], self.mocks),
            )

    def sample_main() -> None:
        setup_logging(int(sys.argv[2]))
        print('stdout', file=sys.stdout)
        print('stderr', file=sys.stderr)
        logging.info('info message')
        logging.warning('warning message')
        sys.exit(int(sys.argv[1]))

    command = Command(sample_main, result_type=Result)
    # happy path:
    result = command('0', str(logging.WARNING))
    result.check(stdout='stdout', stderr='stderr')

    # check typing for call:
    assert_type(result, Result)
    assert isinstance(result, Result)

    # sad path:
    result = command.run('1', str(logging.INFO))
    with ShouldAssert(
        'output: dict not as expected:\n\n'
        'values differ:\n'
        "'stderr': '' (expected) != 'stderr' (actual)\n"
        "'stdout': '' (expected) != 'stdout' (actual)\n\n"
        "While comparing ['stderr']: '' (expected) != 'stderr' (actual)\n\n"
        "While comparing ['stdout']: '' (expected) != 'stdout' (actual)\n\n"
        'return_code: 0 (expected) != 1 (actual)\n\n'
        'mock calls: sequence not as expected:\n\n'
        'same:\n'
        '[]\n\n'
        'expected:\n'
        '[call.setup_logging(30)]\n\n'
        'actual:\n'
        '[call.setup_logging(20)]\n\n'
        'While comparing [0]: \n'
        "'call.setup_logging(30)' (expected)\n"
        '!=\n'
        "'call.setup_logging(20)' (actual)"
    ):
        result.check()

    # check typing for run:
    assert_type(result, Result)
    assert isinstance(result, Result)
