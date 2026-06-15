Testing command-line scripts
============================

.. invisible-code-block: python

    try:
        import loguru
    except ImportError:
        loguru = None
    try:
        import click
    except ImportError:
        click = None

.. currentmodule:: testfixtures.command

Command line scripts always parse :data:`sys.argv` and exit with an integer return code.
Along the way, they often configurate loggers and other services, log their progress or send it to
a stream such :data:`~sys.stderr` or :data:`~sys.stdout`.

This often involves testing boilerplate which needs to vary slightly across projects, but which
has some intricacies that are easy to miss. :class:`Command` aims to make this testing easy and
flexible.

Take a simple :class:`~argparse.ArgumentParser` script:

.. code-block:: python

    from argparse import ArgumentParser

    def main() -> None:
        parser = ArgumentParser()
        parser.add_argument('message')
        args = parser.parse_args()
        print(f"Your message: {args.message}")


This can be tested as follows:

>>> from testfixtures import Command
>>> Command(main).run('my message').check(output='Your message: my message')

We can also test what happens if the required argument is not provided. The program name
:mod:`argparse` puts in its messages varies with how the tests are run, so we use a
:class:`~testfixtures.TextComparison` to match it:

>>> from testfixtures import TextComparison as S
>>> Command(main).run().check(
...     output=S(
...         r'usage: .+ \[-h\] message\n'
...         r'.+: error: the following arguments are required: message'
...     ),
...     return_code=2,
... )

.. skip: start if(click is None, reason="No click installed")

If we now implement our entrypoint with Click instead:

.. code-block:: python

    import click

    @click.command()
    @click.argument('message')
    def main(message: str) -> None:
        click.echo(f"Your message: {message}")

Our test doesn't change:

>>> Command(main).run('my message').check(output='Your message: my message')

.. skip: end

If logging is used instead of :func:`print`:

.. code-block:: python

    from argparse import ArgumentParser
    import logging

    def main() -> None:
        parser = ArgumentParser()
        parser.add_argument('message')
        args = parser.parse_args()
        logging.info(f"Your message: %s", args.message)

Testing is just as simple:

>>> Command(main).run('my message').check(logging=[('INFO', 'Your message: my message')])

Customising setup
-----------------

Most scripts that log instead of print will configure their logging framework and often offer
a way of specifying the log level on the command line:

.. code-block:: python

    from argparse import ArgumentParser
    import logging

    def main() -> None:
        parser = ArgumentParser()
        parser.add_argument('message')
        parser.add_argument('-l', '--log-level', default='INFO')
        args = parser.parse_args()
        logging.basicConfig(level=getattr(logging, args.log_level.upper()))
        logging.info(f"Your message: %s", args.message)

To test this, we can override :meth:`~AbstractRun.setup_mocks` to intercept and record the
configuration call:

.. code-block:: python

    from testfixtures import Run as DefaultRun, Replacer
    from testfixtures.mock import Mock, call

    class Run(DefaultRun):
        @classmethod
        def setup_mocks(cls, replace: Replacer) -> Mock:
            mocks = Mock()
            replace.in_module(logging.basicConfig, mocks.basicConfig)
            return mocks

Now we can check that logging is set up correctly, as well as preventing the configuration call from
getting in the way of the logging capture:

>>> Command(main, Run).run('my message').check(
...    logging=[('INFO', 'Your message: my message')],
...    mock_calls=[call.basicConfig(level=20)],
... )

We can also check that the log level option works as intended:

>>> Command(main, Run).run('-l', 'warning', 'would not be logged').check(
...    logging=[('INFO', 'Your message: would not be logged')],
...    mock_calls=[call.basicConfig(level=30)],
... )

.. skip: start if(loguru is None, reason="No loguru installed")

If we decided to switch to :doc:`loguru <loguru>` for our logging:

.. code-block:: python

    from argparse import ArgumentParser
    from loguru import logger
    import sys

    def main() -> None:
        parser = ArgumentParser()
        parser.add_argument('message')
        parser.add_argument('-l', '--log-level', default='INFO')
        args = parser.parse_args()
        logger.add(sys.stderr, format="{time} {level} {message}", level=args.log_level)
        logger.info(f"Your message: {args.message}")


We can additionally override :meth:`~AbstractRun.setup_logging`:

.. code-block:: python

    from testfixtures import Run as DefaultRun, LogCapture, Replacer, like
    from testfixtures.mock import Mock, call
    from testfixtures.loguru import LoguruSource
    from io import StringIO
    from loguru._logger import Logger

    class Run(DefaultRun):
        @classmethod
        def setup_logging(cls) -> LogCapture:
            return LogCapture(LoguruSource())

        @classmethod
        def setup_mocks(cls, replace: Replacer) -> Mock:
            mocks = Mock()
            replace.on_class(Logger.add, mocks.logger.add)
            return mocks

The checking of logging doesn't change, but the mock calls do:

>>> Command(main, Run).run('my message').check(
...    logging=[('INFO', 'Your message: my message')],
...    mock_calls=[
...        call.logger.add(like(StringIO), format='{time} {level} {message}', level='INFO')
...    ],
... )

.. note::
    The ``like(StringIO)`` is necessary because by the time the script's :meth:`!logger.add` call is
    reached, :class:`Command` has already mocked :data:`sys.stderr` with an
    :class:`~testfixtures.OutputCapture`.

