# Copyright (c) 2008 Simplistix Ltd
# See license.txt for license details.

from testfixtures import Comparison as C
from testfixtures.tests.sample1 import TestClassA,a_function
from unittest import TestCase,TestSuite,makeSuite

class TestC(TestCase):
    
    def test_example(self):
        r = a_function()
        self.assertEqual(r,(
            C('testfixtures.tests.sample1.TestClassA'),
            C('testfixtures.tests.sample1.TestClassB'),
            C('testfixtures.tests.sample1.TestClassA'),
            ))
        self.assertEqual(r[0].args[0],1)
        self.assertEqual(r[1].args[0],2)
        self.assertEqual(r[2].args[0],3)
                        
    def test_repr_module(self):
        self.assertEqual(repr(C('datetime')),'<C:datetime>')

    def test_repr_class(self):
        self.assertEqual(
            repr(C('testfixtures.tests.sample1.TestClassA')),
            '<C:testfixtures.tests.sample1.TestClassA>'
            )

    def test_repr_function(self):
        self.assertEqual(
            repr(C('testfixtures.tests.sample1.z')),
            '<C:testfixtures.tests.sample1.z>'
            )

    def test_repr_instance(self):
        self.assertEqual(
            repr(C(TestClassA('something'))),
            "<C:testfixtures.tests.sample1.TestClassA with vars {'args': ('something',)}>"
            )

    def test_repr_exception(self):
        self.assertEqual(
            repr(C(ValueError('something'))),
            "<C:exceptions.ValueError with vars ('something',)>"
            )

    def test_repr_class_and_vars(self):
        self.assertEqual(
            repr(C(TestClassA,{'args':(1,)})),
            "<C:testfixtures.tests.sample1.TestClassA with vars {'args': (1,)}>"
            )

    def test_first(self):
        self.assertEqual(
            C('testfixtures.tests.sample1.TestClassA'),
            TestClassA()
            )
        
    def test_second(self):
        self.assertEqual(
            TestClassA(),
            C('testfixtures.tests.sample1.TestClassA'),
            )

    def test_not_same_first(self):
        self.assertNotEqual(
            C('datetime'),
            TestClassA()
            )
    
    def test_not_same_second(self):
        self.assertNotEqual(
            TestClassA(),
            C('datetime')
            )

    def test_object_supplied(self):
        self.assertEqual(
            TestClassA(1),
            C(TestClassA(1))
            )

    def test_class_and_vars(self):
        self.assertEqual(
            TestClassA(1),
            C(TestClassA,{'args':(1,)})
            )

    def test_object_and_vars(self):
        self.assertEqual(
            TestClassA(1),
            C(TestClassA(),{'args':(1,)})
            )

    def test_exception(self):
        self.assertEqual(
            ValueError('foo'),
            C(ValueError('foo'))
            )

    def test_exception_class_and_args(self):
        self.assertEqual(
            ValueError('foo'),
            C(ValueError,('foo',))
            )

    def test_exception_instance_and_args(self):
        self.assertEqual(
            ValueError('foo'),
            C(ValueError('bar'),('foo',))
            )

    def test_exception_not_same(self):
        self.assertNotEqual(
            ValueError('foo'),
            C(ValueError('bar'))
            )

def test_suite():
    return TestSuite((
        makeSuite(TestC),
        ))
