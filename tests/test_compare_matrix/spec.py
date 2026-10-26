"""
What compare() should report when comparing two objects, for every combination of
behaviour, relation and mode in :mod:`.axes`.

There is one grid per behaviour, with a row per relation and a column per mode. Each
cell is the expected outcome:

- ``==``: compare() passes.
- ``!=``: compare() raises an AssertionError.
- ``raise``: the sample's ForeignOperandError propagates out of compare().

A ``*`` suffix marks a known bug: the cell shows what should happen, which currently doesn't.

A ``?`` suffix marks an open question: the cell pins what currently happens until the
question is answered.
"""
from dataclasses import dataclass

import pytest

from .axes import BEHAVIOURS, MODES, RELATIONS

# Open questions:
#
# ?  When the two objects are of different types, compare_object falls back to compare_simple,
#    which uses !=, so the ignored __eq__ is consulted after all. Should objects of differing
#    types be compared by attribute under ignore_eq, or always be unequal? Either way, the
#    outcome shouldn't depend on how __eq__ behaves, and EqRaisesForForeign shouldn't raise.
#
# Known bugs:
#
# *  Same cause as above: the values differ, but the ignored __eq__ says they're equal, or raises.

GRIDS = {
    'NoEq': '''
                                trusted    unrelated  type       all        strict
        equal                   ==         ==         ==         ==         ==
        x_value_lower           !=         !=         !=         !=         !=
        x_value_higher          !=         !=         !=         !=         !=
        detail_differs          !=         !=         !=         !=         !=
        x_subclass              !=         !=         !=?        !=?        !=
        y_subclass              !=         !=         !=?        !=?        !=
        x_foreign               !=         !=         !=?        !=?        !=
        y_foreign               !=         !=         !=?        !=?        !=
        x_subclass_other_value  !=         !=         !=         !=         !=
        y_subclass_other_value  !=         !=         !=         !=         !=
        x_foreign_other_value   !=         !=         !=         !=         !=
        y_foreign_other_value   !=         !=         !=         !=         !=
    ''',
    'EqNotImplementedForForeign': '''
                                trusted    unrelated  type       all        strict
        equal                   ==         ==         ==         ==         ==
        x_value_lower           !=         !=         !=         !=         !=
        x_value_higher          !=         !=         !=         !=         !=
        detail_differs          !=         !=         !=         !=         !=
        x_subclass              ==         ==         ==?        ==?        !=
        y_subclass              ==         ==         ==?        ==?        !=
        x_foreign               !=         !=         !=?        !=?        !=
        y_foreign               !=         !=         !=?        !=?        !=
        x_subclass_other_value  !=         !=         !=         !=         !=
        y_subclass_other_value  !=         !=         !=         !=         !=
        x_foreign_other_value   !=         !=         !=         !=         !=
        y_foreign_other_value   !=         !=         !=         !=         !=
    ''',
    'EqFalseForForeign': '''
                                trusted    unrelated  type       all        strict
        equal                   ==         ==         ==         ==         ==
        x_value_lower           !=         !=         !=         !=         !=
        x_value_higher          !=         !=         !=         !=         !=
        detail_differs          !=         !=         !=         !=         !=
        x_subclass              ==         ==         ==?        ==?        !=
        y_subclass              ==         ==         ==?        ==?        !=
        x_foreign               !=         !=         !=?        !=?        !=
        y_foreign               !=         !=         !=?        !=?        !=
        x_subclass_other_value  !=         !=         !=         !=         !=
        y_subclass_other_value  !=         !=         !=         !=         !=
        x_foreign_other_value   !=         !=         !=         !=         !=
        y_foreign_other_value   !=         !=         !=         !=         !=
    ''',
    'EqFalseyForForeign': '''
                                trusted    unrelated  type       all        strict
        equal                   ==         ==         ==         ==         ==
        x_value_lower           !=         !=         !=         !=         !=
        x_value_higher          !=         !=         !=         !=         !=
        detail_differs          !=         !=         !=         !=         !=
        x_subclass              ==         ==         ==?        ==?        !=
        y_subclass              ==         ==         ==?        ==?        !=
        x_foreign               !=         !=         !=?        !=?        !=
        y_foreign               !=         !=         !=?        !=?        !=
        x_subclass_other_value  !=         !=         !=         !=         !=
        y_subclass_other_value  !=         !=         !=         !=         !=
        x_foreign_other_value   !=         !=         !=         !=         !=
        y_foreign_other_value   !=         !=         !=         !=         !=
    ''',
    'EqRaisesForForeign': '''
                                trusted    unrelated  type       all        strict
        equal                   ==         ==         ==         ==         ==
        x_value_lower           !=         !=         !=         !=         !=
        x_value_higher          !=         !=         !=         !=         !=
        detail_differs          !=         !=         !=         !=         !=
        x_subclass              ==         ==         ==?        ==?        !=
        y_subclass              ==         ==         ==?        ==?        !=
        x_foreign               raise      raise      raise?     raise?     !=
        y_foreign               raise      raise      raise?     raise?     !=
        x_subclass_other_value  !=         !=         !=         !=         !=
        y_subclass_other_value  !=         !=         !=         !=         !=
        x_foreign_other_value   raise      raise      !=*        !=*        !=
        y_foreign_other_value   raise      raise      !=*        !=*        !=
    ''',
    'EqAlwaysTrue': '''
                                trusted    unrelated  type       all        strict
        equal                   ==         ==         ==         ==         ==
        x_value_lower           ==         ==         !=         !=         !=
        x_value_higher          ==         ==         !=         !=         !=
        detail_differs          ==         ==         !=         !=         !=
        x_subclass              ==         ==         ==?        ==?        !=
        y_subclass              ==         ==         ==?        ==?        !=
        x_foreign               ==         ==         ==?        ==?        !=
        y_foreign               ==         ==         ==?        ==?        !=
        x_subclass_other_value  ==         ==         !=*        !=*        !=
        y_subclass_other_value  ==         ==         !=*        !=*        !=
        x_foreign_other_value   ==         ==         !=*        !=*        !=
        y_foreign_other_value   ==         ==         !=*        !=*        !=
    ''',
    'EqIgnoresDetail': '''
                                trusted    unrelated  type       all        strict
        equal                   ==         ==         ==         ==         ==
        x_value_lower           !=         !=         !=         !=         !=
        x_value_higher          !=         !=         !=         !=         !=
        detail_differs          ==         ==         !=         !=         !=
        x_subclass              ==         ==         ==?        ==?        !=
        y_subclass              ==         ==         ==?        ==?        !=
        x_foreign               !=         !=         !=?        !=?        !=
        y_foreign               !=         !=         !=?        !=?        !=
        x_subclass_other_value  !=         !=         !=         !=         !=
        y_subclass_other_value  !=         !=         !=         !=         !=
        x_foreign_other_value   !=         !=         !=         !=         !=
        y_foreign_other_value   !=         !=         !=         !=         !=
    ''',
    'EqAsymmetric': '''
                                trusted    unrelated  type       all        strict
        equal                   ==         ==         ==         ==         ==
        x_value_lower           ==         ==         !=         !=         !=
        x_value_higher          !=         !=         !=         !=         !=
        detail_differs          !=         !=         !=         !=         !=
        x_subclass              ==         ==         ==?        ==?        !=
        y_subclass              ==         ==         ==?        ==?        !=
        x_foreign               !=         !=         !=?        !=?        !=
        y_foreign               !=         !=         !=?        !=?        !=
        x_subclass_other_value  ==         ==         !=*        !=*        !=
        y_subclass_other_value  !=         !=         !=         !=         !=
        x_foreign_other_value   !=         !=         !=         !=         !=
        y_foreign_other_value   !=         !=         !=         !=         !=
    ''',
    'EqAcceptsForeign': '''
                                trusted    unrelated  type       all        strict
        equal                   ==         ==         ==         ==         ==
        x_value_lower           !=         !=         !=         !=         !=
        x_value_higher          !=         !=         !=         !=         !=
        detail_differs          !=         !=         !=         !=         !=
        x_subclass              ==         ==         ==?        ==?        !=
        y_subclass              ==         ==         ==?        ==?        !=
        x_foreign               ==         ==         ==?        ==?        !=
        y_foreign               ==         ==         ==?        ==?        !=
        x_subclass_other_value  !=         !=         !=         !=         !=
        y_subclass_other_value  !=         !=         !=         !=         !=
        x_foreign_other_value   !=         !=         !=         !=         !=
        y_foreign_other_value   !=         !=         !=         !=         !=
    ''',
    'list': '''
                                trusted    unrelated  type       all        strict
        equal                   ==         ==         ==         ==         ==
        x_value_lower           !=         !=         !=         !=         !=
        x_value_higher          !=         !=         !=         !=         !=
        detail_differs          !=         !=         !=         !=         !=
        x_subclass              ==         ==         ==         ==         !=
        y_subclass              ==         ==         ==         ==         !=
        x_foreign               ==         ==         ==         ==         !=
        y_foreign               ==         ==         ==         ==         !=
        x_subclass_other_value  !=         !=         !=         !=         !=
        y_subclass_other_value  !=         !=         !=         !=         !=
        x_foreign_other_value   !=         !=         !=         !=         !=
        y_foreign_other_value   !=         !=         !=         !=         !=
    ''',
    'dict': '''
                                trusted    unrelated  type       all        strict
        equal                   ==         ==         ==         ==         ==
        x_value_lower           !=         !=         !=         !=         !=
        x_value_higher          !=         !=         !=         !=         !=
        detail_differs          !=         !=         !=         !=         !=
        x_subclass              ==         ==         ==         ==         !=
        y_subclass              ==         ==         ==         ==         !=
        x_foreign               !=         !=         !=         !=         !=
        y_foreign               !=         !=         !=         !=         !=
        x_subclass_other_value  !=         !=         !=         !=         !=
        y_subclass_other_value  !=         !=         !=         !=         !=
        x_foreign_other_value   !=         !=         !=         !=         !=
        y_foreign_other_value   !=         !=         !=         !=         !=
    ''',
}


