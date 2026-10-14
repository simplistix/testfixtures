Testing with Protocol Buffers
=============================

.. note::

   To ensure you are using compatible versions, install with the ``testfixtures[protobuf]`` extra.

.. invisible-code-block: python

    try:
        from google import protobuf
    except ImportError:
        protobuf = None

.. skip: start if(protobuf is None, reason="No protobuf installed")

Protobuf messages keep their field values outside of their instance attributes,
so :func:`~testfixtures.compare` cannot inspect them the way it does for other
objects. When protobuf is installed, a
:func:`comparer <testfixtures.protobuf.compare_message>` for
:class:`~google.protobuf.message.Message` is automatically
:ref:`registered <comparer-register>`. It compares messages field by field,
using the fields that are set on each of them, so differences are shown clearly:

>>> from google.protobuf.timestamp_pb2 import Timestamp
>>> from testfixtures import compare
>>> compare(Timestamp(seconds=1, nanos=5), expected=Timestamp(seconds=2, nanos=5))
Traceback (most recent call last):
 ...
AssertionError: Timestamp not as expected:
<BLANKLINE>
attributes same:
['nanos']
<BLANKLINE>
attributes differ:
'seconds': 2 (expected) != 1 (actual)

Unlike the comparers for many other libraries, this one is registered without
``ignore_eq=True``, since the ``__eq__`` of protobuf messages can be relied on.
Messages that protobuf considers equal are equal for :func:`~testfixtures.compare`
too, and the comparer is used to explain how unequal messages differ. Messages
of different types are never equal, even when the fields set on them are the same.

Nested messages, repeated fields and map fields are handed off to the comparers
for messages, sequences and mappings, so the breadcrumbs point at the location
of the difference:

>>> from google.protobuf.field_mask_pb2 import FieldMask
>>> compare(FieldMask(paths=['a', 'b']), expected=FieldMask(paths=['a', 'c']))
Traceback (most recent call last):
 ...
AssertionError: FieldMask not as expected:
<BLANKLINE>
attributes differ:
'paths': ['a', 'c'] (expected) != ['a', 'b'] (actual)
<BLANKLINE>
While comparing .paths: sequence not as expected:
<BLANKLINE>
same:
('a',)
<BLANKLINE>
expected:
('c',)
<BLANKLINE>
actual:
('b',)
<BLANKLINE>
While comparing .paths[1]: 'c' (expected) != 'b' (actual)

Only the fields that are set on a message are compared. Where protobuf tracks
whether a field has been set, as it does for members of a ``oneof`` and for
fields marked as ``optional``, a field set to its default value is not the same
as one that has not been set:

>>> from google.protobuf.struct_pb2 import Value
>>> compare(Value(number_value=0), expected=Value())
Traceback (most recent call last):
 ...
AssertionError: Value not as expected:
<BLANKLINE>
attributes in actual but not expected:
'number_value': 0.0

Where protobuf does not track this, the two are equal:

>>> compare(Timestamp(seconds=0), expected=Timestamp())

If the fields set on two messages match but protobuf still considers the
messages to be unequal, such as when only their unknown fields differ,
:func:`~testfixtures.compare` reports that they are not equal rather than
passing.
