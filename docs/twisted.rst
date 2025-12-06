Testing with Twisted
====================

Due to its longevity, Twisted has many of its own patterns for things that have since become
standard in Python. One of these is logging, where it has its own logging framework.

A :class:`testfixtures.twisted.LogCapture` helper is provided, but given the framework's
relatively niche use now, the documentation is provided by way of the test suite:


.. literalinclude:: ../testfixtures/tests/test_twisted.py
