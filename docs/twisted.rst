Testing with Twisted
====================

.. note::

   To ensure you are using compatible versions, install with the ``testfixtures[twisted]`` extra.

Due to its longevity, Twisted has many of its own patterns for things that have since become
standard in Python. One of these is logging, where it has its own logging framework.

Unified LogCapture with TwistedSource
--------------------------------------

The recommended approach is to use the unified :class:`~testfixtures.LogCapture` with a
:class:`~testfixtures.twisted.TwistedSource`. This gives you access to the full
:class:`~testfixtures.LogCapture` API including :meth:`~testfixtures.LogCapture.check`,
:meth:`~testfixtures.LogCapture.raise_first_exception`, and
:meth:`~testfixtures.LogCapture.check_exception_str`::

    from testfixtures import LogCapture
    from testfixtures.twisted import TwistedSource

    with LogCapture(TwistedSource()) as log:
        # ... code that logs via Twisted ...
        log.check((INFO, 'expected message'))

To check captured log entries without caring about order::

    log.check(
        (INFO, 'second message'),
        (INFO, 'first message'),
        order_matters=False,
    )

To check or raise captured exceptions::

    log.check_exception_str('expected error message')
    log.raise_first_exception()

The new tests for this functionality are provided by way of the test suite:

.. literalinclude:: ../tests/test_twisted.py
   :pyobject: TestUnifiedLogCapture

Legacy twisted.LogCapture
--------------------------

A :class:`testfixtures.twisted.LogCapture` helper is also provided for backward compatibility.
Its documentation is provided by way of the test suite:

.. literalinclude:: ../tests/test_twisted.py
   :pyobject: TestLogCapture
