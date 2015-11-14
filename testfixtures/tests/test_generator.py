# Copyright (c) 2008 Simplistix Ltd
# See license.txt for license details.

from unittest import TestCase, TestSuite, makeSuite

from testfixtures import generator
from types import GeneratorType


class TestG(TestCase):

    def test_example(self):
        g = generator(1, 2, 3)
        self.failUnless(isinstance(g, GeneratorType))
        self.assertEqual(tuple(g), (1, 2, 3))

    def test_from_sequence(self):
        s = (1, 2, 3)
        g = generator(*s)
        self.failUnless(isinstance(g, GeneratorType))
        self.assertEqual(tuple(g), (1, 2, 3))
