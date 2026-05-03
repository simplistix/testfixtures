Testing with structlog
======================

.. note::

   To ensure you are using compatible versions, install with the ``testfixtures[structlog]`` extra.

.. invisible-code-block: python

    try:
        import structlog
    except ImportError:
        structlog = None

.. skip: start if(structlog is None, reason="No structlog installed")

Helpers for testing code that uses `structlog <https://www.structlog.org/>`_ will live here.