@dataclass(frozen=True)
class Expected:
    outcome: str
    known_bug: bool = False
    open_question: bool = False


def parse_cell(cell: str) -> Expected:
    if cell.endswith('*'):
        return Expected(cell[:-1], known_bug=True)
    if cell.endswith('?'):
        return Expected(cell[:-1], open_question=True)
    return Expected(cell)


def parse_grid(grid: str) -> dict[tuple[str, str], Expected]:
    header, *rows = grid.split('\n')[1:-1]
    columns = header.split()
    parsed = {}
    for row in rows:
        relation, *cells = row.split()
        for column, cell in zip(columns, cells, strict=True):
            parsed[relation, column] = parse_cell(cell)
    return parsed


def parse() -> dict[tuple[str, str, str], Expected]:
    columns = {mode.column: mode.name for mode in MODES}
    spec = {}
    for behaviour, grid in GRIDS.items():
        for (relation, column), expected in parse_grid(grid).items():
            spec[behaviour, relation, columns[column]] = expected
    return spec


SPEC = parse()
EXPECTED_KEYS = {(b.name, r.name, m.name) for b in BEHAVIOURS for r in RELATIONS for m in MODES}


def marks_for(expected: Expected) -> list[pytest.MarkDecorator]:
    if expected.known_bug:
        return [pytest.mark.xfail(strict=True, reason='known bug, see spec.py')]
    return []
