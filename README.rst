Testfixtures
============

|CircleCI|_ |Docs|_

.. |CircleCI| image:: https://circleci.com/gh/Simplistix/testfixtures/tree/master.svg?style=shield
.. _CircleCI: https://circleci.com/gh/Simplistix/testfixtures/tree/master

.. |Docs| image:: https://readthedocs.org/projects/testfixtures/badge/?version=latest
.. _Docs: http://testfixtures.readthedocs.org/en/latest/

Testfixtures is a collection of helpers and mock objects that are useful when
writing automated tests in Python.

The areas of testing this package can help with are listed below:

**Comparing objects and sequences**

Better feedback when the results aren't as you expected along with
support for comparison of objects that don't normally support
comparison and comparison of deeply nested datastructures.

**Mocking out objects and methods**

Easy to use ways of stubbing out objects, classes or individual
methods for both doc tests and unit tests. Special helpers are
provided for testing with dates and times.

**Testing logging**

Helpers for capturing logging output in both doc tests and
unit tests.

**Testing stream output**

Helpers for capturing stream output, such as that from print
statements, and making assertion about it.

**Testing with files and directories**

Support for creating and checking files and directories in sandboxes
for both doc tests and unit tests.

**Testing exceptions and warnings**

Easy to use ways of checking that a certain exception is raised,
or a warning is issued, even down the to the parameters provided.

**Testing subprocesses**

A handy mock for testing code that uses subprocesses.

**Testing when using django**

Helpers for comparing instances of django models.

**Testing when using zope.component**

An easy to use sterile component registry.
