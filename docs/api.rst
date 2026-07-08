API Reference
=============

.. currentmodule:: testfixtures

.. Register module targets that docstrings and the changelog cross-reference,
   without rendering their (empty) module docstrings.
.. module:: testfixtures.comparison

.. module:: testfixtures.comparers

.. currentmodule:: testfixtures


Comparing
---------

.. autofunction:: compare

.. autofunction:: testfixtures.comparison.register

.. autoclass:: testfixtures.comparison.CompareContext
   :members:

Comparers
~~~~~~~~~

.. autofunction:: testfixtures.comparers.compare_simple

.. autofunction:: testfixtures.comparers.compare_object

.. autofunction:: testfixtures.comparers.merge_ignored_attributes

.. autofunction:: testfixtures.comparers.compare_exception

.. autofunction:: testfixtures.comparers.compare_exception_group

.. autofunction:: testfixtures.comparers.compare_with_type

.. autofunction:: testfixtures.comparers.compare_sequence

.. autofunction:: testfixtures.comparers.compare_generator

.. autofunction:: testfixtures.comparers.compare_tuple

.. autofunction:: testfixtures.comparers.compare_dict

.. autofunction:: testfixtures.comparers.compare_set

.. autofunction:: testfixtures.comparers.compare_text

.. autofunction:: testfixtures.comparers.compare_bytes

.. autofunction:: testfixtures.comparers.compare_call

.. autofunction:: testfixtures.comparers.compare_partial

.. autofunction:: testfixtures.comparers.compare_path

.. autofunction:: testfixtures.comparers.compare_with_fold

.. autofunction:: testfixtures.comparers.safe_repr

.. autofunction:: testfixtures.comparers.safe_pformat

.. autoclass:: testfixtures.comparers.AlreadySeen

.. currentmodule:: testfixtures

Matchers
--------

.. autofunction:: testfixtures.like

.. autofunction:: testfixtures.repr_like

.. autofunction:: testfixtures.str_like

.. autofunction:: testfixtures.sequence

.. autofunction:: testfixtures.contains

.. autofunction:: testfixtures.unordered

.. autofunction:: testfixtures.mapping

Comparison objects
------------------

.. autoclass:: Comparison

.. autoclass:: ReprComparison

.. autoclass:: StrComparison

.. autoclass:: TextComparison
   :members:

.. autoclass:: SequenceComparison
   :members:

.. autoclass:: Subset
   :members:

.. autoclass:: Permutation
   :members:

.. autoclass:: MappingComparison
   :members:

.. autoclass:: RangeComparison
   :members:

.. autoclass:: RoundComparison
   :members:

.. py:class:: StringComparison

   Deprecated alias for :class:`TextComparison`. Note this is *not* the same as
   :class:`StrComparison`.

Capturing
---------

.. autoclass:: LogCapture
   :members:

.. autoclass:: LoggingSource
   :members:

.. autofunction:: log_capture

.. autoclass:: testfixtures.logcapture.CaptureSource
   :members:

.. autoclass:: testfixtures.logcapture.Entry
   :members:

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


Commands
--------

.. automodule:: testfixtures.command
   :members:
   :special-members: __call__

.. currentmodule:: testfixtures

Resources
---------

.. autoclass:: TempDir
   :members:
   :inherited-members:

.. autoclass:: TempDirectory
   :members:
   :inherited-members:

.. autofunction:: tempdir

Serialization Formats
~~~~~~~~~~~~~~~~~~~~~

.. automodule:: testfixtures.formats
  :members:

Helpers and Constants
---------------------

.. currentmodule:: testfixtures

.. autofunction:: diff

.. autofunction:: generator

.. autofunction:: wrap

.. autoclass:: singleton
   :members:

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


testfixtures.loguru
~~~~~~~~~~~~~~~~~~~

.. automodule:: testfixtures.loguru
   :members:

testfixtures.numpy
~~~~~~~~~~~~~~~~~~

.. automodule:: testfixtures.numpy
   :members:

testfixtures.pandas
~~~~~~~~~~~~~~~~~~~

.. automodule:: testfixtures.pandas
   :members:

testfixtures.polars
~~~~~~~~~~~~~~~~~~~

.. automodule:: testfixtures.polars
   :members:

testfixtures.pydantic
~~~~~~~~~~~~~~~~~~~~~

.. automodule:: testfixtures.pydantic
   :members:

testfixtures.structlog
~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: testfixtures.structlog
   :members:

testfixtures.twisted
~~~~~~~~~~~~~~~~~~~~

.. automodule:: testfixtures.twisted

.. autoclass:: testfixtures.twisted.TwistedSource
   :members:

.. autoclass:: testfixtures.twisted.LogCapture
   :members:

.. autodata:: testfixtures.twisted.DEBUG
.. autodata:: testfixtures.twisted.INFO
.. autodata:: testfixtures.twisted.WARN
.. autodata:: testfixtures.twisted.ERROR
.. autodata:: testfixtures.twisted.CRITICAL
