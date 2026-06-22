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

Pydantic's :class:`~pydantic.BaseModel` implements ``__iter__``, yielding
``(name, value)`` pairs for each field so that ``dict(model)`` works.
Without a comparer registered for it, :func:`~testfixtures.compare` treats
any iterable as a sequence, so comparing two differing models produces a
confusing diff of field tuples rather than a clear, field-by-field
comparison:

>>> from pydantic import BaseModel
>>> from testfixtures import compare
>>> class Point(BaseModel):
...     x: int
...     y: int
>>> compare(Point(x=1, y=2), expected=Point(x=1, y=3))
Traceback (most recent call last):
 ...
AssertionError: sequence not as expected:
<BLANKLINE>
same:
(('x', 1),)
<BLANKLINE>
expected:
(('y', 3),)
<BLANKLINE>
actual:
(('y', 2),)
<BLANKLINE>
While comparing [1]: sequence not as expected:
<BLANKLINE>
same:
('y',)
<BLANKLINE>
expected:
(3,)
<BLANKLINE>
actual:
(2,)

Helpers for testing code that uses `Pydantic <https://docs.pydantic.dev/>`_ will live here.
