Finding and explaining differences
==================================

.. currentmodule:: testfixtures

.. invisible-code-block: python

    from collections import namedtuple

The :func:`compare` function checks that two values are equal and, when they are
not, explains *how* they differ. Reach for it instead of
:meth:`~unittest.TestCase.assertEqual` or a plain ``assert``: it offers much more
:ref:`flexible <flexible>` and :ref:`configurable <comparer-register>`
comparison, and far clearer feedback when a check fails, particularly for
deeply nested data structures, objects that don't
:ref:`natively support equality checking <comparer-objects>`, and objects that do
:ref:`silly things <ignore-eq>` when compared.

By default a failed comparison is raised as an :class:`AssertionError`, so it
reads as an assertion in your tests. If you would rather examine the difference
yourself, pass ``raises=False`` and :func:`compare` returns the explanation as
text instead of raising it.

If, instead of checking for *exact* equality, you want to assert that a value
merely *matches* a specification, such as a partial object, a number within a range, a
string matching a pattern, or a sequence in any order, use the flexible
:ref:`comparison objects and matchers <comparison-objects>`. They slot into the
expected side of :func:`compare`, and into plain ``assert`` statements.

Comparing expected and actual
-----------------------------

In its simplest form, :func:`compare` takes two values and raises an
:class:`AssertionError` if they are not equal:

>>> from testfixtures import compare
>>> compare(1, 2)
Traceback (most recent call last):
 ...
AssertionError: 1 != 2

The expected and actual value can also be explicitly supplied, making it clearer as to what has gone
wrong:

>>> compare(expected=1, actual=2)
Traceback (most recent call last):
 ...
AssertionError: 1 (expected) != 2 (actual)

Only one of these needs to be specified, the other will then be inferred:

>>> actual = '123' + '456'
>>> compare(actual, expected='123457')
Traceback (most recent call last):
 ...
AssertionError: '123457' (expected) != '123456' (actual)

However, if there are more specific labels that would be more useful, they can be supplied:

>>> compare(1001, 1002, x_label='realised', y_label='unrealised')
Traceback (most recent call last):
 ...
AssertionError: 1001 (realised) != 1002 (unrealised)

A prefix can also be specified for the message to be used
in the event of failure:

>>> compare(expected=1, actual=2, prefix='wrong number of orders')
Traceback (most recent call last):
 ...
AssertionError: wrong number of orders: 1 (expected) != 2 (actual)

You can also optionally specify a suffix, which will be appended to the
message on a new line:

>>> compare(expected=1, actual=2, suffix='(Except for very large values of 1)')
Traceback (most recent call last):
 ...
AssertionError: 1 (expected) != 2 (actual)
(Except for very large values of 1)

Sometimes the feedback you wish to provide can be expensive to compute, and so you will only
want to do this in the event the comparison fails. This can be done by providing a callable to either
``prefix`` or ``suffix``:

>>> compare(expected=1, actual=2, suffix=lambda: 'This is very expensive to compute...')
Traceback (most recent call last):
 ...
AssertionError: 1 (expected) != 2 (actual)
This is very expensive to compute...

The real strengths of :func:`compare` show when comparing more complex and
nested data: for many built-in types it pinpoints *where* the values differ
rather than simply reporting that they are unequal. See :ref:`compare-types` for
the full catalog of how each type is handled.

.. _flexible:

Controlling the comparison
--------------------------

Several keyword arguments change how :func:`compare` decides whether two values
are equal.

.. _strict-comparison:

Strict comparison
~~~~~~~~~~~~~~~~~

By default, :func:`compare` is lenient: it accepts any reasonable notion of
equality. It treats values of different but compatible types as equal, and lets
some comparers apply their own tolerances. That is usually what you want when
checking a result.

Strict mode removes that leniency at every level. It asks whether the two values
are *identical*: of exactly the same type, with their contents inspected directly
and no tolerance applied anywhere. Reach for it when a difference the default
would forgive actually matters.

The most obvious leniency is over type. By default a :class:`list` matches a
:class:`tuple` with the same items, but strict mode rejects it:

