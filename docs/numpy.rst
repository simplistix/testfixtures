Testing with NumPy
==================

.. note::

   To ensure you are using compatible versions, install with the ``testfixtures[numpy]`` extra.

.. invisible-code-block: python

    try:
        import numpy
    except ImportError:
        numpy = None

.. skip: start if(numpy is None, reason="No numpy installed")

Helpers for testing code that uses `NumPy <https://numpy.org/>`_ will live here.
