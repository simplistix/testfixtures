"""
Tools for helping to test applications that use Pydantic.
"""
from typing import TYPE_CHECKING

import pydantic as pydantic
from pydantic import BaseModel

from .comparers import _compare_mapping, compare_simple

if TYPE_CHECKING:
    from .comparing import CompareContext


def compare_basemodel(
        x: BaseModel,
        y: BaseModel,
        context: 'CompareContext',
) -> str | None:
    """
    Returns an informative string describing the differences between the two
    supplied Pydantic :class:`~pydantic.BaseModel` instances, based on their
    declared fields.
    """
    if type(x) is not type(y):
        return compare_simple(x, y, context)
    x_attrs = x.__dict__.copy()
    y_attrs = y.__dict__.copy()
    if not context.qualified_equals(x_attrs, y_attrs):
        return _compare_mapping(x_attrs, y_attrs, context, x, 'attributes ', '.%s')
    return None