>>> compare([1, 2], (1, 2))
>>> compare([1, 2], (1, 2), strict=True)
Traceback (most recent call last):
 ...
AssertionError: [1, 2] (<class 'list'>) != (1, 2) (<class 'tuple'>)

This catches differences between types that are otherwise treated as
interchangeable. For example, two different :func:`~collections.namedtuple`
classes compare equal by value but not under strict mode:

>>> TypeA = namedtuple('A', 'x')
>>> TypeB = namedtuple('B', 'x')
>>> compare(TypeA(1), TypeB(1))
>>> compare(TypeA(1), TypeB(1), strict=True)
Traceback (most recent call last):
 ...
AssertionError: A(x=1) (<class '__test__.A'>) != B(x=1) (<class '__test__.B'>)

This is also how you assert that a function returns a
:ref:`generator <compare-generators>` rather than some other iterable, since by
default :func:`compare` unwinds a generator and compares its contents like any
other sequence.

The same principle reaches into individual comparers: where one would normally
allow some leeway, strict mode asks for an exact match instead. For example,
:func:`compare` permits the small floating point differences that
:doc:`pandas <pandas>` and :doc:`polars <polars>` tolerate between dataframes,
while strict mode requires them to be exactly equal.

.. _ignore-attributes:

Ignoring attributes
~~~~~~~~~~~~~~~~~~~

When comparing objects, there may be attributes that you don't care about or cannot easily
control, such as timestamps or auto-generated IDs. For example, consider this class:

.. code-block:: python

  from datetime import datetime

  class MyObject:
      def __init__(self, name):
          self.timestamp = datetime.now()
          self.name = name

You can use the ``ignore_attributes`` parameter as follows:

>>> obj1 = MyObject('foo')
>>> obj2 = MyObject('foo')
>>> compare(expected=obj1, actual=obj2, ignore_attributes=['timestamp'])

You can also specify which attributes to ignore on a per-type basis by passing a dictionary
mapping types to sets of attribute names:

>>> class OtherObject:
...     def __init__(self, id, value):
...         self.id = id
...         self.value = value
>>> compare(
...     expected=[MyObject('x'), OtherObject(1, 'y')],
...     actual=[MyObject('x'), OtherObject(2, 'y')],
...     ignore_attributes={MyObject: {'timestamp'}, OtherObject: {'id'}}
... )

.. _ignore-eq:

Ignoring ``__eq__``
~~~~~~~~~~~~~~~~~~~

.. warning::
  If you find yourself in a situation where objects incorrectly express equality, be very careful to
  ensure that you see any tests you implement failing due to inequality before you assume that
  anything described in this section is working as you expect.
  Equality checking is complex, and there are gotchas lurking
  with container types and objects on either side of an equality check implementing ``__eq__``.

Some objects, such as :doc:`pandas <pandas>` and :doc:`polars <polars>` dataframes and
:doc:`Django ORM objects<django>`, make unfortunate choices in their
implementations of ``__eq__`` when it comes to checking that objects have identical attributes.
Since :func:`compare` normally relies on this, it can result in objects appearing to be equal when
they are not.

Take this class, for example:

.. code-block:: python

  class OrmObj:
      def __init__(self, a):
          self.a = a
      def __eq__(self, other):
          return True
      def __repr__(self):
          return 'OrmObj: '+str(self.a)

If we compare normally, we erroneously understand the objects to be equal:

>>> compare(actual=OrmObj(1), expected=OrmObj(2))

In order to get a correct comparison, we need to use the ``ignore_eq`` parameter:

>>> compare(actual=OrmObj(1), expected=OrmObj(2), ignore_eq=OrmObj)
Traceback (most recent call last):
...
AssertionError: OrmObj not as expected:
<BLANKLINE>
attributes differ:
'a': 2 (expected) != 1 (actual)

``ignore_eq`` accepts a single type, an iterable of types, or ``True`` to
skip ``__eq__`` for *every* object during the comparison.

