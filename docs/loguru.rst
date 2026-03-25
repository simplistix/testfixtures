Testing with Loguru
===================

.. note::

   To ensure you are using compatible versions, install with the ``testfixtures[loguru]`` extra.

.. invisible-code-block: python

    try:
        import loguru
    except ImportError:
        loguru = None

.. skip: start if(loguru is None, reason="No loguru installed")

`Loguru <https://github.com/Delgan/loguru>`_ provides a streamlined logging API through a single
global :class:`~loguru._logger.Logger` object.
:class:`~testfixtures.loguru.LoguruSource` is provided to capture and test using
:class:`~testfixtures.LogCapture`.

As a simple example, you can capture loguru output with a `pytest`__ fixture such as this:

__ https://docs.pytest.org/

.. code-block:: python

  import pytest
  from testfixtures import LogCapture
  from testfixtures.loguru import LoguruSource

  @pytest.fixture()
  def logs():
      with LogCapture(LoguruSource()) as logs_:
          yield logs_

You can then check logging in your tests like this:

.. code-block:: python

  from loguru import logger

  def test_logging(logs: LogCapture) -> None:
      logger.info('42 is fine')
      logger.error('13 is not')
      logs.check(
          ('INFO', '42 is fine'),
          ('ERROR', '13 is not'),
      )

See :doc:`logging` for the full :class:`~testfixtures.LogCapture` API, including
:meth:`~testfixtures.LogCapture.check`, :meth:`~testfixtures.LogCapture.check_present`,
:meth:`~testfixtures.LogCapture.actual`, and the :attr:`~testfixtures.LogCapture.entries`
attribute.

Inspecting raw records
----------------------

Each :class:`~testfixtures.logcapture.Entry` in :attr:`~testfixtures.LogCapture.entries`
exposes the underlying loguru :ref:`record dict <loguru:record>` via its ``raw`` attribute:

.. code-block:: python

  from testfixtures import LogCapture
  from testfixtures.loguru import LoguruSource

  with LogCapture(LoguruSource()) as log:
      logger.info('hello world')

>>> log.entries[0].raw
{..., 'level': (name='INFO', ..., 'message': 'hello world', ...}

The loguru :ref:`record dict <loguru:record>` contains rich contextual information.

Checking logging context
------------------------

Loguru supports structured context via :meth:`~loguru._logger.Logger.bind`, which creates a
logger with fixed extra fields, and :meth:`~loguru._logger.Logger.contextualize`, which
temporarily adds context for all logging within a block. Both are exposed through the ``extra``
key in the record dict.

To capture ``extra`` alongside the default level and message, include it in the ``attributes``:

.. code-block:: python

    from testfixtures.loguru import LoguruSource, level_name

    request_log = logger.bind(request_id='abc123')

    with LogCapture(LoguruSource((level_name, 'message', 'extra'))) as log:
        request_log.info('handling request')
        request_log.info('request complete')

    log.check(
        ('INFO', 'handling request', {'request_id': 'abc123'}),
        ('INFO', 'request complete', {'request_id': 'abc123'}),
    )

:meth:`~loguru._logger.Logger.contextualize` works the same way but scopes the context to a
``with`` block, affecting all loggers:

.. code-block:: python

    with LogCapture(LoguruSource((level_name, 'message', 'extra'))) as log:
        logger.info('before task')
        with logger.contextualize(task_id=1234):
            logger.info('processing task')
        logger.info('after task')

    log.check(
        ('INFO', 'before task', {}),
        ('INFO', 'processing task', {'task_id': 1234}),
        ('INFO', 'after task', {})
    )

Capturing specific fields
-------------------------

You can control which fields form the ``actual`` value by passing sequence of ``attributes`` to
:class:`~testfixtures.loguru.LoguruSource`. Elements may be string keys into the
:ref:`record dict <loguru:record>` or callables that receive the :ref:`record dict <loguru:record>`.

To capture only the message:

.. code-block:: python

    with LogCapture(LoguruSource('message')) as log:
        logger.info('just the message')
    log.check('just the message')

You can also mix string keys and callables:

.. code-block:: python

    with LogCapture(LoguruSource((lambda r: r['level'].name, 'message'))) as log:
        logger.debug('a debug message')
        logger.info('something info')
    log.check(
        ('DEBUG', 'a debug message'),
        ('INFO', 'something info'),
    )

For full control, pass a single callable:

.. code-block:: python

    def extract(record):
        return {'level': record['level'].name, 'message': record['message']}

    with LogCapture(LoguruSource(extract)) as log:
        logger.debug('a debug message')
        logger.error('an error')
    log.check(
        {'level': 'DEBUG', 'message': 'a debug message'},
        {'level': 'ERROR', 'message': 'an error'},
    )

Filtering by level
------------------

To capture only messages at or above a minimum level:

.. code-block:: python

    with LogCapture(LoguruSource(level='WARNING')) as log:
        logger.info('ignored')
        logger.warning('captured')
    log.check(('WARNING', 'captured'))

Combining with standard library logging
---------------------------------------

If your application uses both loguru and the standard library's :mod:`logging`,
pass both a :class:`~testfixtures.LoggingSource` and a
:class:`~testfixtures.loguru.LoguruSource` to one :class:`~testfixtures.LogCapture`
to capture and check both:

.. code-block:: python

    import logging
    from testfixtures import LogCapture, LoggingSource
    from testfixtures.loguru import LoguruSource

    with LogCapture(LoggingSource(), LoguruSource()) as log:
        logging.warning('from standard library logging')
        logger.warning('from loguru')

    log.check(
        ('WARNING', 'from standard library logging'),
        ('WARNING', 'from loguru'),
    )

Exceptions
----------

When code logs an exception, the underlying exception object is stored in
:attr:`~testfixtures.logcapture.Entry`'s ``exception`` attribute:

.. code-block:: python

    from testfixtures import LogCapture, compare
    from testfixtures.loguru import LoguruSource

    with LogCapture(LoguruSource()) as logs:
        try:
            raise ValueError('boom')
        except ValueError:
            logger.exception('oh no')

    compare(logs.entries[-1].exception, expected=ValueError('boom'))

Checking the configuration of your log sinks
---------------------------------------------

:class:`~testfixtures.loguru.LoguruSource` is good for checking that your code is logging
the correct messages; just as important is checking that your application has correctly
configured loguru :ref:`sinks <loguru:sink>`. If you have a ``setup_logging`` function such as this:

.. code-block:: python

    import sys
    from loguru import logger

    def setup_logging(level: str = 'INFO') -> None:
        logger.remove()
        logger.add(sys.stderr, level=level, format='{level} {message}')

This can be tested with a unit test such as the following:

.. code-block:: python

    import logging
    import sys
    from loguru._handler import Handler as LoguruHandler
    from loguru._simple_sinks import StreamSink
    from testfixtures import Replacer, compare, like

    def test_setup_logging() -> None:
        with Replacer() as replace:
            replace(logger._core.handlers, {}, container=logger._core, name='handlers')
            setup_logging(level='WARNING')
            handlers = list(logger._core.handlers.values())
            compare(
                handlers,
                expected=[
                    like(
                        LoguruHandler,
                        levelno=logging.WARNING,
                        _sink=like(StreamSink, _stream=sys.stderr),
                    )
                ],
            )
            compare(handlers[0]._formatter.strip(), expected='{level} {message}\n{exception}')

.. check it:

   >>> test_setup_logging()
