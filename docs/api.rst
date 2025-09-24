API Reference
=============

.. currentmodule:: testfixtures


Comparisons
-----------

.. autofunction:: compare

.. autoclass:: Comparison

.. autofunction:: testfixtures.like

.. autoclass:: MappingComparison
   :members:

.. autoclass:: Permutation
   :members:

.. autoclass:: RoundComparison
   :members:

.. autoclass:: RangeComparison
   :members:

.. autoclass:: SequenceComparison
   :members:

.. autofunction:: testfixtures.sequence

.. autofunction:: testfixtures.contains

.. autofunction:: testfixtures.unordered

.. autoclass:: Subset
   :members:

.. autoclass:: StringComparison
   :members:


testfixtures.comparison
~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: testfixtures.comparison

.. autofunction:: testfixtures.comparison.register

.. autofunction:: testfixtures.comparison.compare_simple

.. autofunction:: testfixtures.comparison.compare_object

.. autofunction:: testfixtures.comparison.merge_ignored_attributes

.. autofunction:: testfixtures.comparison.compare_exception

.. autofunction:: testfixtures.comparison.compare_exception_group

.. autofunction:: testfixtures.comparison.compare_with_type

.. autofunction:: testfixtures.comparison.compare_sequence

.. autofunction:: testfixtures.comparison.compare_generator

.. autofunction:: testfixtures.comparison.compare_tuple

.. autofunction:: testfixtures.comparison.compare_dict

.. autofunction:: testfixtures.comparison.compare_set

.. autofunction:: testfixtures.comparison.compare_text

.. autoclass:: testfixtures.comparison.CompareContext

.. currentmodule:: testfixtures

Capturing
---------

.. autoclass:: LogCapture
   :members:

.. autofunction:: log_capture

.. autoclass:: OutputCapture
   :members:

Mocking
-------
.. autoclass:: Replace
   :members:

.. autofunction:: replace_in_environ

.. autofunction:: replace_on_class

.. autofunction:: replace_in_module

.. autoclass:: Replacer
   :members:
   :special-members: __call__

.. autofunction:: replace

.. autofunction:: mock_date

.. autoclass:: testfixtures.datetime.MockDate
    :members:

.. autofunction:: mock_datetime

.. autoclass:: testfixtures.datetime.MockDateTime
    :members:

.. autofunction:: mock_time

.. autoclass:: testfixtures.datetime.MockTime
    :members:
    :special-members: __new__

testfixtures.mock
~~~~~~~~~~~~~~~~~

.. automodule:: testfixtures.mock


testfixtures.popen
~~~~~~~~~~~~~~~~~~

.. automodule:: testfixtures.popen
   :members:

.. currentmodule:: testfixtures

Assertions
----------

.. autoclass:: testfixtures.shouldraise.NoException

.. autoclass:: ShouldRaise
   :members:

.. autoclass:: should_raise

.. autofunction:: ShouldAssert

.. autoclass:: ShouldWarn
   :members:

.. autoclass:: ShouldNotWarn
   :members:


Resources
---------

.. autoclass:: TempDir
   :members:
   :inherited-members:

.. autoclass:: TempDirectory
   :members:
   :inherited-members:

.. autofunction:: tempdir

.. autofunction:: generator


Helpers and Constants
---------------------

.. autofunction:: diff

.. autofunction:: wrap

.. data:: not_there

   A singleton used to represent the absence of a particular attribute or parameter.


Framework Helpers
-----------------

Framework-specific helpers provided by testfixtures.

testfixtures.django
~~~~~~~~~~~~~~~~~~~

.. automodule:: testfixtures.django
  :members:

testfixtures.sybil
~~~~~~~~~~~~~~~~~~


.. autoclass:: testfixtures.sybil.FileParser
   :member-order: bysource
   :members:


testfixtures.twisted
~~~~~~~~~~~~~~~~~~~~

.. automodule:: testfixtures.twisted
   :member-order: bysource
   :members:
