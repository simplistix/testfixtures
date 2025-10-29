Comparing objects and sequences
===============================

.. currentmodule:: testfixtures

.. invisible-code-block: python

    from testfixtures.compat import PY_312_PLUS

The helpers here provide ways of making assertions about object equality
even when those objects don't natively support comparison. Where differences
are found, feedback is provided in a way that makes it quick and easy to see what the
difference was, even in the case of deeply nested data structures.

The compare function
--------------------

The :func:`compare` function can be used as a replacement for
:meth:`~unittest.TestCase.assertEqual` or pytest-style assert statements but offers much more
:ref:`flexible <compare-strings>` and :ref:`configurable <comparer-register>` comparison,
and better feedback if a comparison fails, particularly where nested objects and those that don't
:ref:`natively support equality checking <comparer-objects>` are involved, or if those objects
do :ref:`silly things <ignore-eq>` when you compare them.

It raises an :class:`AssertionError` when its parameters are not equal, which will be
reported as a test failure:

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
want to do this in event the comparison fails. This can be done by providing a callable to either
``prefix`` or ``suffix``:

>>> compare(expected=1, actual=2, suffix=lambda: 'This is very expensive to compute...')
Traceback (most recent call last):
 ...
AssertionError: 1 (expected) != 2 (actual)
This is very expensive to compute...

The real strengths of this function come when comparing more complex
and nested data types. A number of common python data types will give more
detailed output when a comparison fails as described below:

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
then you can use strict comparison, which will highlight the difference:

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

ignoring attributes
^^^^^^^^^^^^^^^^^^^

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

Recursive comparison
~~~~~~~~~~~~~~~~~~~~

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

This also applies to any comparers you have provided, as can be seen
in the next section.

.. _comparer-register:

Providing your own comparers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When using :meth:`compare` frequently for your own complex objects,
it can be beneficial to give more descriptive output when two objects
don't compare as equal.

.. note:: 

    If you are reading this section as a result of needing to test
    objects that don't natively support comparison, or as a result of
    needing to infrequently compare your own subclasses of python
    basic types, take a look at :ref:`comparison-objects` as this may
    well be an easier solution.

.. invisible-code-block: python

  from testfixtures.comparison import _registry, Registry, compare_sequence
  from testfixtures import Replacer
  r = Replacer()
  r.replace('testfixtures.comparison._registry', Registry.initial({
      list: compare_sequence
  }))

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

  from testfixtures.comparison import register
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

  r.restore()

A full list of the available comparers included can be found below the
API documentation for :func:`compare`. These make good candidates for
registering for your own classes, if they provide the necessary
behaviour, and their source is also good to read when wondering how to
implement your own comparers.

.. note::

  A comparer should always return some text when it considers
  the two objects it is comparing to be different.

Handing off comparison
^^^^^^^^^^^^^^^^^^^^^^

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
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

As an example of passing options through to a comparer, suppose you
wanted to compare all decimals in a nested data structure by rounding
them to a number of decimal places that varies from test to test. The
comparer could be implemented and registered as follows:

.. invisible-code-block: python

  from testfixtures.comparison import _registry
  r = Replacer()
  r.replace('testfixtures.comparison._registry', _registry.overlay_with({}))

.. code-block:: python

  from decimal import Decimal
  from testfixtures.comparison import register

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

Ignoring attributes in custom comparers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When writing custom comparers that delegate to :func:`~testfixtures.comparison.compare_object`,
you may want to always ignore certain attributes while still allowing users to pass additional
attributes to ignore via the ``ignore_attributes`` parameter to :func:`compare`.

The :func:`~testfixtures.comparison.merge_ignored_attributes` function makes this easy by
combining multiple ignore specifications:

.. code-block:: python

  from testfixtures.comparison import compare_object, merge_ignored_attributes

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

  r.restore()

.. _ignore-eq:

Ignoring ``__eq__``
~~~~~~~~~~~~~~~~~~~

Some objects, such as those from the :doc:`Django ORM <django>`, have pretty broken
implementations of ``__eq__``. Since :func:`compare` normally relies on this,
it can result in objects appearing to be equal when they are not.

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

In order to get a sane comparison, we need to both supply a custom comparer
as described above, and use the ``ignore_eq`` parameter:

.. code-block:: python

  def compare_orm_obj(x, y, context):
      if x.a != y.a:
          return 'OrmObj: %s != %s' % (x.a, y.a)

