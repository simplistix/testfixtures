Testing logging
===============

.. currentmodule:: testfixtures

Logging is important and testing that your logging is correct should be as easy as possible.
:class:`LogCapture` allows this for standard library :mod:`logging`,
:doc:`loguru <loguru>` and :doc:`twisted <twisted>` logging.
Support for other frameworks is easy to implement by way of the
:class:`~testfixtures.logcapture.CaptureSource` protocol.

If you want to test that your logging has been correctly configured,
see :ref:`check-log-config`.

As a simple example, you can capture logging with a `pytest`__ fixture such as this:

__ https://docs.pytest.org/

.. code-block:: python

  import pytest
  from typing import Iterator
  from testfixtures import LogCapture, LoggingSource

  @pytest.fixture()
  def logs() -> Iterator[LogCapture]:
      with LogCapture(LoggingSource()) as logs_:
          yield logs_

You can check that the code you're testing logs correctly like this:

.. code-block:: python

  import logging

  def test_logging(logs: LogCapture) -> None:
      # code under test
      logging.info('%i is fine', 42)
      logging.error('%s is not', 13)
      logs.check(
          ('INFO', '42 is fine'),
          ('ERROR', '13 is not'),
      )


.. invisible-code-block: python

  from sybil.testing import run_pytest
  run_pytest(test_logging, fixtures=[logs])

Checking captured log messages
------------------------------

There are three ways of checking that the messages captured were as expected.
The following example is used to show these:

.. code-block:: python

  from testfixtures import LogCapture, LoggingSource
  from logging import getLogger
  logger = getLogger()

  with LogCapture(LoggingSource()) as log:
      logger.info('start of block number %i', 1)
      try:
          logger.debug('inside try block')
          raise RuntimeError('No code to run!')
      except:
          logger.error('error occurred', exc_info=True)

The check methods
~~~~~~~~~~~~~~~~~

:obj:`~testfixtures.LogCapture` instances have :meth:`~testfixtures.LogCapture.check`
and :meth:`~testfixtures.LogCapture.check_present` methods to make assertions about
entries that have been logged.

:meth:`~testfixtures.LogCapture.check` will compare the captured logging with what you expect:

>>> log.check(
...     ('INFO', 'start of block number 1'),
...     ('DEBUG', 'inside try block'),
...     ('ERROR', 'error occurred'),
... )


If the actual entries logged were different, you'll get an :class:`AssertionError`:

>>> log.check(('INFO', 'start of block number 1'))
Traceback (most recent call last):
 ...
AssertionError: sequence not as expected:
<BLANKLINE>
same:
(('INFO', 'start of block number 1'),)
<BLANKLINE>
expected:
()
<BLANKLINE>
actual:
(('DEBUG', 'inside try block'), ('ERROR', 'error occurred'))

In contrast, :meth:`~testfixtures.LogCapture.check_present` will only check that the entries you
specify are present, and that their order is as specified. Other entries will be ignored:

>>> log.check_present(
...     ('INFO', 'start of block number 1'),
...     ('ERROR', 'error occurred'),
... )

If the order of entries is non-deterministic, then you can be explicit that the order doesn't
matter:

>>> log.check_present(
...     ('ERROR', 'error occurred'),
...     ('INFO', 'start of block number 1'),
...     order_matters=False
... )

Similarly, if the order of entries is non-deterministic, but you want to ensure there is
no unexpected logging, :meth:`~testfixtures.LogCapture.check` also support ``order_matters``:

>>> log.check(
...     ('DEBUG', 'inside try block'),
...     ('INFO', 'start of block number 1'),
...     ('ERROR', 'error occurred'),
...     order_matters=False
... )

Inspecting
~~~~~~~~~~

:obj:`~testfixtures.LogCapture` instances also keep a list of the
:class:`entries <testfixtures.logcapture.Entry>` they capture. This is useful when
you want to check specifics of the captured logging that aren't
available from either the string representation or the
:meth:`~testfixtures.LogCapture.check` method.

A common case of this is where you want to check that exception
information was logged for certain messages:

.. code-block:: python

  from testfixtures import compare

  compare(log.entries[-1].exception, expected=RuntimeError('No code to run!'))

If you need access to the raw object captured from the logging framework:

>>> log.entries[0].raw
<LogRecord: root, 20, ..., "start of block number %i">

If you want to access the items considered by the check methods, then use
:meth:`~testfixtures.LogCapture.actual`:

>>> from pprint import pprint
>>> pprint(log.actual())
[('INFO', 'start of block number 1'),
 ('DEBUG', 'inside try block'),
 ('ERROR', 'error occurred')]

Printing
~~~~~~~~

:obj:`~testfixtures.LogCapture` instances have a string representation that
shows what entries it has captured. This can be useful in doc tests:

>>> print(log)
INFO start of block number 1
DEBUG inside try block
ERROR error occurred

This representation can also be used to check that no logging has
occurred:

>>> empty = LogCapture()
>>> print(empty)
No logging captured

Only capturing specific logging
-------------------------------

You can capture only logging above a certain level like this:

.. code-block:: python

    with LogCapture(LoggingSource(level=logging.WARNING)) as logs:
        logger = getLogger()
        logger.debug('junk')
        logger.info('something we care about')
        logger.error('an error')

    logs.check(
        ('ERROR', 'an error'),
    )

To only capture a specific logger:

.. code-block:: python

    with LogCapture(LoggingSource(names=['specific'])) as logs:
        getLogger('something').info('junk')
        getLogger('specific').info('what we care about')
        getLogger().info('more junk')

    logs.check(
        ('INFO', 'what we care about'),
    )

To capture multiple loggers:

