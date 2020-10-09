Changes
=======

.. currentmodule:: testfixtures

6.15.0 (9 Oct 2020)
-------------------

- Add support to :class:`LogCapture` for making sure log entries above a specified
  level have been checked.

Thanks to Zoltan Farkas for the implementation.

6.14.2 (4 Sep 2020)
-------------------

- Fix bug where ``ignore_eq`` had no effect on nested objects when using :func:`compare`.

Thanks to Grégoire Payen de La Garanderie for the fix.

6.14.1 (20 Apr 2020)
--------------------

- Fix bugs in comparison of :func:`~unittest.mock.call` objects where the :func:`repr` of the
  :func:`~unittest.mock.call` arguments were the same even when their attributes were not.

6.14.0 (24 Feb 2020)
--------------------

- Add support for non-deterministic logging order when using :meth:`twisted.LogCapture`.

6.13.1 (20 Feb 2020)
--------------------

- Fix for using :func:`compare` to compare two-element :func:`~unittest.mock.call`
  objects.

Thanks to Daniel Fortunov for the fix.

6.13.0 (18 Feb 2020)
--------------------

- Allow any attributes that need to be ignored to be specified directly when calling
  :func:`~testfixtures.comparison.compare_object`. This is handy when writing
  comparers for :func:`compare`.

6.12.1 (16 Feb 2020)
--------------------

- Fix a bug that occured when using :func:`compare` to compare a string with a
  slotted object that had the same :func:`repr` as the string.

6.12.0 (6 Feb 2020)
-------------------

- Add support for ``universal_newlines``, ``text``, ``encoding`` and ``errors`` to
  :class:`popen.MockPopen`, but only for Python 3.

6.11.0 (29 Jan 2020)
--------------------

- :class:`decimal.Decimal` now has better representation when :func:`compare` displays a failed
  comparison, particularly on Python 2.

- Add support to :func:`compare` for explicitly naming objects to be compared as ``x`` and ``y``.
  This allows symmetry with the ``x_label`` and ``y_label`` parameters that are now documented.

- Restore ability for :class:`Comparison` to compare properties and methods, although these uses
  are not recommended.

Thanks to Daniel Fortunov for all of the above.

6.10.3 (22 Nov 2019)
--------------------

- Fix bug where new-style classes had their attributes checked with :func:`compare` even
  when they were of different types.

6.10.2 (15 Nov 2019)
--------------------

- Fix bugs in :func:`compare` when comparing objects which have both ``__slots__``
  and a ``__dict__``.

6.10.1 (1 Nov 2019)
-------------------

- Fix edge case where string interning made dictionary comparison output much less useful.

6.10.0 (19 Jun 2019)
--------------------

- Better feedback where objects do not :func:`compare` equal but do have the same
  representation.

6.9.0 (10 Jun 2019)
-------------------

- Fix deprecation warning relating to :func:`getargspec`.

- Improve :doc:`mocking <mocking>` docs.

- Added ``strip_whitespace`` option to :class:`OutputCapture`.

- When ``separate`` is used with :class:`OutputCapture`, differences in ``stdout`` and ``stderr``
  are now given in the same :class:`AssertionError`.

- :class:`ShouldRaise` no longer catches exceptions that are not of the required type.

- Fixed a problem that resulted in unhelpful :func:`compare` failures when
  :func:`~unittest.mock.call` was involved and Python 3.6.7 was used.

Thanks to Łukasz Rogalski for the deprecation warning fix.

Thanks to Wim Glenn for the :class:`ShouldRaise` idea.

6.8.2 (4 May 2019)
------------------

- Fix handling of the latest releases of the :mod:`mock` backport.

6.8.1 (2 May 2019)
------------------

- Fix bogus import in :class:`OutputCapture`.

6.8.0 (2 May 2019)
------------------

- Allow :class:`OutputCapture` to capture the underlying file descriptors for
  :attr:`sys.stdout` and :attr:`sys.stderr`.

6.7.1 (29 Apr 2019)
-------------------

- Silence :class:`DeprecationWarning` relating to ``collections.abc`` on
  Python 3.7.