If a particular type and all of its subclasses are always problematic, you can register it once
globally so callers don't need to remember the ``ignore_eq=`` argument:

.. invisible-code-block: python

  from testfixtures.comparing import Registry
  registry = Registry.initial().install()


.. code-block:: python

  from testfixtures import register

  register(OrmObj, ignore_eq=True)

.. invisible-code-block: python

   registry.uninstall()

Custom containers and ``ignore_eq``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When you pass a type to ``ignore_eq``, :func:`compare` also has to
ignore the ``__eq__`` of any containers that might contain the type passed to ``ignore_eq``.
This is handled for standard container types and their subclasses, specifically :class:`list`,
:class:`tuple`, :class:`dict`, :class:`set`, and :class:`frozenset`.

For custom container or wrapper types that implement ``__eq__`` and don't subclass one
of these standard container types, *and* which can contain instances of a type for which you'd like
to ``ignore_eq``, you will find that ``ignore_eq`` for the inner type alone is not sufficient.

A real-world example is a :class:`pydantic.BaseModel <pydantic:pydantic.BaseModel>` with a
:class:`pandas.DataFrame` attribute. :class:`~pandas.DataFrame` implements ``__eq__`` in a way
that raises :exc:`ValueError` when used as a boolean, and pydantic's ``__eq__`` calls ``==`` on
each field value directly, so if :class:`~pandas.DataFrame` is the only type passed to
``ignore_eq``, pydantic's ``__eq__`` still fires first and the comparison still raises:

.. code-block:: python

  import pandas as pd
  from pydantic import BaseModel, ConfigDict

  class Report(BaseModel):
      model_config = ConfigDict(arbitrary_types_allowed=True)
      name: str
      data: pd.DataFrame

.. invisible-code-block: python

  from testfixtures.comparing import Registry
  registry = Registry.initial().install()

>>> compare(
...     Report(name='sales', data=pd.DataFrame({'x': [1, 2]})),
...     expected=Report(name='sales', data=pd.DataFrame({'x': [1, 3]})),
...     ignore_eq=pd.DataFrame,
... )
Traceback (most recent call last):
...
ValueError: The truth value of a DataFrame is ambiguous. Use a.empty, a.bool(), a.item(), a.any() or a.all().

.. invisible-code-block: python

  registry.uninstall()

Both types must be known to :func:`compare`. For broadly applicable types like
:class:`~pydantic.BaseModel` and :class:`~pandas.DataFrame`, the right solution is to
:ref:`register <comparer-register>` a comparer for each. This happens automatically
when both pydantic and pandas are installed, so :func:`compare` handles
:class:`~pydantic.BaseModel` instances containing :class:`~pandas.DataFrame`
attributes without any extra arguments:

>>> compare(
...     Report(name='sales', data=pd.DataFrame({'x': [1, 2]})),
...     expected=Report(name='sales', data=pd.DataFrame({'x': [1, 3]})),
... )
Traceback (most recent call last):
...
AssertionError: Report not as expected:
<BLANKLINE>
attributes same:
['name']
<BLANKLINE>
attributes differ:
'data':    x
0  1
1  3 (expected) !=    x
0  1
1  2 (actual)
<BLANKLINE>
While comparing .data: DataFrame.iloc[:, 0] (column name="x") are different
<BLANKLINE>
DataFrame.iloc[:, 0] (column name="x") values are different (50.0 %)
[index]: [0, 1]
[left]:  [1, 3]
[right]: [1, 2]
At positional index 1, first diff: 3 != 2

.. _recursion:

Nested and recursive comparison
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Where :func:`compare` is able to provide a descriptive comparison for
a particular type, it will then recurse to do the same for the
elements contained within objects of that type. 
For example, when comparing a list of dictionaries, the description
will not only tell you where in the list the difference occurred, but
also what the differences were within the dictionaries that weren't
equal:

>>> compare([{'one': 1}, {'two': 2, 'text':'foo\nbar\nbaz'}],
...         [{'one': 1}, {'two': 2, 'text':'foo\nbob\nbaz'}])
Traceback (most recent call last):
 ...
