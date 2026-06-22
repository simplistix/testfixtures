.. _comparison-objects:

Comparison objects and matchers
===============================

.. currentmodule:: testfixtures

.. invisible-code-block: python

    from testfixtures import compare
    from testfixtures.compat import PY_312_PLUS

Often you want to assert that a value *matches* a specification rather than being
exactly equal to something: that it is an instance of a particular type, that
only some of its attributes matter, that a number falls within a range, or that a
string matches a pattern. Functions and objects are provided that express
these expectations and slot into the expected side of :func:`compare`, or into a
plain ``assert``.

The typed helpers :func:`like`, :func:`sequence`, :func:`contains` and
:func:`unordered` are the place to start. They are typed to match the values you
compare against, so they keep type checkers such as `mypy`__ happy. Under the
hood they build the comparison objects described below, which you can also
construct directly when you need one that has no helper.

__ https://mypy-lang.org/

Some expectations have no helper and are used as objects directly:
:ref:`RangeComparison <rangecomparison>` and :ref:`RoundComparison <roundcomparison>` for numbers,
:ref:`MappingComparison <mappingcomparison>` for mappings, and
:ref:`StringComparison <stringcomparison>` for matching against a regular expression.

The examples below use these dataclasses:

.. code-block:: python

  from dataclasses import dataclass

  @dataclass
  class SampleClass:
      x: int
      y: str

  @dataclass
  class Container:
      items: list[SampleClass]

  @dataclass
  class TupleContainer:
      items: tuple[SampleClass, ...]

Partial object comparisons with ``like()``
------------------------------------------

The :func:`~testfixtures.like` function creates partial object comparisons
that are typed to match the class being compared:

>>> from testfixtures import compare, like
>>> expected: list[SampleClass] = [like(SampleClass, x=1)]
>>> compare(expected, actual=[SampleClass(1, '2')])

You can use :func:`~testfixtures.like` anywhere you need a partial comparison,
including in assertions:

>>> expected: SampleClass = like(SampleClass)
>>> assert expected == SampleClass(1, '2')
>>> assert expected == SampleClass(3, '4')

``like()`` always builds a partial :ref:`Comparison <comparison>`. Reach for a
:ref:`Comparison <comparison>` directly when you need to match by type alone, by
dotted import path, against an existing instance, or matching exactly rather than
partially.

Sequence helpers
----------------

:func:`sequence`, :func:`contains` and :func:`unordered` compare sequences
flexibly and all return :ref:`SequenceComparison <sequencecomparison>` objects.
:func:`contains` and :func:`unordered` are the typed equivalents of the
:class:`Subset` and :class:`Permutation` shortcuts.

Configurable sequence comparisons with ``sequence()``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :func:`~testfixtures.sequence` function builds a flexible sequence matcher
with control over ordering, partial matching and recursion.

By default the items must match exactly and in order. Pass ``partial=True`` to
ignore any additional items:

>>> from testfixtures import sequence
>>> compare(expected=sequence(partial=True)([1, 2]), actual=[1, 2, 3])

If you only care that certain items are present, :func:`contains` says this more
concisely.

Pass ``ordered=False`` to ignore the order of the items:

>>> compare(expected=sequence(ordered=False)([2, 1]), actual=[1, 2])

For a full match in any order, :func:`unordered` says this more concisely.

Pass ``recursive=True`` to explain the first item that differs rather than just
listing the items that were not matched:

>>> compare(expected=sequence(recursive=True)([{'k': 1}]), actual=[{'k': 2}])
Traceback (most recent call last):
 ...
AssertionError: not equal:
<BLANKLINE>
<SequenceComparison(ordered=True, partial=False)(failed)>
same:
[]
<BLANKLINE>
expected:
[{'k': 1}]
<BLANKLINE>
actual:
[{'k': 2}]
<BLANKLINE>
While comparing [0]: dict not as expected:
<BLANKLINE>
values differ:
'k': 1 (expected) != 2 (actual)
</SequenceComparison(ordered=True, partial=False)> (expected)
[{'k': 2}] (actual)

Type checkers will complain unless :class:`!TupleContainer` is instantiated with a
:class:`tuple` of :class:`!SampleClass` instances, so pass the ``returns``
parameter for the result to be typed correctly:

>>> actual = TupleContainer((SampleClass(1, 'x'), SampleClass(2, 'x')))
>>> compare(
...     actual,
...     expected=TupleContainer(
...         sequence(returns=tuple[SampleClass, ...])([
...             SampleClass(1, 'x'),
...             SampleClass(2, 'x'),
...         ])
...     ),
... )

