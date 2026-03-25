Testing with Twisted
====================

.. note::

   To ensure you are using compatible versions, install with the ``testfixtures[twisted]`` extra.

.. invisible-code-block: python

    try:
        import twisted
    except ImportError:
        twisted = None

.. skip: start if(twisted is None, reason="No twisted installed")

Due to its longevity, Twisted has its own structured logging framework built around
:class:`~twisted.logger.Logger` objects and log event dicts.
:class:`~testfixtures.twisted.TwistedSource` is provided to work with this.

Testing logging
---------------

Pass a :class:`~testfixtures.twisted.TwistedSource` instance when constructing
:class:`~testfixtures.LogCapture`. It replaces all existing Twisted log observers for the
duration of the context manager and restores them on exit:

.. code-block:: python

  from twisted.logger import Logger
  from testfixtures import LogCapture
  from testfixtures.twisted import TwistedSource

  log = Logger()

  with LogCapture(TwistedSource()) as logs:
      log.info('hello {name}', name='world')

  logs.check(('INFO', 'hello world'))

See :doc:`logging` for the full :class:`~testfixtures.LogCapture` API, including
:meth:`~testfixtures.LogCapture.check`, :meth:`~testfixtures.LogCapture.check_present`,
:meth:`~testfixtures.LogCapture.actual`, and the :attr:`~testfixtures.LogCapture.entries`
attribute.

Inspecting raw events
~~~~~~~~~~~~~~~~~~~~~

Each :class:`~testfixtures.logcapture.Entry` in :attr:`~testfixtures.LogCapture.entries`
exposes the underlying Twisted log event dict via its ``raw`` attribute:

.. code-block:: python

  with LogCapture(TwistedSource()) as logs:
      log.info('hello {greeting}', greeting='world')

>>> logs.entries[0].raw
{'greeting': 'world',..., 'log_level': <LogLevel=info>, 'log_namespace': '<unknown>', ...}

The event dict contains all the structured fields Twisted attaches to each log call,
including ``log_namespace``, ``log_source``, ``log_level``, ``log_format`` along with
any keyword arguments passed to the log call.
``log_failure`` is present when logging a :class:`~twisted.python.failure.Failure`.

Capturing specific fields
~~~~~~~~~~~~~~~~~~~~~~~~~

You can control which fields form the ``actual`` value by passing an ``attributes`` sequence to
:class:`~testfixtures.twisted.TwistedSource`. Elements may be string keys into the event dict
or callables that receive the event dict.

For example, to capture only the formatted message, pass :func:`~twisted.logger.formatEvent` as
the sole element:

.. code-block:: python

    from twisted.logger import formatEvent

    with LogCapture(TwistedSource(attributes=formatEvent)) as logs:
        log.info('hello {greeting}', greeting='world')

    logs.check('hello world')

You can also mix string keys and callables:

.. code-block:: python

    with LogCapture(TwistedSource(attributes=('log_namespace', formatEvent))) as logs:
        Logger(namespace='myapp').info('started')

    logs.check(('myapp', 'started'))

For full control, pass a single callable as ``attributes``:

.. code-block:: python

    from testfixtures.twisted import INFO, WARN
    logger = Logger(namespace='myapp')

    def extract(event):
        return {'level': event['log_level'], 'message': formatEvent(event)}

    with LogCapture(TwistedSource(attributes=extract)) as logs:
        logger.info('started')
        logger.warn('low memory')

    logs.check(
        {'level': INFO, 'message': 'started'},
        {'level': WARN, 'message': 'low memory'},
    )

In the above example, the Twisted log level objects are returned. For convenience in making
assertions about these, the following constants are
exported from :mod:`testfixtures.twisted` for use in assertions:
:data:`~testfixtures.twisted.DEBUG`,
:data:`~testfixtures.twisted.INFO`,
:data:`~testfixtures.twisted.WARN`,
:data:`~testfixtures.twisted.ERROR` and
:data:`~testfixtures.twisted.CRITICAL`.



Filtering by level
~~~~~~~~~~~~~~~~~~

To capture only events at or above a minimum level:

.. code-block:: python

    with LogCapture(TwistedSource(level='warn')) as capture:
        log.info('ignored')
        log.warn('captured')
    capture.check(('WARN', 'captured'))

Combining with standard library logging
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If your application uses both Twisted and the standard library's :mod:`logging`,
pass both a :class:`~testfixtures.LoggingSource` and a
:class:`~testfixtures.twisted.TwistedSource` to one :class:`~testfixtures.LogCapture`
to capture and check both:

.. code-block:: python

    import logging
    from testfixtures import LogCapture, LoggingSource
    from testfixtures.twisted import TwistedSource

    with LogCapture(LoggingSource(), TwistedSource()) as logs:
        logging.warning('from stdlib')
        log.warn('from twisted')

    logs.check(
        ('WARNING', 'from stdlib'),
        ('WARN', 'from twisted'),
    )

.. note::

    Twisted's ``LogLevel.warn`` surfaces as ``'WARN'`` while standard library
    logging uses ``'WARNING'``.

Exceptions and failures
~~~~~~~~~~~~~~~~~~~~~~~

When code logs a :class:`~twisted.python.failure.Failure`, the underlying exception object
is stored in the :attr:`~testfixtures.logcapture.Entry`'s ``exception`` attribute:

.. code-block:: python

    from testfixtures import LogCapture, compare
    from testfixtures.twisted import TwistedSource

    with LogCapture(TwistedSource()) as logs:
        try:
            raise ValueError('boom')
        except Exception:
            log.failure('something went wrong')

    logs.check(
        ('CRITICAL', 'something went wrong')
    )
    compare(logs.entries[-1].exception, expected=ValueError('boom'))

Testing logging configuration
-----------------------------

:class:`~testfixtures.twisted.TwistedSource` is good for checking that your code is logging
the correct messages; just as important is checking that your application has correctly
configured its Twisted log observers. If you have a ``setup_logging`` function such as this:

.. code-block:: python

    import sys
    from twisted.logger import globalLogPublisher, textFileLogObserver

    def setup_logging(stream=None) -> None:
        globalLogPublisher.addObserver(textFileLogObserver(stream or sys.stderr))

This can be tested with a unit test such as the following:

.. code-block:: python

    from twisted.logger import FileLogObserver
    from testfixtures import Replacer, compare, like

    def test_setup_logging() -> None:
        with Replacer() as replace:
            replace(
                globalLogPublisher._observers, [],
                container=globalLogPublisher, name='_observers',
            )
            setup_logging()
            compare(
                globalLogPublisher._observers,
                expected=[like(FileLogObserver)],
            )

.. check it:

   >>> test_setup_logging()

Trial test case support
-----------------------

Since Twisted's ``trial`` test runner has its own ``TestCase`` class on which you may well need
to call ``flushLoggedErrors()`` in the event that you're testing exception logging, a dedicated
:class:`testfixtures.twisted.LogCapture` is also provided, including a
:meth:`~testfixtures.twisted.LogCapture.make` class method for creating, installing and adding a
cleanup for the capture.

This sample test suite shows it all in action:

.. literalinclude:: ../tests/test_twisted.py
   :pyobject: TestLogCapture
