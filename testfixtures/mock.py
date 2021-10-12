"""
A facade for either :mod:`unittest.mock` or its `rolling backport`__, if it is
installed, with a preference for the latter as it may well have newer functionality
and bugfixes.

The facade also contains any bugfixes that are critical to the operation of
functionality provided by testfixtures.

__ https://mock.readthedocs.io
"""
from __future__ import absolute_import

import sys

try:
    from mock import *
    from mock.mock import _Call
    from mock.mock import call as mock_call
    from mock.mock import version_info as backport_version
except ImportError:
    backport_version = None
    class MockCall:
        pass
    mock_call = MockCall()
    try:
        from unittest.mock import *
        from unittest.mock import _Call
    except ImportError:  # pragma: no cover
        pass
try:
    from unittest.mock import call as unittest_mock_call
except ImportError:
    class UnittestMockCall:
        pass
    unittest_mock_call = UnittestMockCall()


has_backport = backport_version is not None
has_unittest_mock = sys.version_info >= (3, 3, 0)

assert (
    (has_backport and backport_version[:3] > (2, 0, 0)) or
    (3, 6, 7) < sys.version_info[:3] < (3, 7, 0) or
    sys.version_info[:3] > (3, 7, 1)
), 'Please upgrade Python or Mock Backport'
parent_name = '_mock_parent'