AssertionError: sequence not as expected:
<BLANKLINE>
same:
[{'one': 1}]
<BLANKLINE>
first:
[{'text': 'foo\nbar\nbaz', 'two': 2}]
<BLANKLINE>
second:
[{'text': 'foo\nbob\nbaz', 'two': 2}]
<BLANKLINE>
While comparing [1]: dict not as expected:
<BLANKLINE>
same:
['two']
<BLANKLINE>
values differ:
'text': 'foo\nbar\nbaz' != 'foo\nbob\nbaz'
<BLANKLINE>
While comparing [1]['text']: 
--- first
+++ second
@@ -1,3 +1,3 @@
 foo
-bar
+bob
 baz

This also applies to any comparer you provide, as shown under
:ref:`comparer-register`.

Preventing infinite recursion
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If an object refers back to itself, directly or via something it
contains, the recursive comparison used by :func:`compare` would loop forever.
To avoid this, if an object is seen more than once during a comparison, it is
wrapped with an :class:`~testfixtures.comparers.AlreadySeen` marker
rather than being compared again.

When that happens *and* a difference is being reported anyway, the
marker becomes visible in the output:

>>> ouroboros1 = {}
>>> ouroboros1['ouroboros'] = ouroboros1
>>> ouroboros2 = {}
>>> ouroboros2['ouroboros'] = ouroboros2
>>> compare({1: ouroboros1, 2: 'foo'}, {1: ouroboros2, 2: ouroboros2})
Traceback (most recent call last):
 ...
AssertionError: dict not as expected:
<BLANKLINE>
same:
[1]
<BLANKLINE>
values differ:
2: 'foo' != {'ouroboros': <Recursion on dict with id=...>}
<BLANKLINE>
While comparing [2]: not equal:
'foo'
<AlreadySeen for {'ouroboros': {...}} at [1] with id ...>

The ``at [1]`` part of the marker is the path where that object was
first encountered, so you can trace the cycle back to its origin.

If the same object appears at the same position in both sides of a
comparison :func:`compare` treats it as equal by identity without calling its ``__eq__``.
No marker is visible in that case, and an :ref:`unhelpful <ignore-eq>` ``__eq__`` cannot
cause a spurious difference.

.. _compare-types:

How each type is compared
-------------------------

Where :func:`compare` recognises the type of the values it is given, it produces
a description tailored to that type, pinpointing exactly what differs, and
:ref:`recurses <recursion>` into the elements those values contain. The
following sections show the feedback given for each supported type.

sets
~~~~
 
Comparing sets that aren't the same will attempt to
highlight where the differences lie:

>>> compare(expected={1, 2}, actual={2, 3})
Traceback (most recent call last):
 ...
AssertionError: set not as expected:
<BLANKLINE>
in expected but not actual:
[1]
<BLANKLINE>
in actual but not expected:
[3]
<BLANKLINE>
<BLANKLINE>

See :ref:`SequenceComparison <sequencecomparison>` to assert only that certain
items are present, regardless of order.

dicts
~~~~~

Comparing dictionaries that aren't the same will attempt to
highlight where the differences lie:

>>> compare(expected=dict(x=1, y=2, a=4), actual=dict(x=1, z=3, a=5))
Traceback (most recent call last):
 ...
AssertionError: dict not as expected:
<BLANKLINE>
same:
['x']
<BLANKLINE>
in expected but not actual:
'y': 2
<BLANKLINE>
in actual but not expected:
'z': 3
<BLANKLINE>
values differ:
'a': 4 (expected) != 5 (actual)

See :ref:`MappingComparison <mappingcomparison>` to assert only that certain
keys are present, or to check the order of keys.

lists and tuples
~~~~~~~~~~~~~~~~

Comparing lists or tuples that aren't the same will attempt to highlight
where the differences lie:

>>> compare(expected=[1, 2, 3], actual=[1, 2, 4])
Traceback (most recent call last):
 ...