.. code-block:: python

    with LogCapture(LoggingSource(names=('one', 'two'))) as logs:
        getLogger('three').info('3')
        getLogger('two').info('2')
        getLogger('one').info('1')

    logs.check(
        ('INFO', '2'),
        ('INFO', '1'),
    )

Capturing can also be disabled and enabled during a test by only having the
:class:`~testfixtures.LogCapture` installed when necessary:

>>> logger = logging.getLogger()
>>> logs = LogCapture(LoggingSource(), install=False)

>>> logger.info('junk')
>>> logs.install()
>>> logger.info('something we care about')
>>> logs.uninstall()
>>> logger.info('more junk')

>>> logs.check(('INFO', 'something we care about'))

You can also capture different attributes by specifying their names; if the attribute is
callable, as with ``getMessage`` here, it will be called:

.. code-block:: python

    logger = getLogger()

    with LogCapture(LoggingSource(attributes=('name', 'levelname', 'getMessage'))) as logs:
        logger.debug('a debug message')
        logger.info('something %s', 'info')
        logger.error('an error')

    logs.check(
        ('root', 'DEBUG', 'a debug message'),
        ('root', 'INFO', 'something info'),
        ('root', 'ERROR', 'an error'),
    )

If you need even more control, you can pass a callable to extract the required information:

.. code-block:: python

    def extract(record):
        return {'level': record.levelname, 'message': record.getMessage()}

    with LogCapture(attributes=extract) as log:
        logger = getLogger()
        logger.debug('a debug message')
        logger.error('an error')
    log.check(
        {'level': 'DEBUG', 'message': 'a debug message'},
        {'level': 'ERROR', 'message': 'an error'},
    )

Methods of capture
------------------

There are three different ways of having a :class:`LogCapture` installed while your code
under test is running:

The context manager
~~~~~~~~~~~~~~~~~~~

The context manager can be used as follows:

.. code-block:: python

    import logging
    from testfixtures import LogCapture, LoggingSource

    logger = logging.getLogger()

    with LogCapture(LoggingSource()) as logs:
        logger.info('a message')
        logger.error('an error')

For the duration of the ``with`` block, logging is captured. If it doesn't match expectations
then an :class:`AssertionError` will be raised:

>>> logs.check(
...     ('INFO', 'a message'),
...     ('ERROR', 'another error'),
... )
Traceback (most recent call last):
 ...
AssertionError: sequence not as expected:
<BLANKLINE>
same:
(('INFO', 'a message'),)
<BLANKLINE>
expected:
(('ERROR', 'another error'),)
<BLANKLINE>
actual:
(('ERROR', 'an error'),)

The decorator
~~~~~~~~~~~~~

To capture logging for a particular test function:

.. code-block:: python

  from testfixtures import log_capture

  @log_capture()
  def test_function(capture):
      logger = logging.getLogger()
      logger.info('a message')
      logger.error('an error')

      capture.check(
          ('root', 'INFO', 'a message'),
          ('root', 'ERROR', 'an error'),
      )

.. check the above raises no assertion error:

  >>> test_function()


.. note::
    This method is not compatible with pytest's fixture discovery stuff.

Manual usage
~~~~~~~~~~~~

You can also manually instantiate, install and uninstall a :class:`~testfixtures.LogCapture`:

>>> from testfixtures import LogCapture, LoggingSource
>>> logs = LogCapture(LoggingSource(), install=False)

When you want to start capturing, :meth:`~LogCapture.install` the capture:

>>> logs.install()

You can then execute code that will log the events you want to test:

>>> from logging import getLogger
>>> getLogger().info('a message')

At any point, you can check what has been logged using the
check method:

>>> logs.check(('INFO', 'a message'))

Alternatively, you can use the string representation of the
:class:`~testfixtures.LogCapture`:

>>> print(logs)
INFO a message

When you're done capturing:

>>> logs.uninstall()

The :meth:`~testfixtures.LogCapture.uninstall` method can also be added as an
:meth:`~unittest.TestCase.addCleanup` if that is easier or more compact in your test
suite.

If you have multiple :class:`~testfixtures.LogCapture` objects in use,
you can easily uninstall them all:

>>> LogCapture.uninstall_all()

.. _check-log-config:

Testing logging configuration
-----------------------------

:class:`LogCapture` is good for checking that your code is logging the
correct messages; just as important is checking that your application
has correctly configured log handlers. If you have a ``setup_logging`` function such as this:

.. code-block:: python

    def setup_logging(level: int = logging.INFO) -> None:
        # Our logging configuration code, in this case just a
        # call to basicConfig:
        logging.basicConfig(
            format='%(levelname)s %(message)s',
            level=level,
            force=True,
        )

This can be tested with a unit test such as the following:

.. code-block:: python

    from testfixtures import Replacer, compare, like
    import logging
    import sys

    logger = logging.getLogger()

    def test_setup_logging() -> None:
        with Replacer() as replace:
            # We mock out the handlers list for the logger we're
            # configuring in such a way that we have no handlers
            # configured at the start of the test and the handlers our
            # configuration installs are removed at the end of the test.
            replace(logger.handlers, [], container=logger, name='handlers')
            replace(logger.level, 0, container=logger, name='level')

            setup_logging(level=logging.WARNING)

            compare(logger.level, expected=logging.WARNING)
            compare(
                logger.handlers,
                expected=[
                    like(
                        logging.StreamHandler,
                        stream = sys.stderr,
                        formatter = like(
                            logging.Formatter,
                            _fmt = '%(levelname)s %(message)s'
                        ),
                        level=logging.NOTSET
                    )
                ]
            )
      

.. check it:

   >>> test_setup_logging()