To assert that a value is specifically a generator rather than just something
that yields the right items, build the expected value with :func:`generator` and
use :ref:`strict comparison <strict-comparison>`.

Checking for item presence with ``contains()``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :func:`~testfixtures.contains` function checks that specified items
are present, regardless of order or additional items:

>>> from testfixtures import contains
>>> actual = Container([SampleClass(1, '2'), SampleClass(3, '4'), SampleClass(5, '6')])
>>> compare(
...     actual,
...     expected=Container(contains([SampleClass(1, '2'), SampleClass(3, '4')]))
... )

Use the ``returns`` parameter when needed for type compatibility:

>>> actual = TupleContainer((SampleClass(1, '2'), SampleClass(3, '4'), SampleClass(5, '6')))
>>> compare(
...     actual,
...     expected=TupleContainer(
...         contains([SampleClass(1, '2')], returns=tuple[SampleClass, ...])
...     ),
... )

Order-independent full matches with ``unordered()``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :func:`~testfixtures.unordered` function checks that sequences contain
exactly the same items, but in any order:

>>> from testfixtures import unordered
>>> actual = Container([SampleClass(2, 'x'), SampleClass(1, 'x')])
>>> compare(
...     actual,
...     expected=Container(
...         unordered([SampleClass(1, 'x'), SampleClass(2, 'x')])
...     ),
... )

Use the ``returns`` parameter for type compatibility:

>>> actual = TupleContainer((SampleClass(2, 'x'), SampleClass(1, 'x')))
>>> compare(
...     actual,
...     expected=TupleContainer(
...         unordered([SampleClass(1, 'x'), SampleClass(2, 'x')], returns=tuple[SampleClass, ...])
...     ),
... )

Comparison objects
------------------

The helpers above build these objects, and you can construct them directly. A
:ref:`Comparison <comparison>`, returned by :func:`like`, and a
:ref:`SequenceComparison <sequencecomparison>`, returned by :func:`sequence`,
:func:`contains` and :func:`unordered`, are usually an implementation detail. The
rest have no helper and are meant to be used directly.

.. _comparison:

``Comparison``
~~~~~~~~~~~~~~

A :class:`~testfixtures.Comparison` is what :func:`like` returns. It compares
equal to any object of the same type whose attributes match those you specify,
even when that type does not support equality itself. For example, take this
class:

.. code-block:: python

  class SomeClass:

      def __init__(self, x, y):
         self.x, self.y = x, y

When a comparison fails, the :class:`~testfixtures.Comparison` will not equal the object it
was compared with and its representation changes to give information about what was different:

>>> from testfixtures import Comparison
>>> c = Comparison(SomeClass, x=2)
>>> print(repr(c))
<C:...SomeClass>x: 2</>
>>> c == SomeClass(1, 2)
False
>>> print(repr(c))
<BLANKLINE>
<C:...SomeClass(failed)>
attributes in actual but not Comparison:
'y': 2
<BLANKLINE>
attributes differ:
'x': 2 (Comparison) != 1 (actual)
</C:...SomeClass>

.. note:: 

   Some test frameworks and helpers, including :meth:`~unittest.TestCase.assertEqual`,
   truncate the text shown in assertions. Use :func:`compare` instead, which will
   give you other desirable behaviour as well as showing you the full
   output of failed comparisons.

There are several ways a comparison can be set up depending on what
you want to check.

If you only care about the type of an object, you can set up the
comparison with only the class:

>>> Comparison(SomeClass) == SomeClass(1, 2)
True

This can also be achieved by specifying the type of the object as a
dotted name:

>>> import sys
>>> Comparison('types.ModuleType') == sys
True

Alternatively, if you happen to have an object already
around, comparison can be done with it:

>>> Comparison(SomeClass(1, 2)) == SomeClass(1, 2)
True

If you only care about certain attributes, this can also easily be
achieved by doing a partial comparison:

>>> Comparison(SomeClass, x=1, partial=True) == SomeClass(1, 2)
True

The above can be problematic if you want to compare an object with
attributes that share names with parameters to the :class:`~testfixtures.Comparison`
constructor. For this reason, you can pass the attributes in a
dictionary:

>>> compare(
...     Comparison(SomeClass, {'partial': 3}, partial=True),
...     SomeClass(1, 2),
... )
Traceback (most recent call last):
 ...
AssertionError: not equal:
<BLANKLINE>
<C:...SomeClass(failed)>
attributes in Comparison but not actual:
'partial': 3
</C:...SomeClass>
<...SomeClass...>

