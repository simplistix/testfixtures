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

Examples
========

The following are short examples of each of the fixtures included, for
more detailed examples, see the unit tests or doc tests in the tests
directory. 

Licensing
=========

Copyright (c) 2008 Simplistix Ltd

See license.txt for details.

Changes
=======

x.y.z 
-----

- Initial Release
