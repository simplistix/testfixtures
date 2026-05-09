Testing with Structlog
======================

.. note::

   To ensure you are using compatible versions, install with the ``testfixtures[structlog]`` extra.

.. invisible-code-block: python

    try:
        import structlog
    except ImportError:
        structlog = None

.. skip: start if(structlog is None, reason="No structlog installed")

.. invisible-code-block: python

    structlog.reset_defaults()
    structlog.contextvars.clear_contextvars()

`structlog <https://www.structlog.org/>`_ builds log entries as event dictionaries
that flow through a configurable chain of :doc:`processors <structlog:processors>`.
:class:`~testfixtures.structlog.StructlogSource` is provided to capture and test
these event dictionaries using :class:`~testfixtures.LogCapture`.

If you have ``cache_logger_on_first_use`` enabled and acquire loggers before
:class:`~testfixtures.LogCapture` is installed, those cached loggers will keep their
old processor chain and bypass capture; acquire loggers inside the capture block, or
disable ``cache_logger_on_first_use`` during tests.

.. note::

    Structlog also has its own :doc:`testing tools <structlog:testing>` including the
    :func:`~structlog.testing.capture_logs` context manager and
    :class:`~structlog.testing.LogCapture` processor, which should not be confused with
    :class:`testfixtures.LogCapture`!

As a simple example, you can capture structlog output with a `pytest`__ fixture such as this:

__ https://docs.pytest.org/

.. code-block:: python

  import pytest
  from testfixtures import LogCapture
  from testfixtures.structlog import StructlogSource

  @pytest.fixture()
  def logs():
      with LogCapture(StructlogSource()) as logs_:
          yield logs_

You can then check logging in your tests like this:

.. code-block:: python

  import structlog

  logger = structlog.get_logger()

  def test_logging(logs: LogCapture) -> None:
      logger.info('42 is fine')
      logger.error('13 is not')
      logs.check(
          ('INFO', '42 is fine'),
          ('ERROR', '13 is not'),
      )


.. invisible-code-block: python

  from sybil.testing import run_pytest
  run_pytest(test_logging, fixtures=[logs])

See :doc:`logging` for the full :class:`~testfixtures.LogCapture` API, including
:meth:`~testfixtures.LogCapture.check`, :meth:`~testfixtures.LogCapture.check_present`,
:meth:`~testfixtures.LogCapture.actual`, and the :attr:`~testfixtures.LogCapture.entries`
attribute.

Inspecting raw event dicts
--------------------------

Each :class:`~testfixtures.logcapture.Entry` in :attr:`~testfixtures.LogCapture.entries`
exposes the underlying structlog event dict via its ``raw`` attribute:

.. code-block:: python

  from testfixtures import LogCapture
  from testfixtures.structlog import StructlogSource

  with LogCapture(StructlogSource()) as log:
      structlog.get_logger().info('hello world')

>>> log.entries[0].raw
{'event': 'hello world', 'level': 'info'}

Checking logging context
------------------------

structlog supports two ways of carrying contextual data: per-logger
:meth:`~structlog.BoundLoggerBase.bind`, which returns a new logger with extra
context bound int, and the contextvars-based
:func:`~structlog.contextvars.bind_contextvars` or
:func:`~structlog.contextvars.bound_contextvars`, which carry context across
function calls and async tasks. Both end up as keys at the top level of the
event dict.

To full capture context, use the :func:`~testfixtures.structlog.raw` helper:

.. code-block:: python

    from testfixtures.structlog import StructlogSource, raw

    request_log = structlog.get_logger().bind(request_id='abc123')

    with LogCapture(StructlogSource(raw)) as log:
        request_log.info('handling request')
        request_log.info('request complete')

    log.check(
        {'event': 'handling request', 'level': 'info', 'request_id': 'abc123'},
        {'event': 'request complete', 'level': 'info', 'request_id': 'abc123'},
    )

The contextvars-based API works the same way; it relies on the
:func:`~structlog.contextvars.merge_contextvars` processor, which is included
in :class:`~testfixtures.structlog.StructlogSource`'s default ``processors`` so
that bound context shows up in tests with no extra wiring:

.. code-block:: python

    from structlog.contextvars import bound_contextvars

    with LogCapture(StructlogSource((level_name, 'event', 'task_id'))) as log:
        structlog.get_logger().info('before task')
        with bound_contextvars(task_id=1234):
            structlog.get_logger().info('processing task')
        structlog.get_logger().info('after task')

    log.check(
        ('INFO', 'before task', None),
        ('INFO', 'processing task', 1234),
        ('INFO', 'after task', None),
    )

Capturing specific fields
-------------------------

You can control which fields form the ``actual`` value by passing a sequence of
``attributes`` to :class:`~testfixtures.structlog.StructlogSource`. Elements may
be string keys into the event dict or callables that receive the event dict.

To capture only the event message:

.. code-block:: python

    with LogCapture(StructlogSource('event')) as log:
        structlog.get_logger().info('just the event')
    log.check('just the event')

You can also mix string keys and callables:

.. code-block:: python

    with LogCapture(StructlogSource((lambda d: d['level'].upper(), 'event'))) as log:
        structlog.get_logger().debug('a debug message')
        structlog.get_logger().info('something info')
    log.check(
        ('DEBUG', 'a debug message'),
        ('INFO', 'something info'),
    )