AssertionError: sequence not as expected:
<BLANKLINE>
same:
[1, 2]
<BLANKLINE>
expected:
[3]
<BLANKLINE>
actual:
[4]

See :ref:`SequenceComparison <sequencecomparison>` to compare without regard to
order, or to assert only that certain items are present.

namedtuples
~~~~~~~~~~~

When two :func:`~collections.namedtuple` instances are compared, if
they are of the same type, the description given will highlight which
elements were the same and which were different:

>>> from collections import namedtuple
>>> TestTuple = namedtuple('TestTuple', 'x y z')
>>> compare(expected=TestTuple(1, 2, 3), actual=TestTuple(1, 4, 3))
Traceback (most recent call last):
 ...
AssertionError: TestTuple not as expected:
<BLANKLINE>
same:
['x', 'z']
<BLANKLINE>
values differ:
'y': 2 (expected) != 4 (actual)

.. _compare-generators:

generators
~~~~~~~~~~

When two generators are compared, they are both first unwound into
tuples and those tuples are then compared.

The :ref:`generator <generator>` helper is useful for creating a
generator to represent the expected results:

>>> from testfixtures import generator
>>> def my_gen(t):
...     i = 0
...     while i<t:
...         i += 1
...         yield i
>>> compare(expected=generator(1, 2, 3), actual=my_gen(2))
Traceback (most recent call last):
 ...
AssertionError: sequence not as expected:
<BLANKLINE>
same:
(1, 2)
<BLANKLINE>
expected:
(3,)
<BLANKLINE>
actual:
()

See :ref:`SequenceComparison <sequencecomparison>` to compare the unwound results
without regard to order, or to assert only that certain items are present.

.. warning::

  If you wish to assert that a function returns a generator, say, for
  performance reasons, then you should use 
  :ref:`strict comparison <strict-comparison>`.

.. _compare-strings:

strings
~~~~~~~

Comparison of strings can be tricky, particularly when those strings
contain multiple lines; spotting the differences between the expected
and actual values can be hard.

To help with this, long strings give a more helpful representation
when comparison fails:

>>> compare(expected="1234567891011", actual="1234567789")
Traceback (most recent call last):
 ...
AssertionError: 
'1234567891011' (expected)
!=
'1234567789' (actual)

Likewise, multi-line strings give unified diffs when their comparison
fails:

>>> compare(
...     expected="""
...         This is line 1
...         This is line 2
...         This is line 3
...         """,
...     actual="""
...         This is line 1
...         This is another line
...         This is line 3
...         """
... )
Traceback (most recent call last):
 ...
AssertionError: 
--- expected
+++ actual
@@ -1,5 +1,5 @@
<BLANKLINE>
         This is line 1
-        This is line 2
+        This is another line
         This is line 3
<BLANKLINE>

Such comparisons can still be confusing as white space is taken into
account. If you need to care about whitespace characters, you can make
spotting the differences easier as follows:

>>> compare("\tline 1\r\nline 2"," line1 \nline 2", show_whitespace=True)
Traceback (most recent call last):
 ...
AssertionError: 
--- first
+++ second
@@ -1,2 +1,2 @@
-'\tline 1\r\n'
+' line1 \n'
 'line 2'

However, you may not care about some of the whitespace involved. To
help with this, :func:`compare` has two options that can be set to
ignore certain types of whitespace.

If you wish to compare two strings that contain blank lines or lines
containing only whitespace characters, but where you only care about
the content, you can use the following:

.. code-block:: python

  compare(
      expected='line1\nline2',
      actual='line1\n \nline2\n\n',
      blanklines=False
  )

If you wish to compare two strings made up of lines that may have
trailing whitespace that you don't care about, you can do so with the
following: 

.. code-block:: python

  compare(
      expected='line1\nline2',
      actual='line1 \t\nline2   \n',
      trailing_whitespace=False
  )

See :ref:`TextComparison <textcomparison>` to assert that a string matches a
regular expression instead of comparing it exactly.

.. _compare-datetime:

datetimes and times
~~~~~~~~~~~~~~~~~~~

