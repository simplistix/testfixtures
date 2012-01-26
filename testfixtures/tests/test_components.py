from __future__ import with_statement
# Copyright (c) 2011-2012 Simplistix Ltd
# See license.txt for license details.

from nose.plugins.skip import SkipTest

try:
    from testfixtures.components import TestComponents
except ImportError:  # pragma: no cover
    raise SkipTest('zope.component is not available')

import atexit

from testfixtures import compare
from unittest import TestCase

from .compat import catch_warnings

class ComponentsTests(TestCase):

    def test_atexit(self):
        c = TestComponents()
        self.assertTrue(
            TestComponents.atexit in [t[0] for t in atexit._exithandlers]
            )
        with catch_warnings(record=True) as w:
            c.atexit()
            self.assertTrue(len(w), 1)
            compare(str(w[0].message), (
                "TestComponents instances not uninstalled by shutdown!"
                ))
        c.uninstall()
        # check re-running has no ill effects
        c.atexit()