Thanks to Tom Hendrikx for the fix.

6.7.0 (11 Apr 2019)
-------------------

- Add :meth:`twisted.LogCapture.raise_logged_failure` debugging helper.

6.6.2 (22 Mar 2019)
-------------------

- :meth:`popen.MockPopen.set_command` is now symmetrical with
  :class:`popen.MockPopen` process instantiation in that both can be called with
  either lists or strings, in the same way as :class:`subprocess.Popen`.

6.6.1 (13 Mar 2019)
-------------------

- Fixed bugs where using :attr:`not_there` to ensure a key or attribute was not there
  but would be set by a test would result in the test attribute or key being left behind.

- Add support for comparing :func:`~functools.partial` instances and fix comparison of
  functions and other objects where ``vars()`` returns an empty :class:`dict`.

6.6.0 (22 Feb 2019)
-------------------

- Add the ability to ignore attributes of particular object types when using
  :func:`compare`.

6.5.2 (18 Feb 2019)
-------------------

- Fix bug when :func:`compare` was used with objects that had ``__slots__`` inherited from a
  base class but where their ``__slots__`` was an empty sequence.

6.5.1 (18 Feb 2019)
-------------------

- Fix bug when :func:`compare` was used with objects that had ``__slots__`` inherited from a
  base class.

6.5.0 (28 Jan 2019)
-------------------

- Experimental support for making assertions about events logged with Twisted's logging framework.

6.4.3 (10 Jan 2019)
-------------------

- Fix problems on Python 2 when the rolling backport of `mock`__ was not installed.

__ https://mock.readthedocs.io

6.4.2 (9 Jan 2019)
------------------

- Fixed typo in the ``executable`` parameter name for :class:`~testfixtures.popen.MockPopen`.

- Fixed :func:`~unittest.mock.call` patching to only patch when needed.

- Fixed :func:`compare` with :func:`~unittest.mock.call` objects for the latest Python releases.

6.4.1 (24 Dec 2018)
-------------------

- Fix bug when using :func:`unittest.mock.patch` and any of the testfixtures decorators
  at the same time and where the object being patched in was not hashable.

6.4.0 (19 Dec 2018)
-------------------

- Add official support for Python 3.7.

- Drop official support for Python 3.5.

- Introduce a facade for :mod:`unittest.mock` at :mod:`testfixtures.mock`, including an
  important bug fix for :func:`~unittest.mock.call` objects.

- Better feedback when :func:`~unittest.mock.call` comparisons fail when using :func:`compare`.

- A re-working of :class:`~testfixtures.popen.MockPopen` to enable it to handle multiple
  processes being active at the same time.

- Fixes to :doc:`datetime` documentation.

Thanks to Augusto Wagner Andreoli for his work on the :doc:`datetime` documentation.

6.3.0 (4 Sep 2018)
------------------

- Allow the behaviour specified with :meth:`~testfixtures.popen.MockPopen.set_command` to be a
  callable meaning that mock behaviour can now be dynamic based on the command executed and whatever
  was sent to ``stdin``.

- Make :class:`~testfixtures.popen.MockPopen` more accurately reflect :class:`subprocess.Popen`
  on Python 3 by adding ``timeout`` parameters to :meth:`~testfixtures.popen.MockPopen.wait` and
  :meth:`~testfixtures.popen.MockPopen.communicate` along with some other smaller changes.

Thanks to Tim Davies for his work on :class:`~testfixtures.popen.MockPopen`.

6.2.0 (14 Jun 2018)
-------------------

- Better rendering of differences between :class:`bytes` when using :func:`compare`
  on Python 3.

6.1.0 (6 Jun 2018)
------------------

- Support filtering for specific warnings with :class:`ShouldWarn`.

6.0.2 (2 May 2018)
------------------

- Fix nasty bug where objects that had neither ``__dict__`` nor ``__slots__``
  would always be considered equal by :func:`compare`.

6.0.1 (17 April 2018)
---------------------

- Fix a bug when comparing equal :class:`set` instances using :func:`compare`
  when ``strict==True``.

