from __future__ import with_statement
# Copyright (c) 2008-2011 Simplistix Ltd
# See license.txt for license details.

from functools import partial, wraps
from testfixtures import Comparison

class ShouldRaiseWrapper:

    def __init__(self,sr,wrapped):
        self.sr = sr
        self.wrapped = wrapped

    def __call__(self,*args,**kw):
        try:
            self.wrapped(*args,**kw)
        except BaseException,actual:
            self.sr.handle(actual)
        else:
            self.sr.handle(None)
            
class _should_raise:
    """
    A wrapper to use when you want to assert that an exception is
    raised.

    .. note::

      Consider using the :class:`ShouldRaise` context manager
      instead.

    :param callable: the object to be wrapped.

    :param exception: This can be one of the following:
    
                      * `None`, indicating that an exception must be
                        raised, but the type is unimportant.
                        
                      * An exception class, indicating that the type
                        of the exception is important but not the
                        parameters it is created with.
                        
                      * An exception instance, indicating that an
                        exception exactly matching the one supplied
                        should be raised.  
    """

    raised = None

    def __init__(self,callable,exception=None):
        self.callable = callable
        self.expected = exception

    def handle(self,actual):
        self.raised = actual
        if self.expected:
                if Comparison(self.expected) != actual:
                    raise AssertionError(
                        '%r raised, %r expected' % (actual,self.expected)
                        )
        elif not actual:
            raise AssertionError('No exception raised!')
            
    def __getattr__(self,name):
        return ShouldRaiseWrapper(self,getattr(self.callable,name))

    # __call__ is special :-S
    def __call__(self,*args,**kw):
        return ShouldRaiseWrapper(self,partial(self.callable))(*args,**kw)

class ShouldRaise:
    """
    This context manager is used to assert that an exception is raised
    within the context it is managing.

    :param exception: This can be one of the following:
    
                      * `None`, indicating that an exception must be
                        raised, but the type is unimportant.
                        
                      * An exception class, indicating that the type
                        of the exception is important but not the
                        parameters it is created with.
                        
                      * An exception instance, indicating that an
                        exception exactly matching the one supplied
                        should be raised.  
    """

    def __init__(self,exception=None):
        self.exception = exception

    def __enter__(self):
        self.sr = _should_raise(None,self.exception)
        return self.sr
    
    def __exit__(self,type,value,traceback):
        # bug in python :-(
        if type is not None and not isinstance(value,type):
            # fixed in 2.7 onwards!
            value = type(value) # pragma: no cover
        self.sr.handle(value)
        return True

class should_raise(object):
    """
    A decorator to assert that the decorated function will raised
    an exception. An exception class or exception instance may be
    passed to check more specifically exactly what exception will be
    raised.

    :param exception: This can be one of the following:
    
                      * `None`, indicating that an exception must be
                        raised, but the type is unimportant.
                        
                      * An exception class, indicating that the type
                        of the exception is important but not the
                        parameters it is created with.
                        
                      * An exception instance, indicating that an
                        exception exactly matching the one supplied
                        should be raised.  
    
    """

    # backwards compatibility for the old should_raise
    # wrapper stuff
    def __new__(cls,target_or_exception, exception=None):
        if exception is not None or callable(target_or_exception):
            return _should_raise(target_or_exception, exception)
        else:
            return super(should_raise,cls).__new__(cls)
        
    def __init__(self, exception=None):
        self.exception=exception

    def __call__(self,target):

        @wraps(target)
        def _should_raise_wrapper(*args, **kw):
            with ShouldRaise(self.exception):
                target(*args,**kw)
                
        return _should_raise_wrapper
            