Given the following two :class:`~datetime.datetime` objects:

>>> from datetime import datetime
>>> from zoneinfo import ZoneInfo
>>> t1 = datetime(2024, 10, 27, 1, fold=0, tzinfo=ZoneInfo('Europe/London'))
>>> str(t1)
'2024-10-27 01:00:00+01:00'
>>> t2 = datetime(2024, 10, 27, 1, fold=1, tzinfo=ZoneInfo('Europe/London'))
>>> str(t2)
'2024-10-27 01:00:00+00:00'

It may well be surprising to find out that Python considers them equivalent:

>>> t1 == t2
True

Unfortunately, that also means that :func:`compare` will also consider them
equal:

>>> compare(t1, t2)

If it is important for you to be able to check you have the correct point in time,
then you can use :ref:`strict comparison <strict-comparison>`, which will highlight the difference:

>>> compare(t1, t2, strict=True)
Traceback (most recent call last):
...
AssertionError: datetime.datetime(2024, 10, 27, 1, 0, tzinfo=zoneinfo.ZoneInfo(key='Europe/London')) != datetime.datetime(2024, 10, 27, 1, 0, fold=1, tzinfo=zoneinfo.ZoneInfo(key='Europe/London'))

This problem can also be seen with :class:`~datetime.time` objects, where given
the following two times:

>>> from datetime import time
>>> t1 = time(1, 30, fold=0)
>>> str(t1)
'01:30:00'
>>> t2 = time(1, 30, fold=1)
>>> str(t2)
'01:30:00'

The times will be considered equal:

>>> t1 == t2
True
>>> compare(t1, t2)

However, once again, strict comparison will highlight the difference:

>>> compare(t1, t2, strict=True)
Traceback (most recent call last):
...
AssertionError: datetime.time(1, 30) != datetime.time(1, 30, fold=1)

.. _comparer-objects:

objects
~~~~~~~

Even if your objects do not natively support comparison, when they are compared
they will be considered identical if they are of the same type and have identical
attributes. Take instances of this class as an example:

.. code-block:: python

  class MyObject:
      def __init__(self, name):
          self.name = name
      def __repr__(self):
          return '<MyObject>'

If the attributes and type of instances are the same, they will be considered equal:

>>> compare(MyObject('foo'), expected=MyObject('foo'))

However, if their attributes differ, you will get an informative error:

>>> compare(MyObject('foo'), expected=MyObject('bar'))
Traceback (most recent call last):
 ...
AssertionError: MyObject not as expected:
<BLANKLINE>
attributes differ:
'name': 'bar' (expected) != 'foo' (actual)
<BLANKLINE>
While comparing .name: 'bar' (expected) != 'foo' (actual)

This type of comparison is also used on objects that make use of ``__slots__``.

To compare only some of an object's attributes, see :ref:`ignore-attributes`, or use the partial
:func:`like` matcher described in :ref:`comparison-objects`.

.. _comparer-register:

Providing your own comparers
----------------------------

The sections above cover how :func:`compare` performs out of the
box. When you need richer feedback for your own types, you can teach
:func:`compare` how to compare them.

.. note::

    If you are reading this section as a result of needing to test
    objects that don't natively support comparison, or as a result of
    needing to infrequently compare your own subclasses of python
    basic types, take a look at :ref:`comparison-objects` as this may
    well be an easier solution.

.. invisible-code-block: python

  from testfixtures.comparing import Registry
  from testfixtures.comparers import compare_sequence
  registry = Registry.initial({list: compare_sequence}).install()

As an example, suppose you have a class whose instances have a
timestamp and a name as attributes, but you'd like to ignore the
timestamp when comparing:

.. code-block:: python

  from datetime import datetime
  
  class MyObject:
      def __init__(self, name):
          self.timestamp = datetime.now()
          self.name = name

To compare lots of these, you would first write a comparer:

.. code-block:: python

  def compare_my_object(x, y, context):
      if x.name == y.name:
          return
      return 'MyObject named %s != MyObject named %s' % (
          context.label('x', repr(x.name)),
          context.label('y', repr(y.name)),
          )

