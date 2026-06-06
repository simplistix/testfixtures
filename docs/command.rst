Testing command-line entry points
=================================

.. currentmodule:: testfixtures.command

When the unit under test is a ``main`` function — the kind of callable
you'd register as a console script — the things you usually want to
assert about it are a mix of process-level concerns: what it printed,
what it logged, what exit code it returned, and which collaborators it
called. :class:`Command` wraps your callable in :class:`~testfixtures.OutputCapture`,
:class:`~testfixtures.LogCapture` and :class:`~testfixtures.Replacer`, runs it with a
:any:`sys.argv` of your choosing, and hands back a :class:`Result` you
can make a single combined assertion against with
:meth:`~testfixtures.command.Result.check`.

Minimal example
---------------

A ``main`` that prints a line and exits cleanly:

.. code-block:: python

  from testfixtures import Command

  def main() -> None:
      print('hello world')

  Command(main).run().check(output='hello world')

If the call needs argv, pass it to :meth:`~testfixtures.command.Command.run`:

.. code-block:: python

  import sys
  from testfixtures import Command

  def main() -> None:
      print(f'hello {sys.argv[1]}')

  Command(main).run('chris').check(output='hello chris')

A non-zero exit
---------------

:class:`SystemExit` is caught and translated: ``int`` codes pass
through to :attr:`~testfixtures.command.AbstractResult.return_code`, ``str`` codes are printed to
stderr and reported as ``1``, and a bare :class:`SystemExit` is
reported as ``1``:

.. code-block:: python

  import sys
  from testfixtures import Command

  def main() -> None:
      print('looking good', file=sys.stderr)
      sys.exit(2)

  Command(main).run().check(output='looking good', return_code=2)

Asserting logging
-----------------

The default :meth:`~testfixtures.command.AbstractResult.setup_logging` hook installs a
:class:`~testfixtures.LogCapture` for the standard-library :mod:`logging` module.
Expected entries can be passed straight to :meth:`~testfixtures.command.Result.check`:

.. code-block:: python

  import logging
  from testfixtures import Command

  def main() -> None:
      logging.info('starting up')

  Command(main).run().check(
      logging=[('INFO', 'starting up')],
  )

To capture a different logging source — `loguru`__ for example —
subclass :class:`Result` and override
:meth:`~testfixtures.command.AbstractResult.setup_logging`, then pass the subclass as
``result_type``:

__ https://github.com/Delgan/loguru

.. code-block:: python

  from loguru import logger
  from testfixtures import Command, LogCapture, Run
  from testfixtures.loguru import LoguruSource

  class LoguruRun(Run):
      @classmethod
      def setup_logging(cls) -> LogCapture:
          return LogCapture(LoguruSource())

  def main() -> None:
      logger.info('hello loguru')

  Command(main, runner=LoguruRun).run().check(
      logging=[('INFO', 'hello loguru')],
  )

Mocking collaborators
---------------------

:meth:`~testfixtures.command.AbstractResult.setup_mocks` is given the
:class:`~testfixtures.Replacer` that is already active for the duration of the run;
install whatever replacements you need on a root :class:`~unittest.mock.Mock`
and return that root so :meth:`~testfixtures.command.Result.check` can assert their
``mock_calls``. The sample function ``tests.sample1.z`` stands in for any
collaborator you might want to replace:

.. code-block:: python

  from unittest.mock import Mock, call
  from testfixtures import Command, Replacer, Run
  from tests import sample1

  class MockedZResult(Run):
      @classmethod
      def setup_mocks(cls, replace: Replacer) -> Mock:
          mock = Mock(return_value='mocked z')
          replace.in_module(sample1.z, mock)
          return mock

  def main() -> None:
      print(sample1.z())

  Command(main, runner=MockedZResult).run().check(
      output='mocked z',
      mock_calls=[call()],
  )

Reusing a customised result
---------------------------

When several tests share the same custom :class:`Result` but exercise
different ``main`` callables, a one-line helper function keeps the
boilerplate down and the wiring obvious at every call site. Reusing
the ``MockedZResult`` from above:

.. code-block:: python

  from typing import Callable
  from testfixtures import Command

  def mocked_z(main: Callable[[], None]) -> Command[MockedZResult]:
      return Command(main, runner=MockedZResult)

  def main_one() -> None:
      print(f'one: {sample1.z()}')

  def main_two() -> None:
      print(f'two: {sample1.z()}')

  mocked_z(main_one).run().check(output='one: mocked z', mock_calls=[call()])
  mocked_z(main_two).run().check(output='two: mocked z', mock_calls=[call()])

The same approach works for any pattern of customisation — split
stdout/stderr, a particular ``LogCapture`` configuration, a standard
set of mocks. Define the :class:`Result` subclass once, define a thin
helper that binds it, and tests across the codebase compose by passing
their ``main`` callable.

Splitting stdout and stderr
---------------------------

The default :meth:`~testfixtures.command.AbstractResult.setup_output` hook captures stdout
and stderr into a single combined stream — :meth:`~testfixtures.command.Result.check`
asserts that combined stream with its ``output`` argument. When you need to
assert them separately, subclass :class:`AbstractResult` and override
:meth:`~testfixtures.command.AbstractResult.setup_output` to return an
:class:`~testfixtures.OutputCapture` with ``separate=True``, then implement a
``check`` whose signature takes ``stdout`` and ``stderr``:

.. code-block:: python

  import sys
  from dataclasses import dataclass
  from testfixtures import Command, OutputCapture
  from testfixtures.command import AbstractRun, CheckResult, check_return_code

  @dataclass
  class SeparateResult(AbstractRun):
      @classmethod
      def setup_output(cls) -> OutputCapture:
          return OutputCapture(separate=True)

      def check(self, stdout: str = '', stderr: str = '', return_code: int = 0) -> None:
          __tracebackhide__ = True
          self.check_results(
              CheckResult('output', self.output.compare(stdout=stdout, stderr=stderr, raises=False)),
              check_return_code(return_code, self.return_code),
          )

  def main() -> None:
      print('on stdout')
      print('on stderr', file=sys.stderr)

  Command(main, runner=SeparateResult).run().check(
      stdout='on stdout',
      stderr='on stderr',
  )
