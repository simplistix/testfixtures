Testing with Pandas
===================

.. note::

   To ensure you are using compatible versions, install with the ``testfixtures[pandas]`` extra.

.. invisible-code-block: python

    try:
        import pandas
    except ImportError:
        pandas = None

.. skip: start if(pandas is None, reason="No pandas installed")

Helpers for testing code that uses `Pandas <https://pandas.pydata.org/>`_ will live here.