Gotchas
^^^^^^^

- If the object being compared has an ``__eq__`` method, such as
  Django model instances, then the :class:`~testfixtures.Comparison`
  must be the first object in the equality check.

  The following class is an example of this:

  .. code-block:: python

        class SomeModel:
            def __eq__(self,other):
                if isinstance(other, SomeModel):
                    return True
                return False
  
  It will not work correctly if used as the second object in the
  expression:

  >>> SomeModel() == Comparison(SomeModel)
  False

  However, if the comparison is correctly placed first, then
  everything will behave as expected:

  >>> Comparison(SomeModel)==SomeModel()
  True

- It probably goes without saying, but comparisons should not be used
  on both sides of an equality check:

  >>> Comparison(SomeClass) == Comparison(SomeClass)
  False

.. _sequencecomparison:

``SequenceComparison``
~~~~~~~~~~~~~~~~~~~~~~

When comparing sequences, you may not care about the order of items in the
sequence. While this type of comparison can often be achieved by pouring
the sequence into a :class:`set`, this may not be possible if the items in the
sequence are unhashable, or part of a nested data structure.
:class:`SequenceComparison` objects can be used in this case:

>>> from testfixtures import compare, SequenceComparison
>>> compare(
...     expected={'k': SequenceComparison({1}, {2}, ordered=False)},
...     actual={'k': [{2}, {1}]},
... )

You may also only care about certain items being present in a sequence, but where
it is important that those items are in the order you expected. This
can also be achieved with :class:`SequenceComparison` objects:

>>> compare(
...     expected=SequenceComparison(1, 3, 5, partial=True),
...     actual=[1, 2, 3, 4, 6],
... )
Traceback (most recent call last):
 ...
AssertionError: not equal:
<BLANKLINE>
<SequenceComparison(ordered=True, partial=True)(failed)>
ignored:
[2, 4, 6]
<BLANKLINE>
same:
[1, 3]
<BLANKLINE>
expected:
[5]
<BLANKLINE>
actual:
[]
</SequenceComparison(ordered=True, partial=True)> (expected)
[1, 2, 3, 4, 6] (actual)

Where there are differences, they may be hard to spot. In this case, you can ask for a more
detailed explanation of what wasn't as expected:

>>> compare(
...     expected=SequenceComparison({1: 'a'}, {2: 'c'}, recursive=True),
...     actual=[{1: 'a'}, {2: 'd'}],
... )
Traceback (most recent call last):
 ...
AssertionError: not equal:
<BLANKLINE>
<SequenceComparison(ordered=True, partial=False)(failed)>
same:
[{1: 'a'}]
<BLANKLINE>
expected:
[{2: 'c'}]
<BLANKLINE>
actual:
[{2: 'd'}]
<BLANKLINE>
While comparing [1]: dict not as expected:
<BLANKLINE>
values differ:
2: 'c' (expected) != 'd' (actual)
<BLANKLINE>
While comparing [1][2]: 'c' (expected) != 'd' (actual)
</SequenceComparison(ordered=True, partial=False)> (expected)
[{1: 'a'}, {2: 'd'}] (actual)

There are also the :class:`Subset` and :class:`Permutation` shortcuts:

>>> from testfixtures import Subset, Permutation
>>> assert Subset({1}, {2}) == [{1}, {2}, {3}]
>>> assert Permutation({1}, {2}) == [{2}, {1}]

.. _mappingcomparison:

``MappingComparison``
~~~~~~~~~~~~~~~~~~~~~

When comparing mappings such as :class:`dict` and :class:`~collections.OrderedDict`,
you may need to check the order of the keys is as you expect.
:class:`MappingComparison` objects can be used for this:

.. skip: start if(not PY_312_PLUS, reason="Python 3.12 has nicer reprs")

>>> from collections import OrderedDict
>>> from testfixtures import compare, MappingComparison
>>> compare(
...     expected=MappingComparison((('a', 1), ('c', 3), ('d', 2)), ordered=True),
...     actual=OrderedDict((('a', 1), ('d', 2), ('c', 3))),
... )
Traceback (most recent call last):
 ...
AssertionError: not equal:
<BLANKLINE>
<MappingComparison(ordered=True, partial=False)(failed)>
wrong key order:
<BLANKLINE>
same:
['a']
<BLANKLINE>
expected:
['c', 'd']
<BLANKLINE>
actual:
['d', 'c']
</MappingComparison(ordered=True, partial=False)> (expected)
OrderedDict({'a': 1, 'd': 2, 'c': 3}) (actual)

