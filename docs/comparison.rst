.. _comparison-objects:

Comparison objects
==================

.. currentmodule:: testfixtures

.. invisible-code-block: python

    from testfixtures import compare
    from testfixtures.compat import PY_312_PLUS

Another common problem with the checking in tests is that you may only want to make
assertions about the type of an object that is nested in a data structure, or even just compare
a subset of an object's attributes. Testfixtures provides the :class:`~testfixtures.Comparison`
class to help in situations like these.

Comparisons will appear to be equal to any object they are compared
with that matches their specification. For example, take the following
class: 

.. code-block:: python

  class SomeClass:

      def __init__(self, x, y):
         self.x, self.y = x, y

When a comparison fails, the :class:`~testfixtures.Comparison` will not equal the object it
was compared with and its representation changes to give information about what went wrong:

>>> from testfixtures import Comparison as C
>>> c = C(SomeClass, x=2)
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

Types of comparison
~~~~~~~~~~~~~~~~~~~

There are several ways a comparison can be set up depending on what
you want to check.

If you only care about the type of an object, you can set up the
comparison with only the class:

>>> C(SomeClass) == SomeClass(1, 2)
True

This can also be achieved by specifying the type of the object as a
dotted name:

>>> import sys
>>> C('types.ModuleType') == sys
True

Alternatively, if you happen to have an object already
around, comparison can be done with it:

>>> C(SomeClass(1, 2)) == SomeClass(1, 2)
True

If you only care about certain attributes, this can also easily be
achieved by doing a partial comparison:

>>> C(SomeClass, x=1, partial=True) == SomeClass(1, 2)
True

The above can be problematic if you want to compare an object with
attributes that share names with parameters to the :class:`~testfixtures.Comparison`
constructor. For this reason, you can pass the attributes in a
dictionary:

>>> compare(C(SomeClass, {'partial': 3}, partial=True), SomeClass(1, 2))
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
~~~~~~~

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

  >>> SomeModel() == C(SomeModel)
  False

  However, if the comparison is correctly placed first, then
  everything will behave as expected:

  >>> C(SomeModel)==SomeModel()
  True

- It probably goes without saying, but comparisons should not be used
  on both sides of an equality check:

  >>> C(SomeClass) == C(SomeClass)
  False


.. _mappingcomparison:

Mapping Comparison objects
---------------------------

When comparing mappings such as :class:`dict` and :class:`~collections.OrderedDict`,
you may need to check the order of the keys is as you expect.
:class:`MappingComparison` objects can be used for this:

.. skip: start if(not PY_312_PLUS, reason="Python 3.12 has nicer reprs")

>>> from collections import OrderedDict
>>> from testfixtures import compare, MappingComparison as M
>>> compare(expected=M((('a', 1), ('c', 3), ('d', 2)), ordered=True),
...         actual=OrderedDict((('a', 1), ('d', 2), ('c', 3))))
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

>>> compare(expected=M(a=1, d=2, partial=True), actual={'a': 1, 'c': 3})
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

>>> compare(expected=M((('a', [1, 2]), ('d', [1, 3])), ordered=True, recursive=True),
...         actual=OrderedDict((('a', [1, 2]), ('d', [1, 4]))))
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

Round Comparison objects
-------------------------

When comparing numerics you often want to be able to compare to a 
given precision to allow for rounding issues which make precise
equality impossible.

For these situations, you can use :class:`RoundComparison` objects
wherever you would use floats or Decimals, and they will compare equal to
any float or Decimal that matches when both sides are rounded to the
specified precision.

Here's an example:

.. code-block:: python

  from testfixtures import compare, RoundComparison as R

  compare(expected=R(1234.5678, 2), actual=1234.5681)

.. note:: 

  You should always pass the same type of object to the
  :class:`RoundComparison` object as you intend to compare it with. If
  the type of the rounded expected value is not the same as the type of
  the rounded value it is being compared to, a :class:`TypeError`
  will be raised.

.. _rangecomparison:

Range Comparison objects
-------------------------

When comparing numbers, dates, times and any other type that can be ordered, you may only
want to assert what range a value will fall into. :class:`RangeComparison` objects
let you confirm a value is within a certain tolerance or range.

Here's an example with numbers:

.. code-block:: python

  from decimal import Decimal
  from testfixtures import compare, RangeComparison as R

  compare(expected=R(123.456, 789), actual=Decimal(555.01))

Here's an example with dates:

.. code-block:: python

  from datetime import date
  from testfixtures import compare, RangeComparison as R

  compare(expected=R(date(1978, 6, 13), date(1978, 10, 31)), actual=date(1978, 7, 1))

.. note::

  :class:`RangeComparison` is inclusive of both the lower and upper bound.

.. _sequencecomparison:

Sequence Comparison objects
---------------------------

When comparing sequences, you may not care about the order of items in the
sequence. While this type of comparison can often be achieved by pouring
the sequence into a :class:`set`, this may not be possible if the items in the
sequence are unhashable, or part of a nested data structure.
:class:`SequenceComparison` objects can be used in this case:

>>> from testfixtures import compare, SequenceComparison as S
>>> compare(expected={'k': S({1}, {2}, ordered=False)}, actual={'k': [{2}, {1}]})

You may also only care about certain items being present in a sequence, but where
it is important that those items are in the order you expected. This
can also be achieved with :class:`SequenceComparison` objects:

>>> compare(expected=S(1, 3, 5, partial=True), actual=[1, 2, 3, 4, 6])
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

>>> compare(expected=S({1: 'a'}, {2: 'c'}, recursive=True), actual=[{1: 'a'}, {2: 'd'}])
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

.. _stringcomparison:

String Comparison objects
-------------------------

When comparing sequences of strings, particularly those coming from
things like the python logging package, you often end up wanting to
express a requirement that one string should be almost like another,
or maybe fit a particular pattern expressed as a regular expression.

For these situations, you can use :class:`StringComparison` objects
wherever you would use normal strings, and they will compare equal to
any string that matches the regular expression they are created with.

Here's an example:

.. code-block:: python

  from testfixtures import compare, StringComparison as S

  compare(expected=S(r'Starting thread \d+'), actual='Starting thread 132356')

If you need to specify flags, this can be done in one of three ways:

- As parameters:

  .. code-block:: python

    compare(expected=S(".*BaR", dotall=True, ignorecase=True), actual="foo\nbar")


- As you would to :func:`re.compile`:

  .. code-block:: python

    import re
    compare(expected=S(".*BaR", re.DOTALL|re.IGNORECASE), actual="foo\nbar")

- Inline:

  .. code-block:: python

    compare(expected=S("(?s:.*bar)"), actual="foo\nbar")

Type-safe comparisons
---------------------

When working with type checkers like `mypy`__, helpers such as :class:`Comparison` and
:class:`SequenceComparison` can cause type errors because they don't match the types you're
comparing against. Several helper functions are provided that create comparisons while keeping type
checkers happy.

__ https://mypy-lang.org/

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
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

Configurable sequence comparisons with ``sequence()``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :func:`~testfixtures.sequence` function provides flexible sequence
comparisons with control over ordering and partial matching:

>>> from testfixtures import sequence
>>> actual = Container([SampleClass(1, 'x'), SampleClass(2, 'x'), SampleClass(3, 'x')])
>>> compare(
...     actual,
...     expected=Container(
...         sequence(partial=True, ordered=False)([
...             SampleClass(3, 'x'),
...             SampleClass(2, 'x'),
...         ])
...     ),
... )

When comparing sequences of different types, use the ``returns`` parameter:

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