Then you'd register that comparer for your type:

.. code-block:: python

  from testfixtures import register
  register(MyObject, compare_my_object)

Now, it'll get used when comparing objects of that type,
even if they're contained within other objects:

>>> compare(expected=[1, MyObject('foo')], actual=[1, MyObject('bar')])
Traceback (most recent call last):
 ...
AssertionError: sequence not as expected:
<BLANKLINE>
same:
[1]
<BLANKLINE>
expected:
[<MyObject ...>]
<BLANKLINE>
actual:
[<MyObject ...>]
<BLANKLINE>
While comparing [1]: MyObject named 'foo' (expected) != MyObject named 'bar' (actual)

From this example, you can also see that a comparer can indicate that
two objects are equal, for :func:`compare`'s purposes, by returning
``None``:

>>> MyObject('foo') == MyObject('foo')
False
>>> compare(MyObject('foo'), MyObject('foo'))

You can also see that you can, and should, use the context object passed in
to add labels to the representations of the objects being compared if the
comparison fails:

>>> compare(MyObject('foo'), MyObject('bar'), x_label='stored', y_label='supplied')
Traceback (most recent call last):
 ...
AssertionError: MyObject named 'foo' (stored) != MyObject named 'bar' (supplied)

It may be that you only want to use a comparer or set of
comparers for a particular test. If that's the case, you can pass
:func:`compare` a ``comparers`` parameter consisting of a
dictionary that maps types to comparers:

>>> compare(MyObject('foo'), MyObject('bar'),
...         comparers={MyObject: compare_my_object})
Traceback (most recent call last):
 ...
AssertionError: MyObject named 'foo' != MyObject named 'bar'

.. invisible-code-block: python

  registry.uninstall()

A full list of the available comparers included can be found below the
API documentation for :func:`compare`. These make good candidates for
registering for your own classes, if they provide the necessary
behaviour, and their source is also good to read when wondering how to
implement your own comparers.

.. note::

  A comparer should always return some text when it considers
  the two objects it is comparing to be different.

.. _custom-comparer-different:

Handing off comparison
~~~~~~~~~~~~~~~~~~~~~~

You may be wondering what the ``context`` object passed to the
comparer is for: it allows you to hand off comparison of parts of the
two objects currently being compared back to the :func:`compare`
machinery.

For example, you may have an object that has a couple of dictionaries
as attributes:

.. code-block:: python

  class Request:
      def __init__(self, uri, headers, body):
          self.uri = uri
          self.headers = headers
          self.body = body

When your tests encounter instances of these that are not as expected,
you want feedback about which bits of the request or response weren't
as expected. This can be achieved by implementing a comparer as
follows:

.. code-block:: python

   def compare_request(x, y, context):
       uri_different = x.uri != y.uri
       headers_different = context.different(x.headers, y.headers, '.headers')
       body_different = context.different(x.body, y.body, '.body')
       if uri_different or headers_different or body_different:
           return f'Request for {x.uri!r} != Request for {y.uri!r}'

Here's this custom request comparer in action:

>>> compare(Request('/foo', {'method': 'POST'}, {'my_field': 'value_1'}),
...         Request('/foo', {'method': 'GET'}, {'my_field': 'value_2'}),
...         comparers={Request: compare_request})
Traceback (most recent call last):
 ...
AssertionError: Request for '/foo' != Request for '/foo'
<BLANKLINE>
While comparing .headers: dict not as expected:
<BLANKLINE>
values differ:
'method': 'POST' != 'GET'
<BLANKLINE>
While comparing .headers['method']: 'POST' != 'GET'
<BLANKLINE>
While comparing .body: dict not as expected:
<BLANKLINE>
values differ:
'my_field': 'value_1' != 'value_2'
<BLANKLINE>
While comparing .body['my_field']: 'value_1' != 'value_2'

.. note::

  A comparer should always return some text when it considers
  the two objects it is comparing to be different.

.. _custom-comparer-options:

