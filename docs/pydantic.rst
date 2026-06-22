Testing with Pydantic
=====================

.. note::

   To ensure you are using compatible versions, install with the ``testfixtures[pydantic]`` extra.

.. invisible-code-block: python

    try:
        import pydantic
    except ImportError:
        pydantic = None

.. skip: start if(pydantic is None, reason="No pydantic installed")

Helpers for testing code that uses `Pydantic <https://docs.pydantic.dev/>`_ will live here.
