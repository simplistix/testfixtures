import sys
from dataclasses import dataclass
from typing import Callable, Generic, Sequence, cast, get_args, get_origin

from testfixtures.compat import TypeVar
from testfixtures.comparison import compare
from testfixtures.logcapture import LogCapture, LoggingSource
from testfixtures.mock import Mock, _Call as Call
from testfixtures.outputcapture import OutputCapture
from testfixtures.replace import Replacer


@dataclass
class CheckResult:
    """
    The result of a single check for one of the :class:`AbstractResult` attributes.
    Failure is indicated by providing a :attr:`message`.
    """

    #: The name of this check
    name: str
    #: The message describing why this check failed, or ``None`` if it passed.
    message: str | None


@dataclass
class AbstractResult:
    """
    A base class used for implementing the result of calling :meth:`Command.run`.
    """

    #: The :class:`~testfixtures.OutputCapture` that was active during the run.
    output: OutputCapture
    #: The return code derived from any :class:`SystemExit` raised during the run,
    #: or ``0`` if none was raised.
    return_code: int
    #: The :class:`~testfixtures.LogCapture` that was active during the run.
    logging: LogCapture
    #: The mocks used during the run.
    mocks: Mock

    def assert_check_results(self, *checks: CheckResult) -> None:
        """
        Accumulate output from the supplied :class:`CheckResult` instances and raise an
        :class:`AssertionError` if any of them failed.
        """
        __tracebackhide__ = True
        problems = [f"{check.name}: {check.message}" for check in checks if check.message]
        if problems:
            raise AssertionError('\n\n'.join(problems))


def check_return_code(expected: int, actual: int) -> CheckResult:
    """
    Check if the expected return code matches the actual one from a :meth:`~Command.run`.
    Used in the default :meth:`Result.check`.
    """
    return CheckResult('return_code', compare(expected=expected, actual=actual, raises=False))


def check_output(expected: str, output: OutputCapture) -> CheckResult:
    """
    Check if the expected output matches the combined output written to :data:`~sys.stdout` and
    :data:`~sys.stderr` during a :meth:`~Command.run`.
    Used in the default :meth:`Result.check`.
    """
    return CheckResult('output', output.compare(expected, raises=False))


def check_logging(expected: Sequence[tuple[str, ...]| str], logging: LogCapture) -> CheckResult:
    """
    Check if the expected logging matches that :meth:`captured <Command.logging>` during a
    :meth:`~Command.run`.
    Used in the default :meth:`Result.check`.
    """
    return CheckResult('logging', logging.check(*expected, raises=False))


def check_mock_calls(expected: Sequence[Call], mocks: Mock) -> CheckResult:
    """
    Check if the expected mock calls match those :meth:`captured <Command.mocks>` during a
    :meth:`~Command.run`.
    Used in the default :meth:`Result.check`.
    """
    return CheckResult('mock calls', compare(expected, actual=mocks.mock_calls, raises=False))


class Result(AbstractResult):
    """
    The result of a single :meth:`Command.run`.
    """

    def check(
        self,
        output: str = '',
        return_code: int = 0,
        logging: Sequence[tuple[str, str]] = (),
        mock_calls: Sequence[Call] = (),
    ) -> None:
        """
        Check the result of a :meth:`Command.run`.

        :param output: Expected output written to either :data:`~sys.stdout` or :data:`~sys.stderr`.

        :param return_code: Expected return code.

        :param logging: Expected log entries to be :meth:`checked <testfixtures.LogCapture.check>`.

        :param mock_calls: Expected :attr:`~unittest.mock.Mock.mock_calls`.
        """
        __tracebackhide__ = True
        self.assert_check_results(
            check_output(output, self.output),
            check_return_code(return_code, self.return_code),
            check_logging(logging, self.logging),
            check_mock_calls(mock_calls, self.mocks),
        )


ResultT = TypeVar('ResultT', bound=AbstractResult, default=Result)


@dataclass
class Command(Generic[ResultT]):
    """
    A test harness for running an entry-point or script callable with various mocks in place.
    These mocks provide a synthetic :data:`sys.argv`, capture output written to
    :data:`~sys.stdout` or :data:`~sys.stderr`, capture logging, and capture
    any setup calls that have been mocked along with any :class:`SystemExit` raised.
    """

    #: The entry-point or script callable to run.
    main: Callable[[], None]

    def _resolve_result_type(self) -> type[ResultT]:
        for base in getattr(type(self), '__orig_bases__', ()):
            if get_origin(base) is Command:
                arg = get_args(base)[0]
                if isinstance(arg, type):
                    return arg
        return cast(type[ResultT], Result)

    def output(self) -> OutputCapture:
        """
        Instantiate the :class:`~testfixtures.OutputCapture` used for each run.
        Can be overriden to make different capturing choices, such as not capturing at all
        or capturing :data:`~sys.stdout` or :data:`~sys.stderr` separately.
        """
        return OutputCapture()

    def logging(self) -> LogCapture:
        """
        Instantiate the :class:`~testfixtures.LogCapture` used for each run.
        Can be overriden to only capture logging at or above a certain level or if a different
        logging framework is in use, such as :mod:`loguru` or :mod:`structlog`.
        """
        return LogCapture(LoggingSource())

    def mocks(self, replace: Replacer) -> Mock:
        """
        Use the provided :class:`~testfixtures.Replacer` to mock any required callables or objects,
        either where they would interfere with testing of the callable, or where you want to check
        that things are called with appropriate options given the command line specified in
        :data:`sys.argv`.

        Any mocks installed should be attributes of a root :class:`unittest.mock.Mock` instance,
        with that root mock being returned for later :meth:`checking <Result.check>`.
        """
        return Mock()

    def run(self, *argv: str) -> ResultT:
        """
        Run :attr:`main` with :data:`sys.argv` set to
        ``[main.__name__, *argv]`` with :meth:`output` and :meth:`logging` captured and
        :meth:`mocks` in place.

        Any :class:`SystemExit` raised by ``main`` is translated to
        :attr:`AbstractResult.return_code` as follows:

        - :class:`int` codes are passed through.
        - :class:`str` codes are printed to stderr and reported as ``1``
        - A bare :class:`SystemExit` is reported as ``1``.

        """
        with (
            Replacer() as replace,
            self.output() as output,
            self.logging() as logging,
        ):
            mocks = self.mocks(replace)
            replace(
                sys.argv,
                container=sys,
                name='argv',
                replacement=[getattr(self.main, '__name__', 'main')] + list(argv),
            )
            return_code = 0
            try:
                self.main()
            except SystemExit as e:
                match e.code:
                    case str():
                        print(e.code, file=sys.stderr)
                        return_code = 1
                    case int():
                        return_code = e.code
                    case None:
                        return_code = 1
        return self._resolve_result_type()(output, return_code, logging, mocks)

    def __call__(self, *argv: str) -> ResultT:
        """
        Alternative way of calling :meth:`run`.
        """
        return self.run(*argv)