Options for custom comparers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As an example of passing options through to a comparer, suppose you
wanted to compare all decimals in a nested data structure by rounding
them to a number of decimal places that varies from test to test. The
comparer could be implemented and registered as follows:

.. invisible-code-block: python

  registry = Registry.initial().install()

.. code-block:: python

  from decimal import Decimal
  from testfixtures import register

  def compare_decimal(x, y, context, precision: int = 2):
       if round(x, precision) != round(y, precision):
           return f'{x!r} != {y!r} when rounded to {precision} places'

  register(Decimal, compare_decimal)

Now, this comparer will be used for comparing all decimals and the
precision used will be that passed to :func:`compare`:

>>> expected_order = {'price': Decimal('1.234'), 'quantity': 5}
>>> actual_order = {'price': Decimal('1.236'), 'quantity': 5}
>>> compare(expected_order, actual_order, precision=1)
>>> compare(expected_order, actual_order, precision=3)
Traceback (most recent call last):
 ...
AssertionError: dict not as expected:
<BLANKLINE>
same:
['quantity']
<BLANKLINE>
values differ:
'price': Decimal('1.234') != Decimal('1.236')
<BLANKLINE>
While comparing ['price']: Decimal('1.234') != Decimal('1.236') when rounded to 3 places

If no precision is passed, the default of ``2`` will be used:

>>> compare(Decimal('2.006'), Decimal('2.009'))
>>> compare(Decimal('2.001'), Decimal('2.009'))
Traceback (most recent call last):
 ...
AssertionError: Decimal('2.001') != Decimal('2.009') when rounded to 2 places

If you only need to compare numbers approximately or within a range, the
:ref:`RoundComparison <roundcomparison>` and :ref:`RangeComparison
<rangecomparison>` objects may be simpler than a custom comparer.

Ignoring attributes in custom comparers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When writing custom comparers that delegate to :func:`~testfixtures.comparers.compare_object`,
you may want to always ignore certain attributes while still allowing users to pass additional
attributes to ignore via the ``ignore_attributes`` parameter to :func:`compare`.

The :func:`~testfixtures.comparers.merge_ignored_attributes` function makes this easy by
combining multiple ignore specifications:

.. code-block:: python

  from testfixtures.comparers import compare_object, merge_ignored_attributes

  class Thing:
      def __init__(self, **kw):
          for k, v in kw.items():
              setattr(self, k, v)

  def compare_thing(x, y, context):
      # Always ignore 'y' attribute, plus any user-specified ignores
      context_ignored = context.options.get('ignore_attributes')
      ignored = merge_ignored_attributes('y', context_ignored)
      return compare_object(x, y, context, ignore_attributes=ignored)

Now the ``y`` attribute will always be ignored, but users can still specify additional
attributes to ignore:

>>> compare(Thing(x=1, y=2), Thing(x=1, y=3),
...         comparers={Thing: compare_thing})

>>> compare(Thing(x=1, y=2, z=3), Thing(x=1, y=4, z=5),
...         comparers={Thing: compare_thing},
...         ignore_attributes=['z'])

.. invisible-code-block: python

  registry.uninstall()

Rendering objects safely in custom comparers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When a custom comparer builds a message it usually needs to render the objects
it is comparing. If one of those objects raises an exception as part of that process, the
caller sees an unrelated traceback instead of any useful comparison message.

:func:`~testfixtures.comparers.safe_repr` and
:func:`~testfixtures.comparers.safe_pformat` are
drop-in replacements for :func:`repr` and :func:`pprint.pformat` that catch
exceptions, but not :class:`BaseException` instances such as :exc:`KeyboardInterrupt`
or :exc:`SystemExit`, and substitute any failures with a marker.

For example, an object whose ``__repr__`` raises yields a marker instead of
propagating the exception:

>>> from testfixtures import safe_repr
>>> class Broken:
...     def __repr__(self):
...         raise ValueError('boom')
>>> print(safe_repr(Broken()))
<unrepresentable ...Broken: ValueError: boom>
