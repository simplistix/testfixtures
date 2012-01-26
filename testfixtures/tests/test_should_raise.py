from __future__ import with_statement
# Copyright (c) 2008-2010 Simplistix Ltd
# See license.txt for license details.

from testfixtures import should_raise,ShouldRaise,Comparison as C
from unittest import TestCase,TestSuite,makeSuite

from .compat import py_27_plus

class TestShouldRaise(TestCase):

    def test_no_params(self):
        def to_test():
            raise ValueError('wrong value supplied')
        should_raise(to_test,ValueError('wrong value supplied'))()
    
    def test_no_exception(self):
        def to_test():
            pass
        try:
            should_raise(to_test,ValueError())()
        except AssertionError,e:
            self.assertEqual(
                e,
                C(AssertionError('None raised, ValueError() expected'))
                )
        else:
            self.fail('No exception raised!')
    
    def test_wrong_exception(self):
        def to_test():
            raise ValueError('bar')
        try:
            should_raise(to_test,ValueError('foo'))()
        except AssertionError,e:
            self.assertEqual(
                e,
                C(AssertionError("ValueError('bar',) raised, ValueError('foo',) expected"))
                )
        else:
            self.fail('No exception raised!')
    
    def test_only_exception_class(self):
        def to_test():
            raise ValueError('bar')
        should_raise(to_test,ValueError)()
    
    def test_no_supplied_or_raised(self):
        # effectvely we're saying "something should be raised!"
        # but we want to inspect s.raised rather than making
        # an up-front assertion
        def to_test():
            pass
        try:
            should_raise(to_test)()
        except AssertionError,e:
            self.assertEqual(
                e,
                C(AssertionError("No exception raised!"))
                )
        else:
            self.fail('No exception raised!')
    
    def test_args(self):
        def to_test(*args):
            raise ValueError('%s'%repr(args))
        should_raise(
            to_test,
            ValueError('(1,)')
            )(1)
    
    def test_kw_to_args(self):
        def to_test(x):
            raise ValueError('%s'%x)
        should_raise(
            to_test,
            ValueError('1')
            )(x=1)

    def test_kw(self):
        def to_test(**kw):
            raise ValueError('%r'%kw)
        should_raise(
            to_test,
            ValueError("{'x': 1}")
            )(x=1)

    def test_both(self):
        def to_test(*args,**kw):
            raise ValueError('%r %r'%(args,kw))
        should_raise(
            to_test,
            ValueError("(1,) {'x': 2}")
            )(1,x=2)

    def test_method_args(self):
        class X:
            def to_test(self,*args):
                self.args = args
                raise ValueError()
        x = X()
        should_raise(x.to_test,ValueError)(1,2,3)
        self.assertEqual(x.args,(1,2,3))
    
    def test_method_kw(self):
        class X:
            def to_test(self,**kw):
                self.kw = kw
                raise ValueError()
        x = X()
        should_raise(x.to_test,ValueError)(x=1,y=2)
        self.assertEqual(x.kw,{'x':1,'y':2})

    def test_method_both(self):
        class X:
            def to_test(self,*args,**kw):
                self.args = args
                self.kw = kw
                raise ValueError()
        x = X()
        should_raise(x.to_test,ValueError)(1,y=2)
        self.assertEqual(x.args,(1,))
        self.assertEqual(x.kw,{'y':2})

    def test_index(self):
        x = []
        should_raise(x,IndexError)[1]
        
    def test_getitem(self):
        x = {}
        should_raise(x,KeyError)['x']
        
    def test_class_class(self):
        class Test:
            def __init__(self, x):
                # The TypeError is raised due to the mis-matched parameters
                # so the pass never gets executed
                pass # pragma: no cover
        r = should_raise(Test, TypeError)()
        self.assertEqual(r, None)
        
    def test_return(self):
        # return of a should_raise is always None!
        def to_test():
            raise ValueError('wrong value supplied')
        s = should_raise(to_test)
        r = s()
        self.assertEqual(s.raised,C(ValueError('wrong value supplied')))
        self.failUnless(r is None)
        
    def test_exception_return(self):
        def to_test(*args):
            raise ValueError('%s'%repr(args))
        r = should_raise(to_test,ValueError('(1,)'))(1)
        self.assertEqual(r,None)
    
    def test_raised(self):
        def to_test():
            raise ValueError('wrong value supplied')
        s = should_raise(to_test)
        s()
        self.assertEqual(s.raised,C(ValueError('wrong value supplied')))
        
    def test_catch_baseexception_1(self):
        def to_test():
            raise SystemExit()
        should_raise(to_test,SystemExit)()
    
    def test_catch_baseexception_2(self):
        def to_test():
            raise KeyboardInterrupt()
        should_raise(to_test,KeyboardInterrupt)()

    def test_with_exception_class_supplied(self):
        with ShouldRaise(ValueError):
            raise ValueError('foo bar')

    def test_with_exception_supplied(self):
        with ShouldRaise(ValueError('foo bar')):
            raise ValueError('foo bar')

    def test_with_exception_supplied_wrong_args(self):
        try:
            with ShouldRaise(ValueError('foo')):
                raise ValueError('bar')
        except AssertionError,e:
            self.assertEqual(
                e,
                C(AssertionError("ValueError('bar',) raised, ValueError('foo',) expected"))
                )
        else:
            self.fail('No exception raised!')

    def test_neither_supplied(self):
        with ShouldRaise():
            raise ValueError('foo bar')
    
    def test_with_no_exception_when_expected(self):
        try:
            with ShouldRaise(ValueError('foo')):
                pass
        except AssertionError,e:
            self.assertEqual(
                e,
                C(AssertionError("None raised, ValueError('foo',) expected"))
                )
        else:
            self.fail('No exception raised!')

    def test_with_no_exception_when_neither_expected(self):
        try:
            with ShouldRaise():
                pass
        except AssertionError,e:
            self.assertEqual(
                e,
                C(AssertionError("No exception raised!"))
                )
        else:
            self.fail('No exception raised!')

    def test_with_getting_raised_exception(self):
        with ShouldRaise() as s:
            raise ValueError('foo bar')
        self.assertEqual(C(ValueError('foo bar')),s.raised)
    
    def test_import_errors_1(self):
        with ShouldRaise(ImportError('No module named textfixtures.foo.bar')) as s:
            import textfixtures.foo.bar
    
    def test_import_errors_2(self):
        with ShouldRaise(ImportError('X')) as s:
            raise ImportError('X')

    def test_custom_exception(self):

        class FileTypeError(Exception):
            def __init__(self,value):
                self.value = value

        with ShouldRaise(FileTypeError('X')) as s:
            raise FileTypeError('X')

    def test_assert_keyerror_raised(self):
        # 2.7 compat
        if py_27_plus:  # pragma: no cover
            expected = "KeyError('foo',) raised, AttributeError('foo',) expected"
        else:  # pragma: no cover
            expected = "KeyError(('foo',),) raised, AttributeError('foo',) expected"
            
        class Dodgy(dict):
            def __getattr__(self,name):
                # NB: we forgot to turn our KeyError into an attribute error
                return self[name]
        try:
            with ShouldRaise(AttributeError('foo')):
                Dodgy().foo
        except AssertionError,e:
            self.assertEqual(
                C(AssertionError(expected)),
                e
                )
        else:
            self.fail('No exception raised!')

    def test_decorator_usage(self):

        @should_raise(ValueError('bad'))
        def to_test():
            raise ValueError('bad')

        to_test()