6.0.0 (27 March 2018)
---------------------

- :func:`compare` will now handle objects that do not natively support equality or inequality
  and will treat these objects as equal if they are of the same type and have the same attributes
  as found using :func:`vars` or ``__slots__``. This is a change in behaviour which, while it could
  conceivably cause tests that are currently failing to pass, should not cause any currently
  passing tests to start failing.

- Add support for writing to the ``stdin`` of :class:`~testfixtures.popen.MockPopen` instances.

- The default behaviour of :class:`~testfixtures.popen.MockPopen` can now be controlled by
  providing a callable.

- :meth:`LogCapture.actual` is now part of the documented public interface.

- Add :meth:`LogCapture.check_present` to help with assertions about a sub-set of messages logged
  along with those that are logged in a non-deterministic order.

- :class:`Comparison` now supports objects with ``__slots__``.

- Added :class:`ShouldAssert` as a simpler tool for testing test helpers.

- Changed the internals of the various decorators testfixtures provides such that they can
  be used in conjunction with :func:`unittest.mock.patch` on the same test method or function.

- Changed the internals of :class:`ShouldRaise` and :class:`Comparison` to make use of
  :func:`compare` and so provide nested comparisons with better feedback. This finally
  allows :class:`ShouldRaise` to deal with Django's
  :class:`~django.core.exceptions.ValidationError`.

- Added handling of self-referential structures to :func:`compare` by treating all but the first
  occurence as equal. Another change needed to support Django's insane
  :class:`~django.core.exceptions.ValidationError`.

Thanks to Hamish Downer and Tim Davies for their work on :class:`~testfixtures.popen.MockPopen`.

Thanks to Wim Glenn and Daniel Fortunov for their help reviewing some of the more major changes.

5.4.0 (25 January 2018)
-----------------------

- Add explicit support for :class:`~unittest.mock.Mock` to :func:`compare`.

5.3.1 (21 November 2017)
------------------------

- Fix missing support for the `start_new_session` parameter to
  :class:`~testfixtures.popen.MockPopen`.

5.3.0 (28 October 2017)
-----------------------

- Add pytest traceback hiding for :meth:`TempDirectory.compare`.

- Add warnings that :func:`log_capture`, :func:`tempdir` and
  :func:`replace` are not currently compatible with pytest's fixtures
  mechanism.

- Better support for ``stdout`` or ``stderr`` *not* being set to ``PIPE``
  when using :class:`~testfixtures.popen.MockPopen`.

- Add support to :class:`~testfixtures.popen.MockPopen` for
  using :class:`subprocess.Popen` as a context manager in Python 3.

- Add support to :class:`~testfixtures.popen.MockPopen` for ``stderr=STDOUT``.

Thanks to Tim Davies for his work on :class:`~testfixtures.popen.MockPopen`.

5.2.0 (3 September 2017)
------------------------

- :class:`test_datetime` and :class:`test_time` now accept a
  :class:`~datetime.datetime` instance during instantiation to set the initial
  value.

- :class:`test_date` now accepts a :class:`~datetime.date` instance during
  instantiation to set the initial value.

- Relax the restriction on adding, setting or instantiating :class:`test_datetime`
  with `tzinfo` such that if the `tzinfo` matches the one configured,
  then it's okay to add.
  This means that you can now instantiate a :class:`test_datetime` with an existing
  :class:`~datetime.datetime` instance that has `tzinfo` set.

- :func:`testfixtures.django.compare_model` now ignores
  :class:`many to many <django.db.models.ManyToManyField>` fields rather than
  blowing up on them.

- Drop official support for Python 3.4, although things should continue to
  work.

5.1.1 (8 June 2017)
-------------------

- Fix support for Django 1.9 in
  :func:`testfixtures.django.compare_model`.

5.1.0 (8 June 2017)
-------------------

- Added support for including non-edit  able fields to the
  :func:`comparer <testfixtures.django.compare_model>` used by :func:`compare`
  when comparing :doc:`django <django>`
  :class:`~django.db.models.Model` instances.

