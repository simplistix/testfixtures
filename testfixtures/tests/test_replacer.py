from __future__ import with_statement
# Copyright (c) 2008 Simplistix Ltd
# See license.txt for license details.

from doctest import DocTestSuite, REPORT_NDIFF,ELLIPSIS
from testfixtures import Replacer
from unittest import TestSuite

class TestReplacer:

    def test_function(self):
        """
        >>> import sample1
        >>> sample1.z()
        'original z'
        
        >>> def test_z():
        ...   return 'replacement z'
        
        >>> r = Replacer()
        >>> r.replace('testfixtures.tests.sample1.z',test_z)
        
        >>> sample1.z()
        'replacement z'
        
        >>> r.restore()
        
        >>> sample1.z()
        'original z'
        """

    def test_class(self):
        """
        >>> import sample1
        >>> sample1.X()
        <testfixtures.tests.sample1.X instance at ...>
        
        >>> class XReplacement(sample1.X): pass
        
        >>> r = Replacer()
        >>> r.replace('testfixtures.tests.sample1.X',XReplacement)
        
        >>> sample1.X()
        <testfixtures.tests.test_replacer.XReplacement instance at ...>
        >>> sample1.X().y()
        'original y'
        
        >>> r.restore()
        
        >>> sample1.X()
        <testfixtures.tests.sample1.X instance at ...>
        """

    def test_method(self):
        """
        >>> import sample1
        >>> sample1.X().y()
        'original y'
        
        >>> def test_y(self):
        ...   return 'replacement y'

        >>> r = Replacer()
        >>> r.replace('testfixtures.tests.sample1.X.y',test_y)

        >>> sample1.X().y()[:38]
        'replacement y'

        >>> r.restore()

        >>> sample1.X().y()
        'original y'
        """

    def test_class_method(self):
        """
        >>> import sample1
        >>> sample1.X.aMethod()
        <class testfixtures.tests.sample1.X at ...>
        
        >>> def rMethod(cls):
        ...   return (cls,1)
        
        >>> r = Replacer()
        >>> r.replace('testfixtures.tests.sample1.X.aMethod',rMethod)
        
        >>> sample1.X.aMethod()
        (<class testfixtures.tests.sample1.X at ...>, 1)
        
        >>> r.restore()
        
        >>> sample1.X.aMethod()
        <class testfixtures.tests.sample1.X at ...>
        """

    def test_multiple_replace(self):
        """
        >>> import sample1
        >>> sample1.z()
        'original z'
        >>> sample1.X().y()
        'original y'
        
        >>> def test_y(self):
        ...   return repr(self)
        >>> def test_z():
        ...   return 'replacement z'

        >>> r = Replacer()
        >>> r.replace('testfixtures.tests.sample1.z',test_z)
        >>> r.replace('testfixtures.tests.sample1.X.y',test_y)

        >>> sample1.z()
        'replacement z'
        >>> sample1.X().y()
        '<testfixtures.tests.sample1.X instance at ...>'

        >>> r.restore()

        >>> sample1.z()
        'original z'
        >>> sample1.X().y()
        'original y'
        """

    def test_gotcha(self):
        """
        Just because you replace an object in one context:

        >>> import sample1,sample2
        >>> sample1.z()
        'original z'
        
        >>> def test_z():
        ...   return 'replacement z'

        >>> r = Replacer()
        >>> r.replace('testfixtures.tests.sample1.z',test_z)

        >>> sample1.z()
        'replacement z'

        Doesn't meant that it's replaced in all contexts:
        
        >>> sample2.z()
        'original z'

        >>> r.restore()
        """
    
    def test_no_dot_in_name(self):
        """
        You need at least one dot in the replacment
        target since everything before the last dot
        defines the object where the replacement will
        take place and the part after the last dot
        defines the name to be replaced.

        If you don't have any dots, you'll get an error:
        
        >>> def test():pass
        >>> Replacer().replace('sample1',test)
        Traceback (most recent call last):
        ...
        ValueError: need more than 1 value to unpack
        """
    
    def test_remove_called_twice(self):
        """
        >>> import sample1
        
        >>> def test_z():
        ...   return 'replacement z'
        
        >>> r = Replacer()
        >>> r.replace('testfixtures.tests.sample1.z',test_z)
        
        >>> r.restore()
        >>> sample1.z()
        'original z'
        
        >>> r.restore()
        >>> sample1.z()
        'original z'
        """

    def test_with_statement(self):
        """
        >>> import sample1
        >>> sample1.z()
        'original z'
        
        >>> def test_z():
        ...   return 'replacement z'
        
        >>> with Replacer() as r:
        ...   r.replace('testfixtures.tests.sample1.z',test_z)
        ...   sample1.z()
        'replacement z'
        
        >>> sample1.z()
        'original z'
        """

    def test_not_there(self):
        """
        >>> def test_bad():
        ...   return 'moo'
        
        >>> with Replacer() as r:
        ...   r.replace('testfixtures.tests.sample1.bad',test_bad)
        Traceback (most recent call last):
        ...
        AttributeError: Original 'bad' not found
        """
        
    def test_not_there_ok(self):
        """
        >>> import sample1
        >>> sample1.bad()
        Traceback (most recent call last):
        ...
        AttributeError: 'module' object has no attribute 'bad'
        
        >>> def test_bad():
        ...   return 'moo'
        
        >>> with Replacer() as r:
        ...   r.replace('testfixtures.tests.sample1.bad',test_bad,strict=False)
        ...   sample1.bad()
        'moo'
        
        >>> sample1.bad()
        Traceback (most recent call last):
        ...
        AttributeError: 'module' object has no attribute 'bad'
        """
        
def test_suite():
    return TestSuite((
        DocTestSuite(optionflags=REPORT_NDIFF|ELLIPSIS),
        ))
