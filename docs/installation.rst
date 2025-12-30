Installation Instructions
=========================

If you want to experiment with testfixtures, the easiest way to
install it is to do the following in a virtualenv:

.. code-block:: bash

  pip install testfixtures

If you are using `uv`__, add testfixtures to your project's `dev` dependency group:

__ https://docs.astral.sh/uv/

.. code-block:: toml

    [dependency-groups]
    dev = [
        "testfixtures",
    ]

If you are using `conda`__, testfixtures can be installed as follows:

__ https://docs.conda.io/

.. code-block:: bash

  conda install -c conda-forge testfixtures

For legacy projects using setuptools with :file:`setup.py`,
you should do one of the following:

- Specify ``testfixtures`` in the ``tests_require`` parameter of your
  package's call to ``setup`` in :file:`setup.py`.

- Add an ``extra_requires`` parameter in your call to ``setup`` as
  follows:

  .. invisible-code-block: python

     from testfixtures.mock import Mock
     setup = Mock()

  .. code-block:: python

    setup(
        # other stuff here
        extras_require=dict(
            test=['testfixtures'],
        )
    )

Optional Dependencies
---------------------

Several optional extras are provided for specific frameworks and tools.
While you don't have to specify these extras, doing so will ensure compatibility
with the version of these packages that your project is using:

- ``[django]``: Django ORM integration and comparison helpers. See :doc:`django`.

- ``[twisted]``: Twisted framework logging support. See :doc:`twisted`.

- ``[sybil]``: Sybil documentation testing framework. See :ref:`sybil`.

- ``[mock-backport]``: See documentation on :ref:`which mock to use <what-mock>`.

Multiple extras can be installed together, for example: ``testfixtures[django,twisted]``.
