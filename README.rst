Testfixtures
============

|Docs|_ |PyPI|_  |Git|_

.. |Docs| image:: https://readthedocs.org/projects/testfixtures/badge/?version=latest
.. _Docs: http://testfixtures.readthedocs.org/en/latest/

.. |PyPI| image:: https://badge.fury.io/py/testfixtures.svg
.. _PyPI: https://pypi.org/project/testfixtures/

.. |Git| image:: https://github.com/simplistix/testfixtures/actions/workflows/ci.yml/badge.svg
.. _Git: https://github.com/simplistix/testfixtures

Testfixtures is a collection of helpers and mock objects that are useful when
writing automated tests in Python.

The areas of testing this package can help with are listed below:

**Comparing, asserting equality and explaining differences**

The ``compare`` function gives readable feedback when results aren't as expected,
with clear diffs for deeply nested data structures and for objects that don't
normally support comparison. This includes first-class support for pandas and
polars dataframes and numpy arrays. Flexible placeholder objects and matchers
such as ``like``, ``sequence``, ``generator``, ``Comparison``, ``RoundComparison``,
``RangeComparison``, ``TextComparison`` and ``SequenceComparison`` let you assert that only part
of a value matters, that a number is within a range or rounded to a precision, or
that a string matches a pattern.

**Mocking out objects and methods**

``Replacer`` makes it easy to swap out objects, classes or individual methods for the
duration of a test, restoring the originals automatically when it ends. You point them
at the thing being replaced directly rather than at a dotted string, so your type
checker verifies the target and the replacement survives refactoring.
``replace_on_class``, ``replace_in_module`` and ``replace_in_environ`` cover common cases such as
methods, module globals and environment variables.

**Mocking dates and times**

``mock_datetime``, ``mock_date`` and ``mock_time`` are drop-in replacements for
the ``datetime`` and ``time`` APIs, for testing code that depends on the current
date or time. They cover the thorny issues of timezones, non-uniform sequences of mock
time increments, explicit ticking and freezing a point in time so you don't have to
invent them from scratch.

**Testing subprocesses**

``MockPopen`` lets you test code that uses ``subprocess.Popen`` without running
real processes.

**Testing command-line scripts**

``Command`` drives entry-point scripts end to end and checks their output,
logging, mock calls and return code.

**Testing logging**

``LogCapture`` captures log messages so you can check what was logged is what you
expected, including from the loguru and structlog libraries.

**Testing stream output**

``OutputCapture`` captures stream output, such as that from print calls or even
writes made directly to file descriptors, and makes it easy to assert about.

**Testing with files and directories**

``TempDirectory`` gives you a sandboxed directory to work in. It makes it easy to
read and write files, serialise and deserialise structured data in formats such as
JSON, YAML and TOML, create directory trees, and assert on the contents of both
individual files and whole directories.

**Testing exceptions and warnings**

``ShouldRaise``, ``ShouldAssert``, ``ShouldWarn`` and ``ShouldNotWarn`` check
that a particular exception is raised, that an assertion fails with a particular
message, or that a warning is issued, down to the parameters involved.

**Testing when using Django**

Helpers for comparing instances of Django models.

**Testing when using Twisted**

Helpers for making assertions about logging when using Twisted.
