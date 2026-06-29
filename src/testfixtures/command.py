"""
Tools for testing entry-point scripts.
"""
import sys
from dataclasses import dataclass
from typing import Callable, Generic, Sequence, Self

from testfixtures.compat import TypeVar
from testfixtures.comparing import compare
from testfixtures.logcapture import LogCapture, LoggingSource
from testfixtures.mock import Mock, _Call as Call
from testfixtures.outputcapture import OutputCapture
from testfixtures.replace import Replacer


@dataclass
class CheckResult:
    """
    The result of a single check for one of the :class:`AbstractRun` attributes.
    Failure is indicated by providing a :attr:`message`.
    """

    #: The name of this check
    name: str
    #: The message describing why this check failed, or ``None`` if it passed.
    message: str | None


def check_output(expected: str, output: OutputCapture) -> CheckResult:
    """
    Check if the expected output matches the combined output written to :data:`~sys.stdout` and
    :data:`~sys.stderr` during a :meth:`~Command.run`.
    Used in the default :meth:`Run.check`.
    """
    return CheckResult('output', output.compare(expected, raises=False))


def check_logging(expected: Sequence[tuple[str, ...] | str], logging: LogCapture) -> CheckResult:
    """
    Check if the expected logging matches that :attr:`captured <AbstractRun.logging>` during a
    :meth:`~Command.run`.
    Used in the default :meth:`Run.check`.
    """
    return CheckResult('logging', logging.check(*expected, raises=False))


def check_mock_calls(expected: Sequence[Call], mocks: Mock) -> CheckResult:
    """
    Check if the expected mock calls match those :attr:`captured <AbstractRun.mocks>` during a
    :meth:`~Command.run`.
    Used in the default :meth:`Run.check`.
    """
    return CheckResult('mock calls', compare(expected, actual=mocks.mock_calls, raises=False))


def check_return_code(expected: int, actual: int) -> CheckResult:
    """
    Check if the expected return code matches the actual one from a :meth:`~Command.run`.
    Used in the default :meth:`Run.check`.
    """
    return CheckResult('return_code', compare(expected=expected, actual=actual, raises=False))


@dataclass
class AbstractRun:
    """
    A base class used for implementing a :meth:`Command.run` and its result.
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

    @classmethod
    def setup_output(cls) -> OutputCapture:
        """
        Instantiate the :class:`~testfixtures.OutputCapture` used for each run.
        Can be overriden to make different capturing choices, such as not capturing at all
        or capturing :data:`~sys.stdout` or :data:`~sys.stderr` separately.
        """
        return OutputCapture()

    @classmethod
    def setup_logging(cls) -> LogCapture:
        """
        Instantiate the :class:`~testfixtures.LogCapture` used for each run.
        Can be overriden to only capture logging at or above a certain level or if a different
        logging framework is in use, such as :mod:`loguru` or :mod:`structlog`.
        """
        return LogCapture(LoggingSource())

    @classmethod
    def setup_mocks(cls, replace: Replacer) -> Mock:
        """
        Use the provided :class:`~testfixtures.Replacer` to mock any required callables or objects,
        either where they would interfere with testing of the callable, or where you want to check
        that things are called with appropriate options given the command line specified in
        :data:`sys.argv`.

        Any mocks installed should be attributes of a root :class:`unittest.mock.Mock` instance,
        with that root mock being returned for later :meth:`checking <Run.check>`.
        """
        return Mock()

    @staticmethod
    def check_output(expected: str, output: OutputCapture) -> CheckResult:
        """
        Override to customise the checking of :attr:`output`.
        """
        return check_output(expected, output)

    @staticmethod
    def check_return_code(expected: int, actual: int) -> CheckResult:
        """
        Override to customise the checking of :attr:`return_code`.
        """
        return check_return_code(expected, actual)

    @staticmethod
    def check_logging(
        expected: Sequence[tuple[str, ...] | str], logging: LogCapture
    ) -> CheckResult:
        """
        Override to customise the checking of :attr:`logging`.
        """
        return check_logging(expected, logging)

    @staticmethod
    def check_mock_calls(expected: Sequence[Call], mocks: Mock) -> CheckResult:
        """
        Override to customise the checking of calls on :attr:`mocks`.
        """
        return check_mock_calls(expected, mocks)

    @classmethod
    def produce(cls, main: Callable[[], None], argv: list[str]) -> Self:
        """
        Produce a :class:`run <AbstractRun>` by setting up all required mocking and capturing
        and then calling the supplied ``main`` with :data:`sys.argv` set to the supplied ``argv``.
        """
        with (
            Replacer() as replace,
            cls.setup_output() as output,
            cls.setup_logging() as logging,
        ):
            mocks = cls.setup_mocks(replace)
            replace(
                sys.argv,
                container=sys,
                name='argv',
                replacement=[getattr(main, '__name__', 'main')] + argv,
            )
            return_code = 0
            try:
                main()
            except SystemExit as e:
                match e.code:
                    case str():
                        print(e.code, file=sys.stderr)
                        return_code = 1
                    case int():
                        return_code = e.code
                    case None:
                        return_code = 1
        return cls(output, return_code, logging, mocks)

    def check_results(self, *checks: CheckResult) -> None:
        """
        Accumulate output from the supplied :class:`CheckResult` instances and raise an
        :class:`AssertionError` if any of them failed.
        """
        __tracebackhide__ = True
        problems = [f"{check.name}: {check.message}" for check in checks if check.message]
        if problems:
            raise AssertionError('\n\n'.join(problems))


class Run(AbstractRun):
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
        self.check_results(
            self.check_output(output, self.output),
            self.check_return_code(return_code, self.return_code),
            self.check_logging(logging, self.logging),
            self.check_mock_calls(mock_calls, self.mocks),
        )


RunT = TypeVar('RunT', bound=AbstractRun, default=Run)


@dataclass
class Command(Generic[RunT]):
    """
    A test harness for running an entry-point or script callable with various mocks in place.
    These mocks provide a synthetic :data:`sys.argv`, capture output written to
    :data:`~sys.stdout` or :data:`~sys.stderr`, capture logging, and capture
    any setup calls that have been mocked along with any :class:`SystemExit` raised.
    """

    #: The entry-point or script callable to run.
    main: Callable[[], None]
    #: The :class:`runner <AbstractRun>` to use.
    runner: type[RunT] = Run  # type: ignore[assignment]

    def run(self, *argv: str) -> RunT:
        """
        Run :attr:`main` with :data:`sys.argv` set to
        ``[main.__name__, *argv]`` with :meth:`~AbstractRun.setup_output` and
        :meth:`~AbstractRun.setup_logging` captured and
        :meth:`~AbstractRun.setup_mocks` in place.

        Any :class:`SystemExit` raised by ``main`` is translated to
        :attr:`AbstractRun.return_code` as follows:

        - :class:`int` codes are passed through.
        - :class:`str` codes are printed to stderr and reported as ``1``
        - A bare :class:`SystemExit` is reported as ``1``.

        """
        return self.runner.produce(self.main, list(argv))

    def __call__(self, *argv: str) -> RunT:
        """
        Alternative way of calling :meth:`run`.
        """
        return self.run(*argv)
