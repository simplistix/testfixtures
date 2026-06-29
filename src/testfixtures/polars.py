"""
Tools for helping to test applications that use Polars.
"""
from typing import TYPE_CHECKING

import polars as polars
from polars import DataFrame
from polars.testing import assert_frame_equal

if TYPE_CHECKING:
    from .comparing import CompareContext


def compare_dataframe(
        x: DataFrame, y: DataFrame, context: 'CompareContext'
) -> str | None:
    """
    Returns a textual description of the differences between two
    :class:`polars.DataFrame` instances, as reported by
    :func:`polars.testing.assert_frame_equal`.

    When ``strict=True`` is passed to :func:`~testfixtures.compare`,
    ``check_exact=True`` is used; otherwise polars' default tolerances apply.
    """
    try:
        assert_frame_equal(x, y, check_exact=context.strict)
    except AssertionError as e:
        return str(e)
    return None