5.0.0 (5 June 2017)
-------------------

- Move from `nose`__ to `pytest`__ for running tests.

  __ http://nose.readthedocs.io/en/latest/

  __ https://docs.pytest.org/en/latest/

- Switch from `manuel`__ to `sybil`__ for checking examples in
  documentation. This introduces a backwards incompatible change
  in that :class:`~testfixtures.sybil.FileParser` replaces the Manuel
  plugin that is no longer included.

  __ http://packages.python.org/manuel/

  __ http://sybil.readthedocs.io/en/latest/

- Add a 'tick' method to :meth:`test_datetime <tdatetime.tick>`,
  :meth:`test_date <tdate.tick>` and :meth:`test_time <ttime.tick>`,
  to advance the returned point in time, which is particularly helpful
  when ``delta`` is set to zero.

4.14.3 (15 May 2017)
--------------------

- Fix build environment bug in ``.travis.yml`` that caused bad tarballs.

4.14.2 (15 May 2017)
--------------------

- New release as it looks like Travis mis-built the 4.14.1 tarball.

4.14.1 (15 May 2017)
--------------------

- Fix mis-merge.

4.14.0 (15 May 2017)
--------------------

- Added helpers for testing with :doc:`django <django>`
  :class:`~django.db.models.Model` instances.

4.13.5 (1 March 2017)
-------------------------

- :func:`compare` now correctly compares nested empty dictionaries when using
  ``ignore_eq=True``.

4.13.4 (6 February 2017)
------------------------

- Keep the `Reproducible Builds`__ guys happy.

  __ https://reproducible-builds.org/

4.13.3 (13 December 2016)
-------------------------

- :func:`compare` now better handles equality comparison with ``ignore_eq=True``
  when either of the objects being compared cannot be hashed.

4.13.2 (16 November 2016)
-------------------------

- Fixed a bug where a :class:`LogCapture` wouldn't be cleared when used via
  :func:`log_capture` on a base class and sub class execute the same test.

Thanks to "mlabonte" for the bug report.

4.13.1 (2 November 2016)
------------------------

- When ``ignore_eq`` is used with :func:`compare`, fall back to comparing by
  hash if not type-specific comparer can be found.

4.13.0 (2 November 2016)
------------------------

- Add support to :func:`compare` for ignoring broken ``__eq__`` implementations.

4.12.0 (18 October 2016)
------------------------

- Add support for specifying a callable to extract rows from log records
  when using :class:`LogCapture`.

- Add support for recursive comparison of log messages with :class:`LogCapture`.

4.11.0 (12 October 2016)
------------------------

- Allow the attributes returned in :meth:`LogCapture.actual` rows to be
  specified.

- Allow a default to be specified for encoding in :meth:`TempDirectory.read` and
  :meth:`TempDirectory.write`.

4.10.1 (5 September 2016)
-------------------------

- Better docs for :meth:`TempDirectory.compare`.

- Remove the need for expected paths supplied to :meth:`TempDirectory.compare`
  to be in sorted order.

- Document a good way of restoring ``stdout`` when in a debugger.

- Fix handling of trailing slashes in :meth:`TempDirectory.compare`.

Thanks to Maximilian Albert for the :meth:`TempDirectory.compare` docs.

4.10.0 (17 May 2016)
--------------------

- Fixed examples in documentation broken in 4.5.1.

- Add :class:`RangeComparison` for comparing against values that fall in a
  range.

- Add :meth:`~popen.MockPopen.set_default` to :class:`~popen.MockPopen`.

Thanks to Asaf Peleg for the :class:`RangeComparison` implementation.

4.9.1 (19 February 2016)
------------------------

- Fix for use with PyPy, broken since 4.8.0.

Thanks to Nicola Iarocci for the pull request to fix.

4.9.0 (18 February 2016)
------------------------

- Added the `suffix` parameter to :func:`compare` to allow failure messages
  to include some additional context.

- Update package metadata to indicate Python 3.5 compatibility.

Thanks for Felix Yan for the metadata patch.

Thanks to Wim Glenn for the suffix patch.

