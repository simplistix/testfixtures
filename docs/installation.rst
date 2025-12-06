Installation Instructions
=========================

If you want to experiment with testfixtures, the easiest way to
install it is to do the following in a virtualenv:

.. code-block:: bash

  pip install testfixtures


If you are using conda, testfixtures can be installed as follows:


.. code-block:: bash

  conda install -c conda-forge testfixtures


If your package uses setuptools and you decide to use testfixtures,
then you should do one of the following:

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
