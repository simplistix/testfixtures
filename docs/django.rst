Testing with Django
===================

.. note::

   To ensure you are using compatible versions, install with the ``testfixtures[django]`` extra.

.. invisible-code-block: python

  try:
      import django
  except ImportError:
      django = None
  else:
      from tests.test_django.models import SampleModel

.. skip: start if(django is None, reason="No django installed")

Django's ORM has an unfortunate implementation choice of considering
:class:`~django.db.models.Model` instances to be identical as long as their
primary keys are the same:

.. literalinclude:: ../tests/test_django/models.py
   :pyobject: SampleModel

>>> SampleModel(id=1, value=1) == SampleModel(id=1, value=2)
True

To work around this, when Django is installed, a
:func:`comparer <testfixtures.django.compare_model>` for the
:class:`~django.db.models.Model` class is automatically
:ref:`registered <comparer-register>` with ``ignore_eq=True``, so
:func:`~testfixtures.compare` does the right thing:

>>> from testfixtures import compare
>>> compare(SampleModel(id=1, value=1), SampleModel(id=1, value=2))
Traceback (most recent call last):
 ...
AssertionError: SampleModel not as expected:
<BLANKLINE>
same:
['id']
<BLANKLINE>
values differ:
'value': 1 != 2

Ignoring fields
---------------

It may also be that you want to ignore fields over which you have no control
and cannot easily mock, such as created or modified times. For this, you
can use the ``ignore_fields`` option:

>>> compare(SampleModel(id=1, value=1), SampleModel(id=1, value=2),
...         ignore_fields=['value'])


Comparing non-editable fields
-----------------------------

By default, non-editable fields are ignored:

>>> compare(SampleModel(not_editable=1), SampleModel(not_editable=2))

If you wish to include these fields in the comparison, pass the
``non_editable_fields`` option:

>>> compare(SampleModel(not_editable=1), SampleModel(not_editable=2),
...         non_editable_fields=True)
Traceback (most recent call last):
 ...
AssertionError: SampleModel not as expected:
<BLANKLINE>
same:
['created', 'id', 'value']
<BLANKLINE>
values differ:
'not_editable': 1 != 2


.. note::

  The registered comparer currently ignores
  :class:`many to many <django.db.models.ManyToManyField>` fields.
  Patches to fix this deficiency are welcome!