4.8.0 (2 February 2016)
-----------------------

- Introduce a new :class:`Replace` context manager and make :class:`Replacer`
  callable. This gives more succinct and easy to read mocking code.

- Add :class:`ShouldWarn` and :class:`ShouldNotWarn` context managers.

4.7.0 (10 December 2015)
------------------------

- Add the ability to pass ``raises=False`` to :func:`compare` to just get
  the resulting message back rather than having an exception raised.

4.6.0 (3 December 2015)
------------------------

- Fix a bug that mean symlinked directories would never show up when using
  :meth:`TempDirectory.compare` and friends.

- Add the ``followlinks`` parameter to :meth:`TempDirectory.compare` to
  indicate that symlinked or hard linked directories should be recursed into
  when using ``recursive=True``.

4.5.1 (23 November 2015)
------------------------

- Switch from :class:`cStringIO` to :class:`StringIO` in :class:`OutputCapture`
  to better handle unicode being written to `stdout` or `stderr`.

Thanks to "tell-k" for the patch.

4.5.0 (13 November 2015)
------------------------

- :class:`LogCapture`, :class:`OutputCapture` and :class:`TempDirectory` now
  explicitly show what is expected versus actual when reporting differences.

Thanks to Daniel Fortunov for the pull request.

4.4.0 (1 November 2015)
-----------------------

- Add support for labelling the arguments passed to :func:`compare`.

- Allow ``expected`` and ``actual`` keyword parameters to be passed to
  :func:`compare`.

- Fix ``TypeError: unorderable types`` when :func:`compare` found multiple
  differences in sets and dictionaries on Python 3.

- Add official support for Python 3.5.

- Drop official support for Python 2.6.

Thanks to Daniel Fortunov for the initial ideas for explicit ``expected`` and
``actual`` support in :func:`compare`.

4.3.3 (15 September 2015)
-------------------------

- Add wheel distribution to release.

- Attempt to fix up various niggles from the move to Travis CI for doing
  releases.

4.3.2 (15 September 2015)
-------------------------

- Fix broken 4.3.1 tag.

4.3.1 (15 September 2015)
-------------------------

- Fix build problems introduced by moving the build process to Travis CI.

4.3.0 (15 September 2015)
-------------------------

- Add :meth:`TempDirectory.compare` with a cleaner, more explicit API that
  allows comparison of only the files in a temporary directory.

- Deprecate :meth:`TempDirectory.check`, :meth:`TempDirectory.check_dir`
  and :meth:`TempDirectory.check_all`

- Relax absolute-path rules so that if it's inside the :class:`TempDirectory`,
  it's allowed.

- Allow :class:`OutputCapture` to separately check output to ``stdout`` and
  ``stderr``.

4.2.0 (11 August 2015)
----------------------

- Add :class:`~testfixtures.popen.MockPopen`, a mock helpful when testing
  code that uses :class:`subprocess.Popen`.

- :class:`ShouldRaise` now subclasses :class:`object`, so that subclasses of it
  may use :meth:`super()`.

- Drop official support for Python 3.2.

Thanks to BATS Global Markets for donating the code for
:class:`~testfixtures.popen.MockPopen`.

4.1.2 (30 January 2015)
-----------------------

- Clarify documentation for ``name`` parameter to :class:`LogCapture`.

- :class:`ShouldRaise` now shows different output when two exceptions have
  the same representation but still differ.

- Fix bug that could result in a :class:`dict` comparing equal to a
  :class:`list`.

Thanks to Daniel Fortunov for the documentation clarification.

4.1.1 (30 October 2014)
-----------------------

- Fix bug that prevented logger propagation to be controlled by the
  :class:`log_capture` decorator.

Thanks to John Kristensen for the fix.

4.1.0 (14 October 2014)
-----------------------

- Fix :func:`compare` bug when :class:`dict` instances with
  :class:`tuple` keys were not equal.

- Allow logger propagation to be controlled by :class:`LogCapture`.

- Enabled disabled loggers if a :class:`LogCapture` is attached to them.