.. skip: end

Customising checks
------------------
If we have a script that always logs a debug message on startup:

.. code-block:: python

    import logging, sys

    def main() -> None:
        logging.debug('starting')
        logging.info(f'action: {sys.argv[1]}')

Our testing can be made more succinct by overriding :meth:`~AbstractRun.check_logging`:

.. code-block:: python

    from collections.abc import Sequence
    from testfixtures import Run as DefaultRun, LogCapture, like
    from testfixtures.command import CheckResult, check_logging

    class Run(DefaultRun):
        @staticmethod
        def check_logging(
                expected: Sequence[tuple[str, ...] | str], logging: LogCapture
        ) -> CheckResult:
            return check_logging((('DEBUG', 'starting'),) + tuple(expected), logging)

Now we only need to specify the action logging in each test:

>>> Command(main, Run).run('wave').check(logging=[('INFO', 'action: wave')])

Similarly, if we have a script that should only ever write to :data:`sys.stdout`:

.. code-block:: python

    import logging, sys

    def main() -> None:
        action = sys.argv[1]
        print(f'action: {action}', file=sys.stderr if action == 'error' else sys.stdout)

We can override both :meth:`~AbstractRun.setup_output` and :meth:`~AbstractRun.check_output`:

.. code-block:: python

    from testfixtures import Run as DefaultRun, OutputCapture, like
    from testfixtures.command import CheckResult, check_logging

    class Run(DefaultRun):
        @classmethod
        def setup_output(cls) -> OutputCapture:
            return OutputCapture(separate=True)

        @staticmethod
        def check_output(expected: str, output: OutputCapture) -> CheckResult:
            return CheckResult(
                'output', output.compare(stdout=expected, stderr='', raises=False)
            )

Now we can check our script as follows:

>>> Command(main, Run).run('wave').check(output='action: wave')

But if there is an error, we will be able to see the output in the failure:

>>> Command(main, Run).run('error').check(output='action: ?')
Traceback (most recent call last):
...
AssertionError: output: dict not as expected:
<BLANKLINE>
values differ:
'stderr': '' (expected) != 'action: error' (actual)
'stdout': 'action: ?' (expected) != '' (actual)
<BLANKLINE>
While comparing ['stderr']:
'' (expected)
!=
'action: error' (actual)
<BLANKLINE>
While comparing ['stdout']: 'action: ?' (expected) != '' (actual)

Customising everything
----------------------

A script or set of scripts may have a well defined approach that doesn't match the default
:meth:`Run.check` signature, such as always allowing the log level to be set, always logging
and never writing to :data:`~sys.stderr` or :data:`~sys.stdout`:

.. skip: start if(click is None or loguru is None, reason="No click or loguru installed")

.. code-block:: python

      import click, sys
      from loguru import logger

      @click.group()
      @click.option(
          "--log-level",
          default="INFO",
          show_default=True,
          type=click.Choice(["DEBUG", "INFO", "ERROR"], case_sensitive=False),
      )
      def cli(log_level):
          logger.remove()
          logger.add(sys.stderr, level=log_level.upper())

      @cli.command()
      def build():
          logger.info("building")

      @cli.command()
      def deploy():
          logger.info("deploying")

For ergonomic testing of this family of commands, in addition to overriding
:meth:`~AbstractRun.setup_logging` and :meth:`~AbstractRun.setup_mocks`, we can also implement
our own :meth:`~Run.check` method:


.. code-block:: python

    from collections.abc import Sequence
    from io import StringIO
    from testfixtures import like, LogCapture, Replacer
    from testfixtures.command import AbstractRun
    from testfixtures.mock import Mock, call
    from testfixtures.loguru import LoguruSource
    from loguru import logger
    from loguru._logger import Logger

    class Run(AbstractRun):
        @classmethod
        def setup_logging(cls) -> LogCapture:
            return LogCapture(LoguruSource())

        @classmethod
        def setup_mocks(cls, replace: Replacer) -> Mock:
            original_remove = Logger.remove
            mocks = Mock()
            def remove(self, handler_id: int = None) -> None:
                # Allow setup_logging to uninstall its handler:
                if handler_id:
                    original_remove(self, handler_id)
                else:
                    mocks.logger.remove()

            replace.on_class(Logger.remove, remove)
            replace.on_class(Logger.add, mocks.logger.add)
            return mocks

        def check(
            self,
            logging: Sequence[tuple[str, str]] = (),
            log_level: str = 'INFO',
            return_code: int = 0,
        ) -> None:
            self.check_results(
                self.check_output(output=self.output, expected=''),
                self.check_return_code(return_code, self.return_code),
                self.check_logging(logging, self.logging),
                self.check_mock_calls(
                    [call.logger.remove(), call.logger.add(like(StringIO), level=log_level)],
                    self.mocks
                ),
            )

    command = Command(cli, runner=Run)

Now out individual tests are succinct and easy to read while still testing their full implementation
on each call:

>>> command.run('build').check(logging=[('INFO', 'building')])
>>> result = command.run('--log-level', 'debug', 'deploy')
>>> result.check(logging=[('INFO', 'deploying')], log_level='DEBUG')

.. skip: end
