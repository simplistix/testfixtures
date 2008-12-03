# Copyright (c) 2008 Simplistix Ltd
# See license.txt for license details.

from testfixtures import Comparison as C
from testfixtures.tests.sample1 import TestClassA,a_function
from unittest import TestCase,TestSuite,makeSuite

class AClass:

    def __init__(self,x,y=None):
        self.x = x
        if y:
            self.y = y

    def __repr__(self):
        return '<AClass>'
        
class TestC(TestCase):
    
    def test_example(self):
        # In this pattern, we want to check a sequence is
        # of the correct type and order.
        r = a_function()
        self.assertEqual(r,(
            C('testfixtures.tests.sample1.TestClassA'),
            C('testfixtures.tests.sample1.TestClassB'),
            C('testfixtures.tests.sample1.TestClassA'),
            ))
        # We also want to check specific parts of some
        # of the returned objects' attributes 
        self.assertEqual(r[0].args[0],1)
        self.assertEqual(r[1].args[0],2)
        self.assertEqual(r[2].args[0],3)
                        
    def test_example_with_object(self):
        # Here we see compare an object with a Comparison
        # based on an object of the same type and with the
        # same attributes:
        self.assertEqual(
            C(AClass(1,2)),
            AClass(1,2),
            )
        # ...even though the original class doesn't support
        # meaningful comparison:
        self.assertNotEqual(
            AClass(1,2),
            AClass(1,2),
            )

    def test_example_with_vars(self):
        # Here we use a Comparison to make sure both the
        # type and attributes of an object are correct.
        self.assertEqual(
            C('testfixtures.tests.test_comparison.AClass',
              x=1,y=2),
            AClass(1,2),
            )
        
    def test_example_with_odd_vars(self):
        # If the variable names class with parameters to the
        # Comparison constructor, they can be specified in a
        # dict:
        self.assertEqual(
            C('testfixtures.tests.test_comparison.AClass',
              {'x':1,'y':2}),
            AClass(1,2),
            )
        
    def test_example_not_strict(self):
        # Here, we only care about the 'x' attribute of
        # the AClass object, so we turn strict mode off.
        # With strict mode off, only attributes specified
        # in the Comparison object will be checked, and
        # any others will be ignored.
        self.assertEqual(
            C('testfixtures.tests.test_comparison.AClass',
              x=1,
              strict=False),
            AClass(1,2),
            )
                        
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

    def test_class_and_kw(self):
        self.assertEqual(
            TestClassA(1),
            C(TestClassA,args=(1,))
            )

    def test_class_and_vars_and_kw(self):
        self.assertEqual(
            AClass(1,2),
            C(AClass,{'x':1},y=2)
            )
        
    def test_object_and_vars(self):
        # vars passed are used instead of the object's
        self.assertEqual(
            TestClassA(1),
            C(TestClassA(),{'args':(1,)})
            )

    def test_object_and_kw(self):
        # kws passed are used instead of the object's
        self.assertEqual(
            TestClassA(1),
            C(TestClassA(),args=(1,))
            )

    def test_object_not_strict(self):
        # only attributes on comparison object
        # are used
        self.assertEqual(
            C(AClass(1),strict=False),
            AClass(1,2),
            )

    def test_example_with_missing_vars(self):
        try:
            self.assertEqual(
                C('testfixtures.tests.test_comparison.AClass',
                  x=1,y=2,z=3),
                AClass(1,2)
                )
        except Exception,e:
            self.failUnless(isinstance(e,AssertionError))
            self.assertEqual(
                e.args,
                ("<C:testfixtures.tests.test_comparison.AClass with vars {'y': 2, 'x': 1, 'z': 3}> != <AClass>",)
                )
        else:
            self.fail('No exception raised!')

    def test_not_strict_missing_from_actual(self):
        try:
            self.assertEqual(
                C('testfixtures.tests.test_comparison.AClass',
                  z=3,
                  strict=False),
                AClass(1,2)
                )
        except Exception,e:
            self.failUnless(isinstance(e,AssertionError))
            self.assertEqual(
                e.args,
                ("<C:testfixtures.tests.test_comparison.AClass with vars {'z': 3}> != <AClass>",)
                )
        else:
            self.fail('No exception raised!')
        
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
