import logging
import sys
from argparse import ArgumentParser
from dataclasses import dataclass
from functools import partial
from typing import assert_type, Sequence
from testfixtures.mock import Mock, call, _Call as Call

import pytest

from testfixtures import (
    LogCapture,
    LoggingSource,
    OutputCapture,
    Replacer,
    ShouldAssert,
    compare,
)
from testfixtures.command import (
    AbstractRun,
    CheckResult,
    Command,
    Run as DefaultRun,
    check_logging,
    check_mock_calls,
    check_return_code,
)


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
    from loguru import logger as loguru_logger
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
    assert_type(result, DefaultRun)
    assert isinstance(result, DefaultRun)
    # check run type
    result = Command(sample_main_minimal).run()
    assert_type(result, DefaultRun)
    assert isinstance(result, DefaultRun)


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
    class SplitOutput(DefaultRun):
        @classmethod
        def setup_output(cls) -> OutputCapture:
            return OutputCapture(separate=True)

    def main() -> None:
        raise SystemExit("foo!")

    result = Command(main, runner=SplitOutput)()
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
        'output: \n--- expected\n+++ actual\n@@ -1,3 +1,3 @@\n line 1\n line 2\n-line X\n+line 3'
    ):
        Command(main)().check(output="line 1\nline 2\nline X")


class KeepWhitespaceRun(DefaultRun):
    @classmethod
    def setup_output(cls) -> OutputCapture:
        return OutputCapture(strip_whitespace=False)


def test_multi_line_output_strict_matches() -> None:
    def main() -> None:
        print("line 1")
        print("line 2")

    Command(main, runner=KeepWhitespaceRun)().check(output="line 1\nline 2\n")


def test_multi_line_output_strict_fails() -> None:
    def main() -> None:
        print("line 1")
        print("line 2")

    with ShouldAssert('output: \n--- expected\n+++ actual\n@@ -1,2 +1,3 @@\n line 1\n line 2\n+'):
        Command(main, runner=KeepWhitespaceRun)().check(output="line 1\nline 2")


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
    class MockingResult(DefaultRun):
        @classmethod
        def setup_mocks(cls, replace: Replacer) -> Mock:
            mock = Mock()
            replace.in_module(setup_logging, mock.setup_logging)
            return mock

    Command(sample_main_logging, runner=MockingResult).run('-l', '10').check(
        logging=[
            ('INFO', "argv: ['sample_main_logging', '-l', '10']"),
        ],
        mock_calls=[call.setup_logging(10)],
    )


def test_systemexit_none() -> None:
    def main() -> None:
        raise SystemExit()

    result = Command(main)()
    compare(result.return_code, expected=1)


def test_callable_without_name() -> None:
    Command(partial(check_argv_first))()


def test_loguru_logging() -> None:
    pytest.importorskip("loguru")
    from testfixtures.loguru import LoguruSource

    class LoguruRun(DefaultRun):
        @classmethod
        def setup_logging(cls) -> LogCapture:
            return LogCapture(LoguruSource())

    Command(sample_main_loguru, runner=LoguruRun)().check(
        logging=[('INFO', 'hello loguru')],
    )


def test_click() -> None:
    click = pytest.importorskip("click")

    @click.command()
    @click.option('--name', default='world')
    def sample_click(name: str) -> None:
        click.echo(f'hello {name}')

    Command(sample_click).run('--name', 'chris').check(output='hello chris')


def test_argparse() -> None:
    Command(sample_argparse_main).run('--name', 'chris').check(output='hello chris')


def test_customise_by_overriding_setup_and_check() -> None:
    @dataclass
    class Run(AbstractRun):
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
            self.check_results(
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

    command = Command(sample_main, runner=Run)

    # happy path:
    result = command('0', str(logging.WARNING))
    result.check(stdout='stdout', stderr='stderr')

    # check typing for call:
    assert_type(result, Run)
    assert isinstance(result, Run)

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
    assert_type(result, Run)
    assert isinstance(result, Run)


def test_customise_checking_by_changing_check_defaults() -> None:
    @dataclass
    class Run(DefaultRun):
        @classmethod
        def setup_mocks(cls, replace: Replacer) -> Mock:
            mocks = Mock()
            replace.in_module(setup_logging, mocks.setup_logging)
            return mocks

        def check(
            self,
            output: str = 'default output',
            return_code: int = 1,
            logging: Sequence[tuple[str, str]] = (('INFO', 'default logging'),),
            mock_calls: Sequence[Call] = (call.setup_logging(logging.WARNING),),
        ) -> None:
            return super().check(output, return_code, logging, mock_calls)

    def sample_main() -> None:
        setup_logging(int(sys.argv[2]))
        print('default', file=sys.stdout, end=' ')
        print('output', file=sys.stderr)
        logging.info('default logging')
        sys.exit(int(sys.argv[1]))

    Command(sample_main, runner=Run).run('1', str(logging.WARNING)).check()


def test_customise_by_overriding_check_methods() -> None:
    @dataclass
    class Run(DefaultRun):
        @classmethod
        def setup_mocks(cls, replace: Replacer) -> Mock:
            mocks = Mock()
            replace.in_module(setup_logging, mocks.setup_logging)
            return mocks

        @classmethod
        def setup_output(cls) -> OutputCapture:
            return OutputCapture(separate=True)

        @staticmethod
        def check_output(expected: str, output: OutputCapture) -> CheckResult:
            return CheckResult('output', output.compare(stdout=expected, stderr='', raises=False))

        @staticmethod
        def check_return_code(expected: int, return_code: int) -> CheckResult:
            return check_return_code(expected, actual=return_code + 10)

        @staticmethod
        def check_logging(
                expected: Sequence[tuple[str, ...] | str], logging: LogCapture
        ) -> CheckResult:
            return check_logging((('INFO', 'command starting'),) + tuple(expected), logging)

        @staticmethod
        def check_mock_calls(expected: Sequence[Call], mocks: Mock) -> CheckResult:
            return check_mock_calls([call.setup_logging(logging.INFO), *expected], mocks)

    def sample_main() -> None:
        setup_logging(logging.INFO)
        logging.info('command starting')
        print('some output')
        sys.exit(int(sys.argv[1]))

    command = Command(sample_main, runner=Run)
    result = command('42', str(logging.WARNING))
    result.check(output='some output', return_code=52)
