Testing warnings
================

.. currentmodule:: testfixtures

Testfixtures has tools that make it easy to make assertions about code that may emit warnings.

The :class:`ShouldWarn` context manager
---------------------------------------

This context manager allows you to assert that particular warnings are
emitted in a block of code, for example:

>>> from warnings import warn
>>> from testfixtures import ShouldWarn
>>> with ShouldWarn(UserWarning('you should fix that')):
...     warn('you should fix that')

If a warning issued doesn't match the one expected,
:class:`ShouldWarn` will raise an :class:`AssertionError`
causing the test in which it occurs to fail:

>>> from warnings import warn
>>> from testfixtures import ShouldWarn
>>> with ShouldWarn(UserWarning('you should fix that')):
...     warn("sorry dave, I can't let you do that")
Traceback (most recent call last):
...
AssertionError:...
<SequenceComparison(ordered=True, partial=False)(failed)>
same:
[]
<BLANKLINE>
expected:
[
<C:....UserWarning(failed)>
attributes differ:
'args': ('you should fix that',) (Comparison) != ("sorry dave, I can't let you do that",) (actual)
</C:....UserWarning>]
<BLANKLINE>
actual:
[UserWarning("sorry dave, I can't let you do that"...)]
</SequenceComparison(ordered=True, partial=False)> (expected) != [UserWarning("sorry dave, I can't let you do that"...)] (actual)

You can check multiple warnings in a particular piece of code:

>>> from warnings import warn
>>> from testfixtures import ShouldWarn
>>> with ShouldWarn(UserWarning('you should fix that'),
...                 UserWarning('and that too')):
...     warn('you should fix that')
...     warn('and that too')

If you don't care about the order of issued warnings, you can use ``order_matters=False``:

>>> from warnings import warn
>>> from testfixtures import ShouldWarn
>>> with ShouldWarn(UserWarning('you should fix that'),
...                 UserWarning('and that too'),
...                 order_matters=False):
...     warn('and that too')
...     warn('you should fix that')

If you want to inspect more details of the warnings issued, you can capture
them into a list as follows:

>>> from warnings import warn_explicit
>>> from testfixtures import ShouldWarn
>>> with ShouldWarn() as captured:
...     warn_explicit(message='foo', category=DeprecationWarning,
...                   filename='bar.py', lineno=42)
>>> len(captured)
1
>>> captured[0].message
DeprecationWarning('foo'...)
>>> captured[0].lineno
42

The :class:`ShouldNotWarn` context manager
------------------------------------------

If you do not expect any warnings to be logged in a piece of code, you can use
the :class:`ShouldNotWarn` context manager. If any warnings are issued in the
context it manages, it will raise an :class:`AssertionError` to indicate this:

>>> from warnings import warn
>>> from testfixtures import ShouldNotWarn
>>> with ShouldNotWarn():
...     warn("woah dude")
Traceback (most recent call last):
...
AssertionError:...
<SequenceComparison(ordered=True, partial=False)(failed)>
same:
[]
<BLANKLINE>
expected:
[]
<BLANKLINE>
actual:
[UserWarning('woah dude'...)]
</SequenceComparison(ordered=True, partial=False)> (expected) != [UserWarning('woah dude'...)] (actual)
