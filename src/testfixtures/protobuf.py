"""
Tools for helping to test applications that use Protocol Buffers.
"""
from typing import TYPE_CHECKING

from google import protobuf as protobuf
from google.protobuf.message import Message

from .comparers import compare_attribute_mapping, compare_with_type

if TYPE_CHECKING:
    from .comparing import CompareContext


def compare_message(x: Message, y: Message, context: 'CompareContext') -> str | None:
    """
    Returns an informative string describing the differences between the two
    supplied protobuf :class:`~google.protobuf.message.Message` instances,
    based on the fields set on each of them as returned by
    :meth:`~google.protobuf.message.Message.ListFields`.

    Messages of different types are never equal. When the set fields match but
    the messages are still not equal, such as when only their unknown fields
    differ, a short description saying so is returned.
    """
    if type(x) is not type(y):
        return compare_with_type(x, y, context)
    x_fields = {field.name: value for field, value in x.ListFields()}
    y_fields = {field.name: value for field, value in y.ListFields()}
    differences = compare_attribute_mapping(x_fields, y_fields, context, x, y)
    if differences is None and x != y:
        x_label = context.x_label or 'x'
        y_label = context.y_label or 'y'
        differences = f'Both {x_label} and {y_label} have the same field values, but are not equal!'
    return differences