You may also only care about certain keys being present in a mapping. This
can also be achieved with :class:`MappingComparison` objects:

>>> compare(
...     expected=MappingComparison(a=1, d=2, partial=True),
...     actual={'a': 1, 'c': 3},
... )
Traceback (most recent call last):
 ...
AssertionError: not equal:
<BLANKLINE>
<MappingComparison(ordered=False, partial=True)(failed)>
ignored:
['c']
<BLANKLINE>
same:
['a']
<BLANKLINE>
in expected but not actual:
'd': 2
</MappingComparison(ordered=False, partial=True)> (expected)
{'a': 1, 'c': 3} (actual)

Where there are differences, they may be hard to spot. In this case, you can ask for a more
detailed explanation of what wasn't as expected:

>>> compare(
...     expected=MappingComparison(
...         (('a', [1, 2]), ('d', [1, 3])), ordered=True, recursive=True
...     ),
...     actual=OrderedDict((('a', [1, 2]), ('d', [1, 4]))),
... )
Traceback (most recent call last):
 ...
AssertionError: not equal:
<BLANKLINE>
<MappingComparison(ordered=True, partial=False)(failed)>
same:
['a']
<BLANKLINE>
values differ:
'd': [1, 3] (expected) != [1, 4] (actual)
<BLANKLINE>
While comparing ['d']: sequence not as expected:
<BLANKLINE>
same:
[1]
<BLANKLINE>
expected:
[3]
<BLANKLINE>
actual:
[4]
</MappingComparison(ordered=True, partial=False)> (expected)
OrderedDict({'a': [1, 2], 'd': [1, 4]}) (actual)

.. skip: end

.. _roundcomparison:

``RoundComparison``
~~~~~~~~~~~~~~~~~~~

When comparing numerics you often want to be able to compare to a 
given precision to allow for rounding issues which make precise
equality impossible.

For these situations, you can use :class:`RoundComparison` objects
wherever you would use floats or Decimals, and they will compare equal to
any float or Decimal that matches when both sides are rounded to the
specified precision.

Here's an example:

.. code-block:: python

  from testfixtures import compare, RoundComparison

  compare(
      expected=RoundComparison(1234.5678, precision=2),
      actual=1234.5681,
  )

.. note:: 

  You should always pass the same type of object to the
  :class:`RoundComparison` object as you intend to compare it with. If
  the type of the rounded expected value is not the same as the type of
  the rounded value it is being compared to, a :class:`TypeError`
  will be raised.

.. _rangecomparison:

``RangeComparison``
~~~~~~~~~~~~~~~~~~~

When comparing numbers, dates, times and any other type that can be ordered, you may only
want to assert what range a value will fall into. :class:`RangeComparison` objects
let you confirm a value is within a certain tolerance or range.

Here's an example with numbers:

.. code-block:: python

  from decimal import Decimal
  from testfixtures import compare, RangeComparison

  compare(
      expected=RangeComparison(123.456, 789),
      actual=Decimal(555.01),
  )

Here's an example with dates:

.. code-block:: python

  from datetime import date
  from testfixtures import compare, RangeComparison

  compare(
      expected=RangeComparison(date(1978, 6, 13), date(1978, 10, 31)),
      actual=date(1978, 7, 1),
  )

.. note::

  :class:`RangeComparison` is inclusive of both the lower and upper bound.

.. _stringcomparison:

``StringComparison``
~~~~~~~~~~~~~~~~~~~~

When comparing sequences of strings, particularly those coming from
things like the python logging package, you often end up wanting to
express a requirement that one string should be almost like another,
or maybe fit a particular pattern expressed as a regular expression.

For these situations, you can use :class:`StringComparison` objects
wherever you would use normal strings, and they will compare equal to
any string that matches the regular expression they are created with.

Here's an example:

.. code-block:: python

  from testfixtures import compare, StringComparison

  compare(
      expected=StringComparison(r'Starting thread \d+'),
      actual='Starting thread 132356',
  )

If you need to specify flags, this can be done in one of three ways:

- As parameters:

  .. code-block:: python

    compare(
        expected=StringComparison(".*BaR", dotall=True, ignorecase=True),
        actual="foo\nbar",
    )


- As you would to :func:`re.compile`:

  .. code-block:: python

    import re
    compare(
        expected=StringComparison(".*BaR", re.DOTALL|re.IGNORECASE),
        actual="foo\nbar",
    )

- Inline:

  .. code-block:: python

    compare(
        expected=StringComparison("(?s:.*bar)"),
        actual="foo\nbar",
    )
