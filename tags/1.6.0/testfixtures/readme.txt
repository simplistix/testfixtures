============
TestFixtures
============

TestFixtures is a collection of helpers and mock objects that are
useful when writing unit tests or doc tests.

It's simple enough to get going with them, do one of the following:

- `easy_install testfixtures`

- add `testfixtures` as a required egg in your buildout config.
  You should only need to do this in the section that defines your
  test runner.

- download testfixtures.tar.gz from 

  http://pypi.python.org/pypi/testfixtures

  You'll then need to unpack it and do the usual 
  `python setup.py install`

If you're wondering why "yet another mock object library", testing is
often described as an art form and as such some styles of library will
suite some people while others will suite other styles. This library
was extracted from common test fixtures the author found himself
repeating from package to packages and so decided to extract them into
their own library and give them some tests of their own!

NB: TestFixtures own tests use the excellent Mock package:

    http://pypi.python.org/pypi/mock/

    While use of TestFixtures doesn't require Mock to be installed,
    it's highly recommended if you need mock objects for testing.

The available helpers and mock objects are listed below, for
functional examples, see the contents of the tests folder.

**Comparison**
  This class lets you instantiate placeholders that can be used to
  compared expected results with actual results where objects in the
  actual results do not support useful comparison.
  The comparision can be based just on the type of the object or on a
  partial set of the object's attributes, both of which are
  particularly handy when comparing sequences returned from tested
  code.

**compare**
  A replacement for assertEquals and the failUnless(x() is True)
  pattern. Gives more useful differences when the arguments aren't the
  same, particularly for sequences and long strings.

**diff**
  This function will compare two strings and give a unified diff
  of their comparison. Handy as a third parameter to
  unittest.TestCase.assertEquals.

**generator**
  This function will return a generator that yields the arguments
  it was called with when the generator is iterated over.

**LogCapture**
  This helper allows you to capture log messages for specified loggers
  in doctests.

**log_capture**
  This decorator allows you to capture log messages for specified loggers
  for the duration of unittest methods.

**replace**
  This decorator enables you to replace objects such as classes and
  functions for the duration of a unittest method. The replacements
  are removed regardless of what happens during the test.

**Replacer**
  This helper enables you to replace objects such as classes and
  functions from within doctests and then restore the originals once
  testing is completed.

**should_raise**
  This is a better version of assertRaises that lets you check the
  exception raised is not only of the correct type but also has the
  correct parameters.

**TempDirectory**
  This helper will create a temporary directory for you using mkdtemp
  and provides a handy class method for cleaning all of these up.

**tempdir**
  This decorator will create a temporary directory for the duration of
  the unit test and clear it up no matter the outcome of the test.

**test_date**
  This is a handy class factory that returns datetime.date
  replacements that have a `today` method that gives repeatable,
  specifiable, testable dates.

**test_datetime**
  This is a handy class factory that returns datetime.datetime
  replacements that have a `now` method that gives repeatable,
  specifiable, testable datetimes.

**test_time**
  This is a handy replacement for time.time that gives repeatable,
  specifiable, testable times.

**wrap**
  This is a generic decorator for wrapping method and function calls
  with a try-finally and having code executed before the try and as
  part of the finally.

Licensing
=========

Copyright (c) 2008 Simplistix Ltd

See license.txt for details.

Changes
=======

1.6.0 (09 May 2009)
-------------------

- added support for using TempDirectory, Replacer and LogCapture as
  context managers for with statements

- fixed test failure in Python 2.6

1.5.4 (11 Feb 2009)
-------------------

- fix bug where should_raise didn't complain when no exception 
  was raised but one was expected.

- clarified that the return of a should_raise call will be None
  in the event that an exception is raised by no expected 
  exception is specified.

1.5.3 (17 Dec 2008)
-------------------

- should_raise now supports methods other than __call__

1.5.2 (14 Dec 2008)
-------------------

- added `makedir` and `check_dir` methods to TempDirectory and added
  support for sub directories to `read` and `write`

1.5.1 (12 Dec 2008)
-------------------

- added `path` parameter to `write` method of TempDirectory so
  that the full path of the file written can be easilly obtained

1.5.0 (12 Dec 2008)
-------------------

- added handy `read` and `write` methods to TempDirectory for
  creating and reading files in the temporary directory

- added support for rich comparison of objects that don't support
  vars()

1.4.0 (12 Dec 2008)
-------------------

- improved representation of failed Comparison

- improved representation of failed compare with sequences

1.3.1 (10 Dec 2008)
-------------------

- fixed bug that occurs when directory was deleted by a test that
  use tempdir or TempDirectory

1.3.0 (9 Dec 2008)
------------------

- added TempDirectory helper

- added tempdir decorator

1.2.0 (3 Dec 2008)
------------------

- LogCaptures now auto-install on creation unless configured otherwise

- LogCaptures now have a clear method

- LogCaptures now have a class method uninstall_all that uninstalls
  all instances of LogCapture. Handy for a tearDown method in doctests.

1.1.0 (3 Dec 2008)
------------------

- add support to Comparisons for only comparing some attributes

- move to use zope.dottedname

1.0.0 (26 Nov 2008)
-------------------

- Initial Release