Thanks to Daniel Fortunov for the :func:`compare` fix.

4.0.2 (10 September 2014)
-------------------------

- Fix "maximum recursion depth exceeded" when comparing a string with
  bytes that did not contain the same character.

4.0.1 (4 August 2014)
---------------------

- Fix bugs when string compared equal and options to :func:`compare`
  were used.

- Fix bug when strictly comparing two nested structures containing
  identical objects.

4.0.0 (22 July 2014)
--------------------

- Moved from buildout to virtualenv for development.

- The ``identity`` singleton is no longer needed and has been
  removed.

- :func:`compare` will now work recursively on data structures for
  which it has registered comparers, giving more detailed feedback on
  nested data structures. Strict comparison will also be applied
  recursively.

- Re-work the interfaces for using custom comparers with
  :func:`compare`.

- Better feedback when comparing :func:`collections.namedtuple`
  instances.

- Official support for Python 3.4.

Thanks to Yevgen Kovalienia for the typo fix in :doc:`datetime`.

3.1.0 (25 May 2014)
-------------------

- Added :class:`RoundComparison` helper for comparing numerics to a
  specific precision.

- Added ``unless`` parameter to :class:`ShouldRaise` to cover
  some very specific edge cases.

- Fix missing imports that showed up :class:`TempDirectory` had to do
  the "convoluted folder delete" dance on Windows.

Thanks to Jon Thompson for the :class:`RoundComparison` implementation.

Thanks to Matthias Lehmann for the import error reports.

3.0.2 (7 April 2014)
--------------------

- Document :attr:`ShouldRaise.raised` and make it part of the official
  API. 

- Fix rare failures when cleaning up :class:`TempDirectory` instances
  on Windows.

3.0.1 (10 June 2013)
--------------------

- Some documentation tweaks and clarifications.

- Fixed a bug which masked exceptions when using :func:`compare` with
  a broken generator.

- Fixed a bug when comparing a generator with a non-generator.

- Ensure :class:`LogCapture` cleans up global state it may effect.

- Fixed replacement of static methods using a :class:`Replacer`.

3.0.0 (5 March 2013)
--------------------

- Added compatibility with Python 3.2 and 3.3.

- Dropped compatibility with Python 2.5.

- Removed support for the following obscure uses of
  :class:`should_raise`: 

  .. invisible-code-block: python

     from testfixtures.mock import MagicMock
     should_raise = x = MagicMock()

  .. code-block:: python

    should_raise(x, IndexError)[1]
    should_raise(x, KeyError)['x']

- Dropped the `mode` parameter to :meth:`TempDirectory.read`. 

- :meth:`TempDirectory.makedir` and :meth:`TempDirectory.write` no
  longer accept a `path` parameter.
  
- :meth:`TempDirectory.read` and :meth:`TempDirectory.write` now
  accept an `encoding` parameter to control how non-byte data is
  decoded and encoded respectively.

- Added the `prefix` parameter to :func:`compare` to allow failure
  messages to be made more informative.

- Fixed a problem when using sub-second deltas with :func:`test_time`.

2.3.5 (13 August 2012)
----------------------

- Fixed a bug in :func:`~testfixtures.comparison.compare_dict` that
  mean the list of keys that were the same was returned in an unsorted
  order.

2.3.4 (31 January 2012)
-----------------------

- Fixed compatibility with Python 2.5

- Fixed compatibility with Python 2.7

- Development model moved to continuous integration using Jenkins.

- Introduced `Tox`__ based testing to ensure packaging and
  dependencies are as expected.

  __ http://tox.testrun.org/latest/

- 100% line and branch coverage with tests.

- Mark :class:`test_datetime`, :class:`test_date` and
  :class:`test_time` such that nose doesn't mistake them as tests.

2.3.3 (12 December 2011)
-------------------------

- Fixed a bug where when a target was replaced more than once using a
  single :class:`Replacer`, :meth:`~Replacer.restore` would not
  correctly restore the original.

2.3.2 (10 November 2011)
-------------------------

