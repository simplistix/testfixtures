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
