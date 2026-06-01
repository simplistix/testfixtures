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

The default :meth:`~testfixtures.command.Command.logging` hook installs a
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
subclass :class:`Command` and override the :meth:`~testfixtures.command.Command.logging`
hook:

__ https://github.com/Delgan/loguru

.. code-block:: python

  from loguru import logger
  from testfixtures import Command, LogCapture
  from testfixtures.loguru import LoguruSource

  class LoguruCommand(Command):
      def logging(self) -> LogCapture:
          return LogCapture(LoguruSource())

  def main() -> None:
      logger.info('hello loguru')

  LoguruCommand(main).run().check(logging=[('INFO', 'hello loguru')])

Mocking collaborators
---------------------

The :meth:`~testfixtures.command.Command.mocks` hook is given the :class:`~testfixtures.Replacer` that is
already active for the duration of the run; install whatever
replacements you need and return them so :meth:`~testfixtures.command.Result.check` can
assert their ``mock_calls``. The sample function ``tests.sample1.z``
stands in for any collaborator you might want to replace:

.. code-block:: python

  from unittest.mock import Mock, call
  from testfixtures import Command, Replacer
  from tests import sample1

  class MyCommand(Command):
      def mocks(self, replace: Replacer) -> Mock:
          mock = Mock(return_value='mocked z')
          replace.in_module(sample1.z, mock)
          return mock

  def main() -> None:
      print(sample1.z())

  MyCommand(main).run().check(
      output='mocked z',
      mock_calls=[call()],
  )

Splitting stdout and stderr
---------------------------

The default :meth:`~testfixtures.command.Command.output` hook captures stdout and stderr
into a single combined stream — :meth:`~testfixtures.command.Result.check` asserts that
combined stream with its ``output`` argument. When you need to assert
them separately, override :meth:`~testfixtures.command.Command.output` to return an
:class:`~testfixtures.OutputCapture` with ``separate=True``, define an
:class:`~testfixtures.command.AbstractResult` subclass whose ``check`` accepts
``stdout`` and ``stderr``, then specialise ``Command`` to that subclass
via the generic parameter:

.. code-block:: python

  import sys
  from dataclasses import dataclass
  from testfixtures import Command, OutputCapture, compare
  from testfixtures.command import AbstractResult, CheckResult, check_return_code

  @dataclass
  class SeparateResult(AbstractResult):
      def check(self, stdout: str = '', stderr: str = '', return_code: int = 0) -> None:
          __tracebackhide__ = True
          self.assert_check_results(
              CheckResult('output', self.output.compare(stdout=stdout, stderr=stderr, raises=False)),
              check_return_code(return_code, self.return_code),
          )

  class SeparateCommand(Command[SeparateResult]):
      def output(self) -> OutputCapture:
          return OutputCapture(separate=True)

  def main() -> None:
      print('on stdout')
      print('on stderr', file=sys.stderr)

  SeparateCommand(main).run().check(
      stdout='on stdout',
      stderr='on stderr',
  )