- Fixed a bug where attributes and keys could not be
  removed by a :class:`Replacer` as described in
  :ref:`removing_attr_and_item` if the attribute or key might not be
  there, such as where a test wants to ensure an ``os.environ``
  variable is not set.

2.3.1 (8 November 2011)
-------------------------

- Move to use `nose <http://readthedocs.org/docs/nose/>`__ for running
  the TestFixtures unit tests.

- Fixed a bug where :meth:`tdatetime.now` returned an instance of the
  wrong type when `tzinfo` was passed in 
  :ref:`strict mode <strict-dates-and-times>`.

2.3.0 (11 October 2011)
-------------------------

- :class:`Replacer`, :class:`TempDirectory`, :class:`LogCapture` and
  :class:`~components.TestComponents` instances will now warn if the
  process they are created in exits without them being cleaned
  up. Instances of these classes should be cleaned up at the end of
  each test and these warnings serve to point to a cause for possible
  mysterious failures elsewhere.

2.2.0 (4 October 2011)
-------------------------

- Add a :ref:`strict mode <strict-dates-and-times>` to
  :class:`test_datetime` and :class:`test_date`. 
  When used, instances returned from the mocks are instances of those
  mocks. The default behaviour is now to return instances of the real
  :class:`~datetime.datetime` and :class:`~datetime.date` classes
  instead, which is usually much more useful.

2.1.0 (29 September 2011)
-------------------------

- Add a :ref:`strict mode <strict-comparison>` to
  :func:`compare`. When used, it ensures that
  the values compared are not only equal but also of the same
  type. This mode is not used by default, and the default mode
  restores the more commonly useful functionality where values of
  similar types but that aren't equal give useful feedback about
  differences.

2.0.1 (23 September 2011)
-------------------------

- add back functionality to allow comparison of generators with
  non-generators.

2.0.0 (23 September 2011)
-------------------------

- :func:`compare` now uses a registry of comparers that can be
  modified either by passing a `registry` option to :func:`compare`
  or, globally, using the :func:`~comparison.register` function.

- added a comparer for :class:`set` instances to :func:`compare`.

- added a new `show_whitespace` parameter to
  :func:`~comparison.compare_text`, the comparer used when comparing
  strings and unicodes with :func:`compare`.

- The internal queue for :class:`test_datetime` is now considered to
  be in local time. This has implication on the values returned from
  both :meth:`~tdatetime.now` and :meth:`~tdatetime.utcnow` when
  `tzinfo` is passed to the :class:`test_datetime` constructor.

- :meth:`set` and :meth:`add` on :class:`test_date`,
  :class:`test_datetime` and :class:`test_time` now accept instances
  of the appropriate type as an alternative to just passing in the
  parameters to create the instance.

- Refactored the monolithic ``__init__.py`` into modules for each
  type of functionality.

1.12.0 (16 August 2011)
-----------------------

- Add a :attr:`~OutputCapture.captured` property to
  :class:`OutputCapture` so that more complex assertion can be made
  about the output that has been captured.

- :class:`OutputCapture` context managers can now be temporarily
  disabled using their :meth:`~OutputCapture.disable` method.

- Logging can now be captured only when it exceeds a specified logging
  level.

- The handling of timezones has been reworked in both
  :func:`test_datetime` and :func:`test_time`. This is not backwards
  compatible but is much more useful and correct.

1.11.3 (3 August 2011)
----------------------

- Fix bugs where various :meth:`test_date`, :meth:`test_datetime` and
  :meth:`test_time` methods didn't accept keyword parameters.

1.11.2 (28 July 2011)
---------------------

- Fix for 1.10 and 1.11 releases that didn't include non-.py files as
  a result of the move from subversion to git.

1.11.1 (28 July 2011)
---------------------

- Fix bug where :meth:`tdatetime.now` didn't accept the `tz`
  parameter that :meth:`datetime.datetime.now` did.

1.11.0 (27 July 2011)
---------------------

- Give more useful output when comparing dicts and their subclasses.

- Turn :class:`should_raise` into a decorator form of
  :class:`ShouldRaise` rather than the rather out-moded wrapper
  function that it was.

