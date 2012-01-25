from __future__ import with_statement
# Copyright (c) 2010-2011 Simplistix Ltd
# See license.txt for license details.

from testfixtures import OutputCapture, compare
from unittest import TestCase, TestSuite, makeSuite

import sys

class TestOutputCapture(TestCase):

    def test_compare_strips(self):
        with OutputCapture() as o:
            print ' Bar! '
        o.compare('Bar!')

    def test_stdout_and_stderr(self):
        with OutputCapture() as o:
            print >>sys.stdout,'hello'
            print >>sys.stderr,'out'
            print >>sys.stdout,'there'
            print >>sys.stderr,'now'
        o.compare("hello\nout\nthere\nnow\n")

    def test_original_restore(self):
        o_out, o_err = sys.stdout, sys.stderr
        with OutputCapture() as o:
            self.assertFalse(sys.stdout is o_out)
            self.assertFalse(sys.stderr is o_err)
        self.assertTrue(sys.stdout is o_out)
        self.assertTrue(sys.stderr is o_err)

    def test_double_disable(self):
        o_out, o_err = sys.stdout, sys.stderr
        with OutputCapture() as o:
            self.assertFalse(sys.stdout is o_out)
            self.assertFalse(sys.stderr is o_err)
            o.disable()
            self.assertTrue(sys.stdout is o_out)
            self.assertTrue(sys.stderr is o_err)
            o.disable()
            self.assertTrue(sys.stdout is o_out)
            self.assertTrue(sys.stderr is o_err)
        self.assertTrue(sys.stdout is o_out)
        self.assertTrue(sys.stderr is o_err)

    def test_double_enable(self):
        o_out, o_err = sys.stdout, sys.stderr
        with OutputCapture() as o:
            o.disable()
            self.assertTrue(sys.stdout is o_out)
            self.assertTrue(sys.stderr is o_err)
            o.enable()
            self.assertFalse(sys.stdout is o_out)
            self.assertFalse(sys.stderr is o_err)
            o.enable()
            self.assertFalse(sys.stdout is o_out)
            self.assertFalse(sys.stderr is o_err)
        self.assertTrue(sys.stdout is o_out)
        self.assertTrue(sys.stderr is o_err)
