# Copyright (c) 2008-2011 Simplistix Ltd
# See license.txt for license details.

from testfixtures import replace,compare,should_raise, not_there
from unittest import TestCase,TestSuite,makeSuite

import sample1,sample2

class TestReplace(TestCase):

    def test_function(self):

        def test_z():
            return 'replacement z'

        compare(sample1.z(),'original z')

        @replace('testfixtures.tests.sample1.z',test_z)
        def test_something():
            compare(sample1.z(),'replacement z')

        compare(sample1.z(),'original z')

        test_something()

        compare(sample1.z(),'original z')
        
    def test_class(self):

        OriginalX = sample1.X
        
        class ReplacementX(sample1.X):
            pass

        self.failIf(OriginalX is ReplacementX)
        self.failUnless(isinstance(sample1.X(),OriginalX))

        @replace('testfixtures.tests.sample1.X',ReplacementX)
        def test_something():
            self.failIf(OriginalX is ReplacementX)
            self.failUnless(isinstance(sample1.X(),ReplacementX))

        self.failIf(OriginalX is ReplacementX)
        self.failUnless(isinstance(sample1.X(),OriginalX))

        test_something()

        self.failIf(OriginalX is ReplacementX)
        self.failUnless(isinstance(sample1.X(),OriginalX))

    def test_method(self):

        def test_y(self):
            return self

        compare(sample1.X().y(),'original y')
        
        @replace('testfixtures.tests.sample1.X.y',test_y)
        def test_something():
            self.failUnless(isinstance(sample1.X().y(),sample1.X))

        compare(sample1.X().y(),'original y')
        
        test_something()
        
        compare(sample1.X().y(),'original y')

    def test_class_method(self):

        def rMethod(cls):
            return (cls,1)

        compare(sample1.X().aMethod(),sample1.X)

        @replace('testfixtures.tests.sample1.X.aMethod',rMethod)
        def test_something(r):
            compare(r,rMethod)
            compare(sample1.X().aMethod(),(sample1.X,1))

        compare(sample1.X().aMethod(),sample1.X)
        
        test_something()
        
        compare(sample1.X().aMethod(),sample1.X)

    def test_multiple_replace(self):

        def test_y(self):
            return 'test y'

        def test_z():
            return 'test z'

        compare(sample1.z(),'original z')
        compare(sample1.X().y(),'original y')

        @replace('testfixtures.tests.sample1.z',test_z)
        @replace('testfixtures.tests.sample1.X.y',test_y)
        def test_something(passed_test_y,passed_test_z):
            compare(test_z,passed_test_z)
            compare(test_y,passed_test_y)
            compare(sample1.z(),'test z')
            compare(sample1.X().y(),'test y')

        compare(sample1.z(),'original z')
        compare(sample1.X().y(),'original y')

        test_something()

        compare(sample1.z(),'original z')
        compare(sample1.X().y(),'original y')

    def test_gotcha(self):
        # Just because you replace an object in one context,
        # doesn't meant that it's replaced in all contexts!

        def test_z():
            return 'test z'
        
        compare(sample1.z(),'original z')
        compare(sample2.z(),'original z')
        
        @replace('testfixtures.tests.sample1.z',test_z)
        def test_something():
            compare(sample1.z(),'test z')
            compare(sample2.z(),'original z')
            
        compare(sample1.z(),'original z')
        compare(sample2.z(),'original z')
    
        test_something()

        compare(sample1.z(),'original z')
        compare(sample2.z(),'original z')

    def test_raises(self):

        def test_z():
            return 'replacement z'

        compare(sample1.z(),'original z')

        @replace('testfixtures.tests.sample1.z',test_z)
        def test_something():
            compare(sample1.z(),'replacement z')
            raise Exception()

        compare(sample1.z(),'original z')

        should_raise(test_something)()

        compare(sample1.z(),'original z')


    def test_want_replacement(self):

        o = object()

        @replace('testfixtures.tests.sample1.z',o)
        def test_something(r):
            self.failUnless(r is o)
            self.failUnless(sample1.z is o)

        test_something()

    def test_not_there(self):

        o = object()

        @replace('testfixtures.tests.sample1.bad',o)
        def test_something(r):
            pass
        
        should_raise(
            test_something,
            AttributeError("Original 'bad' not found")
            )()

    def test_not_there_ok(self):

        o = object()

        @replace('testfixtures.tests.sample1.bad',o,strict=False)
        def test_something(r):
            self.failUnless(r is o)
            self.failUnless(sample1.bad is o)

        test_something()

    def test_replace_dict(self):

        from sample1 import someDict

        original = someDict['key']
        replacement = object()
        
        @replace('testfixtures.tests.sample1.someDict.key',replacement)
        def test_something(obj):
            self.failUnless(obj is replacement)
            self.failUnless(someDict['key'] is replacement)

        test_something()

        self.failUnless(someDict['key'] is original)

    def test_replace_dict_remove_key(self):

        from sample1 import someDict

        @replace('testfixtures.tests.sample1.someDict.key',not_there)
        def test_something(obj):
            self.failIf('key' in someDict)

        test_something()

        self.assertEqual(someDict.keys(), ['complex_key','key'])

    def test_replace_dict_not_there(self):

        from sample1 import someDict

        replacement = object()
        
        @replace('testfixtures.tests.sample1.someDict.key2',replacement,strict=False)
        def test_something(obj):
            self.failUnless(obj is replacement)
            self.failUnless(someDict['key2'] is replacement)

        test_something()

        self.assertEqual(someDict.keys(), ['complex_key','key'])

    def test_replace_complex(self):

        from sample1 import someDict

        original = someDict['complex_key'][1]
        replacement = object()
        
        @replace('testfixtures.tests.sample1.someDict.complex_key.1',replacement)
        def test_something(obj):
            self.failUnless(obj is replacement)
            self.assertEqual(someDict['complex_key'],[1,obj,3])

        test_something()

        self.assertEqual(someDict['complex_key'],[1,2,3])


def test_suite():
    return TestSuite((
        makeSuite(TestReplace),
        ))