>>> compare(actual=OrmObj(1), expected=OrmObj(2),
...         comparers={OrmObj: compare_orm_obj}, ignore_eq=True)
Traceback (most recent call last):
...
AssertionError: OrmObj: 2 != 1

.. _strict-comparison:

Strict comparison
~~~~~~~~~~~~~~~~~

If is it important that the two values being compared are of exactly
the same type, rather than just being equal as far as Python is
concerned, then the strict mode of :func:`compare` should be used.

For example, these two instances will normally appear to be equal
provided the elements within them are the same:

>>> TypeA = namedtuple('A', 'x')
>>> TypeB = namedtuple('B', 'x')
>>> compare(TypeA(1), TypeB(1))

If this type difference is important, then the `strict` parameter
should be used:

>>> compare(TypeA(1), TypeB(1), strict=True)
Traceback (most recent call last):
 ...
AssertionError: A(x=1) (<class '__test__.A'>) != B(x=1) (<class '__test__.B'>)

.. _comparison-objects:

Comparison objects
------------------

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
AssertionError: 
<C:...SomeClass(failed)>
attributes in Comparison but not actual:
'partial': 3
</C:...SomeClass> != <...SomeClass...>

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
AssertionError:...
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
</MappingComparison(ordered=True, partial=False)> (expected) != OrderedDict({'a': 1, 'd': 2, 'c': 3}) (actual)

You may also only care about certain keys being present in a mapping. This
can also be achieved with :class:`MappingComparison` objects:

>>> compare(expected=M(a=1, d=2, partial=True), actual={'a': 1, 'c': 3})
Traceback (most recent call last):
 ...
AssertionError:...
<MappingComparison(ordered=False, partial=True)(failed)>
ignored:
['c']
<BLANKLINE>
same:
['a']
<BLANKLINE>
in expected but not actual:
'd': 2
</MappingComparison(ordered=False, partial=True)> (expected) != {'a': 1, 'c': 3} (actual)

Where there are differences, they may be hard to spot. In this case, you can ask for a more
detailed explanation of what wasn't as expected:

>>> compare(expected=M((('a', [1, 2]), ('d', [1, 3])), ordered=True, recursive=True),
...         actual=OrderedDict((('a', [1, 2]), ('d', [1, 4]))))
Traceback (most recent call last):
 ...
AssertionError:...
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
</MappingComparison(ordered=True, partial=False)> (expected) != OrderedDict({'a': [1, 2], 'd': [1, 4]}) (actual)

.. skip: end

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

Range Comparison objects
-------------------------

When comparing numbers, dates, times and any other type that can be ordered, you may only
want to assert what range a value will fall into. :class:`RangeComparison` objects
let you confirm a value is within a certain tolerance or range.

Here's an example with numbers:

.. code-block:: python

  from testfixtures import compare, RangeComparison as R

  compare(expected=R(123.456, 789), actual=Decimal(555.01))

Here's an example with dates:

.. code-block:: python

  from datetime import date
  from testfixtures import compare, RangeComparison as R

  compare(expected=R(date(1978, 6, 13), date(1978, 10, 31)), actual=date(1978, 7, 1))

.. note::

  :class:`RangeComparison` is inclusive of both the lower and upper bound.

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
AssertionError:...
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
</SequenceComparison(ordered=True, partial=True)> (expected) != [1, 2, 3, 4, 6] (actual)

Where there are differences, they may be hard to spot. In this case, you can ask for a more
detailed explanation of what wasn't as expected:

>>> compare(expected=S({1: 'a'}, {2: 'c'}, recursive=True), actual=[{1: 'a'}, {2: 'd'}])
Traceback (most recent call last):
 ...
AssertionError:...
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
</SequenceComparison(ordered=True, partial=False)> (expected) != [{1: 'a'}, {2: 'd'}] (actual)

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


Differentiating chunks of text
------------------------------

Testfixtures provides a function that will compare two strings and
give a unified diff as a result. This can be handy as a third
parameter to :meth:`~unittest.TestCase.assertEqual` or just as a
general utility function for comparing two lumps of text.

As an example:

>>> from testfixtures import diff
>>> print(diff('line1\nline2\nline3',
...            'line1\nlineA\nline3'))
--- first
+++ second
@@ -1,3 +1,3 @@
 line1
-line2
+lineA
 line3
