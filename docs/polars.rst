Testing with Polars
===================

.. note::

   To ensure you are using compatible versions, install with the ``testfixtures[polars]`` extra.

.. invisible-code-block: python

    try:
        import polars
    except ImportError:
        polars = None

.. skip: start if(polars is None, reason="No polars installed")

Helpers for testing code that uses `Polars <https://pola.rs/>`_ will live here.
