"""
Tools for helping to test applications that use Protocol Buffers.
"""
from typing import TYPE_CHECKING, Any

from google import protobuf as protobuf
from google.protobuf.message import Message

from .comparers import compare_attribute_mapping, compare_with_type

if TYPE_CHECKING:
    from .comparing import CompareContext


def _set_fields(message: Message) -> dict[str, Any]:
    # Extensions are keyed as protobuf's text format shows them, so they can't
    # collide with an ordinary field of the same name:
    return {
        f'[{field.full_name}]' if field.is_extension else field.name: value
        for field, value in message.ListFields()
    }


def _unknown_fields(message: Message) -> Message:
    # A copy of message with everything but its unknown fields cleared:
    unknown = type(message)()
    unknown.MergeFrom(message)
    for field in message.DESCRIPTOR.fields:
        unknown.ClearField(field.name)
    if message.DESCRIPTOR.extension_ranges:
        for extension in message.Extensions:
            unknown.ClearExtension(extension)
    return unknown


def compare_message(x: Message, y: Message, context: 'CompareContext') -> str | None:
    """
    Returns an informative string describing the differences between the two
    supplied protobuf :class:`~google.protobuf.message.Message` instances,
    based on the fields set on each of them as returned by
    :meth:`~google.protobuf.message.Message.ListFields`. Extensions are named
    by their full name in square brackets, as protobuf's text format shows them.

    Messages of different types are never equal. When the set fields match but
    the unknown fields of the messages differ, a short description saying so is
    returned.
    """
    if type(x) is not type(y):
        return compare_with_type(x, y, context)
    differences = compare_attribute_mapping(_set_fields(x), _set_fields(y), context, x, y)
    if differences is None and x != y and _unknown_fields(x) != _unknown_fields(y):
        x_label = context.x_label or 'x'
        y_label = context.y_label or 'y'
        differences = (
            f'Both {x_label} and {y_label} have the same field values, '
            'but their unknown fields differ!'
        )
    return differences
