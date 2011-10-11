# Copyright (c) 2011 Simplistix Ltd
# See license.txt for license details.

import atexit
import warnings

from testfixtures import compare
from testfixtures.components import TestComponents
from unittest import TestCase

class ComponentsTests(TestCase):

    def test_atexit(self):
        c = TestComponents()
        self.assertTrue(
            TestComponents.atexit in [t[0] for t in atexit._exithandlers]
            )
        with warnings.catch_warnings(record=True) as w:
            c.atexit()
            self.assertTrue(len(w), 1)
            compare(str(w[0].message), (
                "TestComponents instances not uninstalled by shutdown!"
                ))
        c.uninstall()
