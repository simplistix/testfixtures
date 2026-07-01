Testing with Pydantic
=====================

.. note::

   To ensure you are using compatible versions, install with the ``testfixtures[pydantic]`` extra.

.. invisible-code-block: python

    try:
        import pydantic
    except ImportError:
        pydantic = None

.. skip: start if(pydantic is None, reason="No pydantic installed")

When pydantic is installed, a :func:`comparer <testfixtures.pydantic.compare_basemodel>`
for :class:`~pydantic.BaseModel` is automatically
:ref:`registered <comparer-register>` with ``ignore_eq=True``. It compares
models field-by-field using their declared attributes, so differences are
shown clearly:

>>> from pydantic import BaseModel
>>> from testfixtures import compare
>>> class Point(BaseModel):
...     x: int
...     y: int
>>> compare(Point(x=1, y=2), expected=Point(x=1, y=3))
Traceback (most recent call last):
 ...
AssertionError: Point not as expected:
<BLANKLINE>
attributes same:
['x']
<BLANKLINE>
attributes differ:
'y': 3 (expected) != 2 (actual)

The ``ignore_eq=True`` registration is also needed whenever a model contains
attributes whose type has a custom ``__eq__`` that :func:`~testfixtures.compare`
has a registered comparer for, such as :doc:`Polars <polars>` or
:doc:`Pandas <pandas>` DataFrames. Without it, pydantic's ``__eq__``
calls ``==`` on each attribute value before testfixtures can intercept it,
which for many such types raises an error or gives a misleading result.

For example, consider a model with a :class:`~polars.DataFrame` attribute:

.. code-block:: python

  import polars as pl
  from pydantic import BaseModel, ConfigDict

  class Report(BaseModel):
      model_config = ConfigDict(arbitrary_types_allowed=True)
      name: str
      data: pl.DataFrame

  r1 = Report(name='sales', data=pl.DataFrame({'x': [1, 2], 'y': [3, 4]}))
  r2 = Report(name='sales', data=pl.DataFrame({'x': [1, 2], 'y': [3, 5]}))

Without the ``BaseModel`` registration, pydantic's ``__eq__`` fires first and
raises a :exc:`TypeError`:

.. invisible-code-block: python

  from testfixtures.comparing import Registry
  registry = Registry.initial().install()

>>> compare(r1, expected=r2)
Traceback (most recent call last):
 ...
TypeError: the truth value of a DataFrame is ambiguous
<BLANKLINE>
Hint: to check if a DataFrame contains any values, use `is_empty()`.

.. invisible-code-block: python

  registry.uninstall()

With the registration in place, :func:`~testfixtures.compare` hands off
to the :doc:`Polars comparer <polars>` and produces a clear diff:

>>> compare(r1, expected=r2)
Traceback (most recent call last):
 ...
AssertionError: Report not as expected:
<BLANKLINE>
attributes same:
['name']
<BLANKLINE>
attributes differ:
'data': shape: (2, 2)
┌─────┬─────┐
│ x   ┆ y   │
│ --- ┆ --- │
│ i64 ┆ i64 │
╞═════╪═════╡
│ 1   ┆ 3   │
│ 2   ┆ 5   │
└─────┴─────┘ (expected) != shape: (2, 2)
┌─────┬─────┐
│ x   ┆ y   │
│ --- ┆ --- │
│ i64 ┆ i64 │
╞═════╪═════╡
│ 1   ┆ 3   │
│ 2   ┆ 4   │
└─────┴─────┘ (actual)
<BLANKLINE>
While comparing .data: DataFrames are different (value mismatch for column "y")
[left]: shape: (2,)
Series: 'y' [i64]
[
	3
	5
]
[right]: shape: (2,)
Series: 'y' [i64]
[
	3
	4
]

Testing validation errors
--------------------------

When a :class:`~pydantic.BaseModel` is given invalid data, pydantic raises
:class:`pydantic.ValidationError <pydantic:pydantic_core.ValidationError>`. This type has no public constructor that
takes a plain message, so building an instance to hand to :class:`~testfixtures.ShouldRaise`
for a full comparison is impractical.

Even setting aside how hard it is to construct one, comparing full instances
would not catch anything useful anyway. Pydantic stores the details of what
went wrong outside the ``args`` and ``__dict__`` that :func:`~testfixtures.compare` inspects
for exceptions, so any two naturally raised :class:`pydantic.ValidationError <pydantic:pydantic_core.ValidationError>`
instances compare equal regardless of what actually failed:

.. invisible-code-block: python

  from pydantic import ValidationError

  errors = []
  for bad in ({'x': 'not-an-int', 'y': 2}, {'x': 2, 'y': 'also-not-an-int'}):
      try:
          Point(**bad)
      except ValidationError as e:
          errors.append(e)

>>> compare(errors[0], expected=errors[1])

The way to check a raised :class:`pydantic.ValidationError <pydantic:pydantic_core.ValidationError>` is therefore to
match its :func:`repr` or :class:`str` rendering with
:func:`~testfixtures.repr_like` or :func:`~testfixtures.str_like`. Use
``match`` rather than ``expected``, since the rendering includes a
pydantic-version-specific URL:

>>> from testfixtures import ShouldRaise, repr_like
>>> with ShouldRaise(repr_like(ValidationError, match='validation error for Point')):
...     Point(x='not-an-int', y=2)

>>> from testfixtures import str_like
>>> with ShouldRaise(str_like(ValidationError, match='validation error for Point')):
...     Point(x='not-an-int', y=2)

``repr_like`` and ``str_like`` can also compare the whole rendering exactly,
rather than matching a pattern within it. If the rendering doesn't match, an
:class:`AssertionError` explains the difference:

.. invisible-code-block: python

  try:
      Point(x='not-an-int', y=2)
  except ValidationError as e:
      wrong_text = str(e).replace('\nx\n', '\ny\n', 1)

>>> with ShouldRaise(repr_like(ValidationError, wrong_text)):
...     Point(x='not-an-int', y=2)
Traceback (most recent call last):
...
AssertionError: not equal:
<ReprComparison: pydantic_core._pydantic_core.ValidationError: 1 validation error for Point
y
  Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='not-an-int', input_type=str]
    For further information visit https://errors.pydantic.dev/.../v/int_parsing> (expected)
1 validation error for Point
x
  Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='not-an-int', input_type=str]
    For further information visit https://errors.pydantic.dev/.../v/int_parsing (raised)
