Testing with Loguru
===================

.. note::

   To ensure you are using compatible versions, install with the ``testfixtures[loguru]`` extra.

`Loguru <https://github.com/Delgan/loguru>`_ provides a streamlined logging API with a single
``logger`` object. Testfixtures integrates with it through :class:`~testfixtures.loguru.LoguruSource`,
which plugs into the unified :class:`~testfixtures.LogCapture` API.

LogCapture with LoguruSource
-----------------------------

Pass a :class:`~testfixtures.loguru.LoguruSource` instance in the ``sources`` list when
constructing :class:`~testfixtures.LogCapture`. The source exclusively captures loguru output
for the duration of the context manager, removing any pre-existing loguru handlers and
restoring them on exit::

    from testfixtures import LogCapture
    from testfixtures.loguru import LoguruSource

    with LogCapture(LoguruSource()) as log:
        # ... code that logs via loguru ...
        log.check(('INFO', 'expected message'))

By default, each captured entry's ``actual`` value is a ``(level_name, message)`` tuple.

To filter by level::

    with LogCapture(LoguruSource(level='WARNING')) as log:
        # only WARNING and above are captured
        ...

To capture only the message (single field)::

    with LogCapture(LoguruSource(fields=(lambda r: r['message'],))) as log:
        ...
        log.check('expected message')

To check or raise captured exceptions::

    log.check_exception_str('expected error message')
    log.raise_first_exception()

The tests for this functionality are provided by way of the test suite:

.. literalinclude:: ../tests/test_loguru.py
   :pyobject: TestLogCapture