1.10.0 (19 July 2011)
---------------------

- Remove dependency on :mod:`zope.dottedname`.

- Implement the ability to mock out :class:`dict` and :class:`list`
  items using :class:`~testfixtures.Replacer` and
  :func:`~testfixtures.replace`.

- Implement the ability to remove attributes and :class:`dict`
  items using :class:`~testfixtures.Replacer` and
  :func:`~testfixtures.replace`.

1.9.2 (20 April 2011)
---------------------

- Fix for issue #328: :meth:`~tdatetime.utcnow` of :func:`test_datetime`
  now returns items from the internal queue in the same way as 
  :meth:`~tdatetime.now`.

1.9.1 (11 March 2011)
------------------------

- Fix bug when :class:`ShouldRaise` context managers incorrectly
  reported what exception was incorrectly raised when the incorrectly
  raised exception was a :class:`KeyError`.

1.9.0 (11 February 2011)
------------------------

- Added :class:`~components.TestComponents` for getting a sterile
  registry when testing code that uses :mod:`zope.component`.

1.8.0 (14 January 2011)
-----------------------

- Added full Sphinx-based documentation.

- added a `Manuel <http://packages.python.org/manuel/>`__ plugin for
  reading and writing files into a :class:`TempDirectory`.

- any existing log handlers present when a :class:`LogCapture` is
  installed for a particular logger are now removed.

- fix the semantics of :class:`should_raise`, which should always
  expect an exception to be raised!

- added the :class:`ShouldRaise` context manager.

- added recursive support to :meth:`TempDirectory.listdir` and added
  the new :meth:`TempDirectory.check_all` method.

- added support for forward-slash separated paths to all relevant
  :class:`TempDirectory` methods.

- added :meth:`TempDirectory.getpath` method.

- allow files and directories to be ignored by a regular expression
  specification when using :class:`TempDirectory`.

- made :class:`Comparison` objects work when the attributes expected
  might be class attributes.

- re-implement :func:`test_time` so that it uses the correct way to
  get timezone-less time.

- added :meth:`~tdatetime.set` along with `delta` and `delta_type`
  parameters to :func:`test_date`, :func:`test_datetime` and
  :func:`test_time`.

- allow the date class returned by the :meth:`tdatetime.date` method
  to be configured.

- added the :class:`OutputCapture` context manager.

- added the :class:`StringComparison` class.

- added options to ignore trailing whitespace and blank lines when
  comparing multi-line strings with :func:`compare`.

- fixed bugs in the handling of some exception types when using
  :class:`Comparison`, :class:`ShouldRaise` or :class:`should_raise`.

- changed :func:`wrap` to correctly set __name__, along with some
  other attributes, which should help when using the decorators with
  certain testing frameworks.

1.7.0 (20 January 2010)
-----------------------

- fixed a bug where the @replace decorator passed a classmethod
  rather than the replacment to the decorated callable when replacing
  a classmethod

- added set method to test_date, test_datetime and test_time to allow
  setting the parameters for the next instance to be returned.

- added delta and delta_type parameters to test_date,test_datetime and
  test_time to control the intervals between returned instances.


1.6.2 (23 September 2009)
-------------------------

- changed Comparison to use __eq__ and __ne__ instead of the
  deprecated __cmp__

- documented that order matters when using Comparisons with objects
  that implement __eq__ themselves, such as instances of Django
  models.

1.6.1 (06 September 2009)
-------------------------

- @replace and Replacer.replace can now replace attributes that may
  not be present, provided the `strict` parameter is passed as False.

- should_raise now catches BaseException rather than Exception so
  raising of SystemExit and KeyboardInterrupt can be tested.

1.6.0 (09 May 2009)
-------------------

- added support for using TempDirectory, Replacer and LogCapture as
  context managers.

- fixed test failure in Python 2.6.

1.5.4 (11 Feb 2009)
-------------------

- fix bug where should_raise didn't complain when no exception 
  was raised but one was expected.

- clarified that the return of a should_raise call will be None
  in the event that an exception is raised but no expected 
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
