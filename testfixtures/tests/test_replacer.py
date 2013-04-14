# Copyright (c) 2008-2013 Simplistix Ltd
# See license.txt for license details.

from doctest import DocTestSuite, REPORT_NDIFF, ELLIPSIS
from testfixtures import Replacer
from unittest import TestSuite

class TestReplacer:

    def test_function(self): # pragma: no branch
        """
        >>> from testfixtures.tests import sample1
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

    def test_class(self): # pragma: no branch
        """
        >>> from testfixtures.tests import sample1
        >>> sample1.X()
        <testfixtures.tests.sample1.X ...>
        
        >>> class XReplacement(sample1.X): pass
        
        >>> r = Replacer()
        >>> r.replace('testfixtures.tests.sample1.X',XReplacement)
        
        >>> sample1.X()
        <testfixtures.tests.test_replacer.XReplacement ...>
        >>> sample1.X().y()
        'original y'
        
        >>> r.restore()
        
        >>> sample1.X()
        <testfixtures.tests.sample1.X ...>
        """

    def test_method(self): # pragma: no branch
        """
        >>> from testfixtures.tests import sample1
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

    def test_class_method(self): # pragma: no branch
        """
        >>> from testfixtures.tests import sample1
        >>> sample1.X.aMethod()
        <class ...testfixtures.tests.sample1.X...>
        
        >>> def rMethod(cls):
        ...   return (cls,1)
        
        >>> r = Replacer()
        >>> r.replace('testfixtures.tests.sample1.X.aMethod',rMethod)
        
        >>> sample1.X.aMethod()
        (<class ...testfixtures.tests.sample1.X...>, 1)
        
        >>> r.restore()
        
        >>> sample1.X.aMethod()
        <class ...testfixtures.tests.sample1.X...>
        """

    def test_multiple_replace(self): # pragma: no branch
        """
        >>> from testfixtures.tests import sample1
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
        '<testfixtures.tests.sample1.X ...>'

        >>> r.restore()

        >>> sample1.z()
        'original z'
        >>> sample1.X().y()
        'original y'
        """

    def test_gotcha(self): # pragma: no branch
        """
        Just because you replace an object in one context:

        >>> from testfixtures.tests import sample1
        >>> from testfixtures.tests import sample2
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

    def test_remove_called_twice(self): # pragma: no branch
        """
        >>> from testfixtures.tests import sample1
        
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

    def test_with_statement(self): # pragma: no branch
        """
        >>> from testfixtures.tests import sample1
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

    def test_not_there(self): # pragma: no branch
        """
        >>> def test_bad():
        ...   return 'moo'
        
        >>> with Replacer() as r:
        ...   r.replace('testfixtures.tests.sample1.bad',test_bad)
        Traceback (most recent call last):
        ...
        AttributeError: Original 'bad' not found
        """

    def test_not_there_ok(self): # pragma: no branch
        """
        >>> from testfixtures.tests import sample1
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

    def test_replace_all_to_mock_json_dumps_function(self): # pragma: no branch
        """
        First, import the original dumps function
        >>> from json import dumps

        Tuck away a pointer to that function in some module (like it had
        imported it itself). 
        >>> from testfixtures.tests import sample1
        >>> sample1.dumps = dumps

        Create a reference to the object within a function closure. 
        >>> def json_dump(obj):
        ...     return dumps(obj)
        ... 
        
        Test the function is working 
        >>> print sample1.dumps([1, 2, 3])
        [1, 2, 3]
        >>> print json_dump([1, 2, 3])
        [1, 2, 3]

        Now, replace 'all' references to this function in the entire memory
        space.
        >>> with Replacer() as r:
        ...
        ...     def mock_dumper(obj):
        ...         return '<MOCK JSON OBJECT>'
        ...
        ...     r.replace('json.dumps', mock_dumper, all=True)
        ...
        ...     import json
        ...
        ...     print json.dumps([1, 2, 3])
        ...     print dumps([1, 2, 3])
        ...     print sample1.dumps([1, 2, 3])
        ...     print json_dump([1, 2, 3])
        ... 
        <MOCK JSON OBJECT>
        <MOCK JSON OBJECT>
        <MOCK JSON OBJECT>
        <MOCK JSON OBJECT>

        
        Now, outside of the 'with' suite, the original 'dumps' function from 
        the json module is restored.

        >>> import json
        >>> print json.dumps([1, 2, 3])
        [1, 2, 3]

        >>> print dumps([1, 2, 3])
        [1, 2, 3]

        >>> print sample1.dumps([1, 2, 3])
        [1, 2, 3]

        >>> print json_dump([1, 2, 3])
        [1, 2, 3]
        """


    def test_replace_all_in_dict(self): # pragma: no branch
        """
        
        First, setup a small list and insert it a couple of times into 
        a dictionary.
        >>> some_list = [1, 2, 3]
        >>> 
        >>> my_map = {'a': some_list, 'b': 20, 'c': ['C', some_list]}

        Now, replace it _everywhere_ it is found. 
        #>>> with Replacer() as r:
        #...     new_list = ['X', 'Y', 'Z']
        #...     r.replace(testfixtures.tests.test_replacer.my_map.a', new_list, all=True)
        #...     print sorted(my_map.items())
        #... 
        [('a', ['X', 'Y', 'Z']), ('b', 20), ('c', ['C', ['X', 'Y', 'Z']])]
        
        
        And now, once out of the with suite, the map is restored
         
        >>> print sorted(my_map.items())
        [('a', [1, 2, 3]), ('b', 20), ('c', ['C', [1, 2, 3]])]
        """

    def test_replace_all_on_strings(self): # pragma: no branch
        """
        When using the 'all' parameter, the target nor the replacement can be 
        scalars.

        >>> r = Replacer()
        >>>
        >>> r.replace('json.__version__', '0.0.0', all=True)
        Traceback (most recent call last):
            ...
        TypeError: The target cannot be a scalar type when using 'all'.

        >>> r.replace('json.dumps', 100, all=True)
        Traceback (most recent call last):
            ...
        TypeError: The replacement cannot be a scalar type when using 'all'.
        """





def test_suite():
    return DocTestSuite(optionflags=REPORT_NDIFF | ELLIPSIS)


