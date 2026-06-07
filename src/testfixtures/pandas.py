"""
Tools for helping to test applications that use Pandas.
"""
from typing import TYPE_CHECKING

import pandas as pandas
from pandas import DataFrame
from pandas.testing import assert_frame_equal

if TYPE_CHECKING:
    from .comparing import CompareContext


def compare_dataframe(
        x: DataFrame, y: DataFrame, context: 'CompareContext'
) -> str | None:
    """
    Returns a textual description of the differences between two
    :class:`pandas.DataFrame` instances, as reported by
    :func:`pandas.testing.assert_frame_equal`.

    When ``strict=True`` is passed to :func:`~testfixtures.compare`,
    ``check_exact=True`` is used; otherwise pandas' default tolerances apply.
    """
    try:
        assert_frame_equal(x, y, check_exact=context.strict)
    except AssertionError as e:
        return str(e)
    return None