For full control, pass a single callable:

.. code-block:: python

    def extract(event_dict):
        return {'level': event_dict['level'].upper(), 'event': event_dict['event']}

    with LogCapture(StructlogSource(extract)) as log:
        structlog.get_logger().debug('a debug message')
        structlog.get_logger().error('an error')
    log.check(
        {'level': 'DEBUG', 'event': 'a debug message'},
        {'level': 'ERROR', 'event': 'an error'},
    )

Filtering by level
------------------

To capture only messages at or above a minimum level:

.. code-block:: python

    with LogCapture(StructlogSource(level='WARNING')) as log:
        structlog.get_logger().info('ignored')
        structlog.get_logger().warning('captured')
    log.check(('WARNING', 'captured'))

Combining with standard library logging
---------------------------------------

If your application uses both structlog and the standard library's
:mod:`logging`, pass both a :class:`~testfixtures.logcapture.LoggingSource` and
a :class:`~testfixtures.structlog.StructlogSource` to one
:class:`~testfixtures.LogCapture`:

.. code-block:: python

    import logging
    from testfixtures import LogCapture
    from testfixtures.logcapture import LoggingSource
    from testfixtures.structlog import StructlogSource

    with LogCapture(StructlogSource(), LoggingSource()) as log:
        logging.warning('from standard library logging')
        structlog.get_logger().warning('from structlog')

    log.check(
        ('WARNING', 'from standard library logging'),
        ('WARNING', 'from structlog'),
    )

Note that if your structlog is configured with
:class:`structlog.stdlib.LoggerFactory` so that structlog calls flow *through*
stdlib logging, then a single :class:`~testfixtures.logcapture.LoggingSource`
is enough — adding :class:`~testfixtures.structlog.StructlogSource` would
double-capture each event.

Exceptions
----------

When code logs an exception, the underlying exception object is stored in
:attr:`~testfixtures.logcapture.Entry`'s ``exception`` attribute:

.. code-block:: python

    from testfixtures import LogCapture, compare
    from testfixtures.structlog import StructlogSource

    with LogCapture(StructlogSource()) as logs:
        try:
            raise ValueError('boom')
        except ValueError:
            structlog.get_logger().exception('oh no')

    compare(logs.entries[-1].exception, expected=ValueError('boom'))

Running selected processors during capture
------------------------------------------

By default :class:`~testfixtures.structlog.StructlogSource` bypasses your
configured processor chain — only :func:`structlog.stdlib.add_log_level` and
:func:`~structlog.contextvars.merge_contextvars` run before capture. This
mirrors :func:`structlog.testing.capture_logs` and keeps assertions clean of
per-run noise like timestamps and call sites.

If you need different processors during capture (for example, to verify what a
renderer would emit), pass them via ``processors``:

.. code-block:: python

    from structlog.contextvars import merge_contextvars
    from structlog.processors import KeyValueRenderer

    with LogCapture(
        StructlogSource(
            attributes='event',
            processors=[merge_contextvars, KeyValueRenderer(sort_keys=True)],
        )
    ) as log:
        structlog.get_logger().bind(user='alice').info('hi')

    log.check("event='hi' level='info' user='alice'")

The same pattern works for :class:`~structlog.processors.JSONRenderer`:

.. code-block:: python

    from structlog.processors import JSONRenderer

    with LogCapture(
        StructlogSource(
            attributes='event',
            processors=[merge_contextvars, JSONRenderer(sort_keys=True)],
        )
    ) as log:
        structlog.get_logger().bind(user='alice').info('hi')

    log.check('{"event": "hi", "level": "info", "user": "alice"}')

When a renderer is the last processor, the captured value is a string, so
``attributes`` is best set to a single key like ``'event'`` to avoid
tuple-shaping over a string. See structlog's :doc:`processors guide
<structlog:processors>` and :func:`~structlog.testing.capture_logs` for the
underlying mechanics.

Avoid putting :func:`structlog.processors.format_exc_info` in ``processors``:
it replaces ``exc_info`` with a formatted string and defeats the
:attr:`~testfixtures.logcapture.Entry.exception` extraction shown above.

Checking the configuration of your logging
------------------------------------------

:class:`~testfixtures.structlog.StructlogSource` is good for checking that your
code is logging the correct messages; just as important is checking that your
application has correctly configured structlog. If you have a ``setup_logging``
function such as this:

.. code-block:: python

    import structlog

    def setup_logging() -> None:
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.stdlib.add_log_level,
                structlog.processors.TimeStamper(fmt='iso'),
                structlog.processors.JSONRenderer(),
            ],
        )

This can be tested with a unit test such as the following:

.. code-block:: python

    from testfixtures import compare

    def test_setup_logging() -> None:
        setup_logging()
        config = structlog.get_config()
        names = [getattr(p, '__name__', type(p).__name__) for p in config['processors']]
        compare(
            names,
            expected=['merge_contextvars', 'add_log_level', 'TimeStamper', 'JSONRenderer'],
        )

.. check it:

   >>> test_setup_logging()
   >>> structlog.reset_defaults()
