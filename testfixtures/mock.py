"""
testfixtures.mock
-----------------

A facade for either :mod:`unittest.mock` or its `rolling backport`__, if it is
installed, with a preference for the latter as it may well have newer functionality
and bugfixes.

The facade also contains any bugfixes that are critical to the operation of
functionality provided by TestFixtures.

__ https://mock.readthedocs.io
"""
from __future__ import absolute_import

try:
    from mock import *
    from mock.mock import _Call
except ImportError:
    from unittest.mock import *
    from unittest.mock import _Call


def __eq__(self, other):
    if other is ANY:
        return True
    try:
        len_other = len(other)
    except TypeError:
        return False

    self_name = ''
    if len(self) == 2:
        self_args, self_kwargs = self
    else:
        self_name, self_args, self_kwargs = self

    if (getattr(self, 'parent', None) and getattr(other, 'parent', None)
            and self.parent != other.parent):
        return False

    other_name = ''
    if len_other == 0:
        other_args, other_kwargs = (), {}
    elif len_other == 3:
        other_name, other_args, other_kwargs = other
    elif len_other == 1:
        value, = other
        if isinstance(value, tuple):
            other_args = value
            other_kwargs = {}
        elif isinstance(value, str):
            other_name = value
            other_args, other_kwargs = (), {}
        else:
            other_args = ()
            other_kwargs = value
    elif len_other == 2:
        # could be (name, args) or (name, kwargs) or (args, kwargs)
        first, second = other
        if isinstance(first, str):
            other_name = first
            if isinstance(second, tuple):
                other_args, other_kwargs = second, {}
            else:
                other_args, other_kwargs = (), second
        else:
            other_args, other_kwargs = first, second
    else:
        return False

    if self_name and other_name != self_name:
        return False

    # this order is important for ANY to work!
    return (other_args, other_kwargs) == (self_args, self_kwargs)


_Call.__eq__ = __eq__
