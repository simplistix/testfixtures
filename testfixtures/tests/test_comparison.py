# Copyright (c) 2008-2012 Simplistix Ltd
# See license.txt for license details.

from testfixtures import Comparison as C, compare, tempdir
from testfixtures.tests.sample1 import TestClassA,a_function
from unittest import TestCase,TestSuite,makeSuite

from .compat import py_27_plus

class AClass:

    def __init__(self,x,y=None):
        self.x = x
        if y:
            self.y = y

    def __repr__(self):
        return '<'+self.__class__.__name__+'>'
        
class BClass(AClass): pass

class WeirdException(Exception):
    def __init__(self,x,y):
        self.x = x
        self.y = y
        
class X(object):
    __slots__ = ['x']
    def __repr__(self):
        return '<X>'

class FussyDefineComparison(object):

    def __init__(self, attr):
        self.attr = attr
        
    def __eq__(self, other):
        if not isinstance(other, self.__class__):  # pragma: no cover
            raise TypeError()
        return False  # pragma: no cover

    def __ne__(self, other):
        return not self==other  # pragma: no cover
    
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
                        
    def test_example_dont_use_c_wrappers_on_both_sides(self):
        # NB: don't use C wrappers on both sides!
        e = ValueError('some message')
        try:
            self.assertEqual(C(e),C(e))
        except Exception,e:
            self.failUnless(isinstance(e,AssertionError))
            self.assertEqual(
                e.args,
                (
                "<C(failed):exceptions.ValueError>wrong type</C> != \n"
                "  <C:exceptions.ValueError>\n"
                "  args:('some message',)\n"
                "  </C>",
                ))
        else:
            self.fail('No exception raised!')
    
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
            "\n"
            "  <C:testfixtures.tests.sample1.TestClassA>\n"
            "  args:('something',)\n"
            "  </C>"
            )

    def test_repr_exception(self):
        self.assertEqual(
            repr(C(ValueError('something'))),
            "\n"
            "  <C:exceptions.ValueError>\n"
            "  args:('something',)\n"
            "  </C>"
            )

    def test_repr_exception_not_args(self):
        self.assertEqual(
            repr(C(WeirdException(1,2))),
            "\n"
            "  <C:testfixtures.tests.test_comparison.WeirdException>\n"
            "  args:()\n"
            "  x:1\n"
            "  y:2\n"
            "  </C>"
            )
    
    def test_repr_class_and_vars(self):
        self.assertEqual(
            repr(C(TestClassA,{'args':(1,)})),
            "\n"
            "  <C:testfixtures.tests.sample1.TestClassA>\n"
            "  args:(1,)\n"
            "  </C>"
            )

    def test_repr_nested(self):
        self.assertEqual(
            repr(C(TestClassA,y=C(AClass),z=C(BClass(1,2)))),
            "\n"
            "  <C:testfixtures.tests.sample1.TestClassA>\n"
            "  y:<C:testfixtures.tests.test_comparison.AClass>\n"
            "  z:\n"
            "    <C:testfixtures.tests.test_comparison.BClass>\n"
            "    x:1\n"
            "    y:2\n"
            "    </C>\n"
            "  </C>"
            )

    def test_repr_failed_wrong_class(self):
        try:
            self.assertEqual(
                C('testfixtures.tests.test_comparison.AClass',
                  x=1,y=2),
                BClass(1,2)
                )
        except Exception,e:
            self.failUnless(isinstance(e,AssertionError))
            self.assertEqual(
                e.args,
                (
                "<C(failed):testfixtures.tests.test_comparison.AClass>wrong type</C> != <BClass>",
                ))
        else:
            self.fail('No exception raised!')

    def test_repr_failed_all_reasons_in_one(self):
        try:
            self.assertEqual(
                C('testfixtures.tests.test_comparison.AClass',
                  y=5,z='missing'),
                AClass(1,2)
                )
        except Exception,e:
            self.failUnless(isinstance(e,AssertionError))
            self.assertEqual(
                e.args,
                (
                "\n"
                "  <C(failed):testfixtures.tests.test_comparison.AClass>\n"
                "  x:1 not in Comparison\n"
                "  y:5 != 2\n"
                "  z:'missing' not in other\n"
                "  </C> != <AClass>",
                ))
        else:
            self.fail('No exception raised!')

    def test_repr_failed_not_in_other(self):
        # use single element tuple to check %
        try:
            self.assertEqual(
                C('testfixtures.tests.test_comparison.AClass',
                  x=1,y=2,z=(3,)),
                AClass(1,2)
                )
        except Exception,e:
            self.failUnless(isinstance(e,AssertionError))
            self.assertEqual(
                e.args,
                (
                "\n"
                "  <C(failed):testfixtures.tests.test_comparison.AClass>\n"
                "  z:(3,) not in other\n"
                "  </C> != <AClass>",
                ))
        else:
            self.fail('No exception raised!')

    def test_repr_failed_not_in_self_strict(self):
        # use single element tuple to check %
        try:
            self.assertEqual(
                C('testfixtures.tests.test_comparison.AClass',y=2),
                AClass((1,),2)
                )
        except Exception,e:
            self.failUnless(isinstance(e,AssertionError))
            self.assertEqual(
                e.args,
                (
                "\n"
                "  <C(failed):testfixtures.tests.test_comparison.AClass>\n"
                "  x:(1,) not in Comparison\n"
                "  </C> != <AClass>",
                ))
        else:
            self.fail('No exception raised!')

    def test_repr_failed_not_in_self_not_strict(self):
        try:
            self.assertEqual(
                C('testfixtures.tests.test_comparison.AClass',
                  x=1,y=2,z=(3,)),
                AClass(1,2)
                )
        except Exception,e:
            self.failUnless(isinstance(e,AssertionError))
            self.assertEqual(
                e.args,
                (
                "\n"
                "  <C(failed):testfixtures.tests.test_comparison.AClass>\n"
                "  z:(3,) not in other\n"
                "  </C> != <AClass>",
                ))
        else:
            self.fail('No exception raised!')

    def test_repr_failed_one_attribute_not_equal(self):
        # use single element tuple to check %
        try:
            self.assertEqual(
                C('testfixtures.tests.test_comparison.AClass',x=1,y=(2,)),
                AClass(1,(3,))
                )
        except Exception,e:
            self.failUnless(isinstance(e,AssertionError))
            self.assertEqual(
                e.args,
                (
                "\n"
                "  <C(failed):testfixtures.tests.test_comparison.AClass>\n"
                "  y:(2,) != (3,)\n"
                "  </C> != <AClass>",
                ))
        else:
            self.fail('No exception raised!')

    def test_repr_failed_nested(self):
        left_side = [C(AClass, x=1, y=2),
                     C(BClass, x=C(AClass, x=1), y=C(AClass))]
        right_side = [AClass(1, 3), AClass(1, 3)]

        # do the comparison
        left_side == right_side
        
        self.assertEqual(
            "[\n"
            "  <C(failed):testfixtures.tests.test_comparison.AClass>\n"
            "  y:2 != 3\n"
            "  </C>, \n"
            "  <C:testfixtures.tests.test_comparison.BClass>\n"
            "  x:\n"
            "    <C:testfixtures.tests.test_comparison.AClass>\n"
            "    x:1\n"
            "    </C>\n"
            "  y:<C:testfixtures.tests.test_comparison.AClass>\n"
            "  </C>]",
            repr(left_side)
            )

        self.assertEqual(
            "[<AClass>, <AClass>]",
            repr(right_side)
            )

    def test_repr_failed_nested_failed(self):
        left_side = [C(AClass, x=1, y=2),
                     C(BClass,
                       x=C(AClass, x=1, strict=False),
                       y=C(AClass, z=2))]
        right_side = [AClass(1, 2),
                      BClass(AClass(1, 2),AClass(1, 2))]
        
        # do the comparison
        left_side == right_side
        
        self.assertEqual(
            "[\n"
            "  <C:testfixtures.tests.test_comparison.AClass>\n"
            "  x:1\n"
            "  y:2\n"
            "  </C>, \n"
            "  <C(failed):testfixtures.tests.test_comparison.BClass>\n"
            "  y:\n"
            "  <C(failed):testfixtures.tests.test_comparison.AClass>\n"
            "  x:1 not in Comparison\n"
            "  y:2 not in Comparison\n"
            "  z:2 not in other\n"
            "  </C> != <AClass>\n"
            "  </C>]",
            repr(left_side)
            )

        self.assertEqual(
            '[<AClass>, <BClass>]',
            repr(right_side)
            )

    def test_repr_failed_passed_failed(self):
        c = C('testfixtures.tests.test_comparison.AClass',x=1,y=2)

        try:
            self.assertEqual(c,AClass(1,3))
        except Exception,e:
            self.failUnless(isinstance(e,AssertionError))
            self.assertEqual(
                e.args,
                (
                "\n"
                "  <C(failed):testfixtures.tests.test_comparison.AClass>\n"
                "  y:2 != 3\n"
                "  </C> != <AClass>",
                ))
        else:
            self.fail('No exception raised!')

        self.assertEqual(c,AClass(1,2))
        
        try:
            self.assertEqual(c,AClass(3,2))
        except Exception,e:
            self.failUnless(isinstance(e,AssertionError))
            self.assertEqual(
                e.args,
                (
                "\n"
                "  <C(failed):testfixtures.tests.test_comparison.AClass>\n"
                "  x:1 != 3\n"
                "  </C> != <AClass>",
                ))
        else:
            self.fail('No exception raised!')


    @tempdir()
    def test_repr_file_different(self,d):
        path = d.write('file','stuff',path=True)
        f = open(path)
        f.close()
        c = C(file,name=path,mode='r',closed=False,strict=False)
        self.assertNotEqual(f,c)
        compare(repr(c),
                "\n"
                "  <C(failed):__builtin__.file>\n"
                "  closed:False != True\n"
                "  </C>",
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

    def test_exception(self):
        self.assertEqual(
            ValueError('foo'),
            C(ValueError('foo'))
            )

    def test_exception_class_and_args(self):
        self.assertEqual(
            ValueError('foo'),
            C(ValueError,args=('foo',))
            )

    def test_exception_instance_and_args(self):
        self.assertEqual(
            ValueError('foo'),
            C(ValueError('bar'),args=('foo',))
            )

    def test_exception_not_same(self):
        self.assertNotEqual(
            ValueError('foo'),
            C(ValueError('bar'))
            )

    def test_exception_no_args_different(self):
        self.assertNotEqual(
            WeirdException(1,2),
            C(WeirdException(1,3))
            )

    def test_exception_no_args_same(self):
        self.assertEqual(
            C(WeirdException(1,2)),
            WeirdException(1,2)
            )
        
    @tempdir()
    def test_file_same(self,d):
        path = d.write('file','stuff',path=True)
        f = open(path)
        f.close()
        self.assertEqual(
            f,
            C(file,name=path,mode='r',closed=True,strict=False)
            )

    def test_no___dict___strict(self):
        x = X()
        try:
            self.assertEqual(
                C(X,x=1),
                x
                )
        except TypeError,e:
            self.assertEqual(e.args,(
                '<X> does not support vars() so cannot do strict comparison',
                ))
        else:
            self.fail('No exception raised!')

    def test_no___dict___not_strict_same(self):
        x = X()
        x.x=1
        self.assertEqual(C(X,x=1,strict=False),x)

    def test_no___dict___not_strict_different(self):
        x = X()
        x.x=2
        try:
            self.assertEqual(
                C(X,x=1,y=2,strict=False),
                x
                )
        except AssertionError,e:
            compare(
                e.args[0],
                (
                "\n"
                "  <C(failed):testfixtures.tests.test_comparison.X>\n"
                "  x:1 != 2\n"
                "  y:2 not in other\n"
                "  </C> != <X>",
                )[0])
        else:
            self.fail('No exception raised!')

    def test_compared_object_defines_eq(self):
        # If an object defines eq, such as Django instances,
        # things become tricky
        
        class Annoying:
            def __init__(self):
                self.eq_called = 0            
            def __eq__(self,other):
                self.eq_called += 1
                if isinstance(other,Annoying):
                    return True
                return False

        self.assertEqual(Annoying(), Annoying())

        # Suddenly, order matters.

        # This order is wrong, as it uses the class's __eq__:
        self.assertFalse(Annoying() == C(Annoying))
        # although this, which is subtle different, does not:
        self.assertFalse(Annoying() != C(Annoying))

        # This is the right ordering:
        self.assertTrue(C(Annoying) == Annoying())
        self.assertFalse(C(Annoying) != Annoying())
        
        # When the ordering is right, you still get the useful
        # comparison representation afterwards
        c = C(Annoying,eq_called=1)        
        c==Annoying()
        self.assertEqual(repr(c),
                         '\n  <C(failed):testfixtures.tests.test_comparison.Annoying>\n'
                         '  eq_called:1 != 0\n'
                         '  </C>')
        
    def test_compared_object_class_attributes(self):

        class Classy(object):
            x = 1
            y = 2

        self.assertEqual(C(Classy,x=1,y=2),Classy())

        c = C(Classy,x=1,y=1)
        self.assertNotEqual(c,Classy())
        self.assertEqual(repr(c),
                         '\n  <C(failed):testfixtures.tests.test_comparison.Classy>\n'
                         '  y:1 != 2\n'
                         '  </C>')

        
        ce = C(Classy,x=1,y=1)
        ca = Classy()
        ca.y=1
        self.assertEqual(ce,ca)

        ce = C(Classy,x=1,y=2)
        ca = Classy()
        ca.y=1
        self.assertNotEqual(ce,ca)
        self.assertEqual(repr(ce),
                         '\n  <C(failed):testfixtures.tests.test_comparison.Classy>\n'
                         '  y:2 != 1\n'
                         '  </C>')

    def test_importerror(self):
        self.failIf(
            C(ImportError('x'))!=ImportError('x')
            )
        
    def test_class_defines_comparison_strictly(self):
        self.assertEqual(
            C('testfixtures.tests.test_comparison.FussyDefineComparison', attr=1),
            FussyDefineComparison(1)
            )

    def test_cant_resolve(self):
        try:
            C('testfixtures.bonkers')
        except Exception, e:
            self.failUnless(isinstance(e, AttributeError))
            self.assertEqual(
                e.args,
                ("'testfixtures.bonkers' could not be resolved",)
                )
        else:
            self.fail('No exception raised!')

    def test_no_name(self):
        class NoName(object): pass
        NoName.__name__ = ''
        NoName.__module__ = ''
        c = C(NoName)
        self.assertEqual(repr(c), "<C:<class '.'>>")
