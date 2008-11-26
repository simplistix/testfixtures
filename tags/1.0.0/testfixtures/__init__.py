# Copyright (c) 2008 Simplistix Ltd
# See license.txt for license details.

import logging

from datetime import datetime,timedelta,date
from difflib import unified_diff
from functools import partial
from inspect import getargspec
from new import classobj
from resolve import resolve
from time import mktime
from types import ClassType,GeneratorType,MethodType

class Wrappings:
    def __init__(self):
        self.before = []
        self.after = []
        
def wrap(before,after=None):
    def wrapper(wrapped):
        if getattr(wrapped,'_wrappings',None) is None:
            w = Wrappings()
            def wrapping(*args,**kw):
                args = list(args)
                to_add = len(getargspec(wrapped)[0][len(args):])
                added = 0
                for c in w.before:
                    r = c()
                    if added<to_add:
                        args.append(r)
                        added+=1
                try:
                    return wrapped(*args,**kw)
                finally:
                    for c in w.after:
                        c()
            f = wrapping
            f._wrappings = w
        else:
            f = wrapped
        w = f._wrappings
        w.before.append(before)
        if after is not None:
            w.after.insert(0,after)
        return f
    return wrapper

class Replacer:

    def __init__(self,replace_returns=False):
        self.originals = {}
        self.replace_returns=replace_returns

    def replace(self,target,replacement):
        container,attribute = target.rsplit('.',1)
        container = resolve(container)
        t_obj = getattr(container,attribute)
        if (isinstance(t_obj,MethodType)
            and t_obj.im_self is container
            and not isinstance(replacement,MethodType)):
            replacement = classmethod(replacement)
        self.originals[target] = t_obj
        setattr(container,attribute,replacement)
        if self.replace_returns:
            return replacement

    def restore(self):
        for target,original in tuple(self.originals.items()):
            self.replace(target,original)
            del self.originals[target]
            
    def __call__(self,original_function):
        self.original_function = original_function
        return self.new_function

def replace(target,replacement):
    r  = Replacer(replace_returns=True)
    return wrap(partial(r.replace,target,replacement),r.restore)

def diff(x,y):
    return '\n'.join(
        tuple(unified_diff(
            x.split('\n'),
            y.split('\n'),
            lineterm='')
              )[2:]
        )

identity = object()

def compare(x,y):
    if isinstance(x,GeneratorType) and isinstance(x,GeneratorType):
        x = tuple(x)
        y = tuple(y)
    if x!=y:
        message = None
        if isinstance(x,basestring) and isinstance(y,basestring):
            if len(x)>10 or len(y)>10:
                if '\n' in x or '\n' in y:
                    message = '\n'+diff(x,y)
                else:
                    message = '\n%r\n!=\n%r'%(x,y)
        elif ((isinstance(x,tuple) and isinstance(y,tuple))
              or
              (isinstance(x,list) and isinstance(y,list))):
            l_x = len(x)
            l_y = len(y)
            i = 0
            while i<l_x and i<l_y:
                if cmp(x[i],y[i]):
                    break
                i+=1
            message = (
                'Sequence not as expected:\n'
                '  same:%r\n'
                ' first:%r\n'
                'second:%r')%(
                x[:i],
                x[i:],
                y[i:],
                )
        if message is None:
            message = '%r != %r'%(x,y)
        raise AssertionError(message)
    return identity
    
def generator(*args):
    for i in args:
        yield i

class Comparison:
    def __init__(self,t,v=None):
        if isinstance(t,basestring):
            c = resolve(t)
        elif isinstance(t,ClassType):
            c = t
        elif isinstance(t,type) and issubclass(t,BaseException):
            c = t
        elif isinstance(t,BaseException):
            c = t.__class__
            if v is None:
                v = t.args
        else:
            c = t.__class__
            if v is None:
                v=vars(t)
        self.c = c
        self.v = v
        
    def __cmp__(self,other):
        if self.c is not other.__class__:
            return -1
        if self.v is None:
            return 0
        if isinstance(other,BaseException):
            v = other.args
        else:
            v = vars(other)
        return cmp(self.v,v)
    
    def __repr__(self):
        if self.v is None:
            v = ''
        else:
            v = ' with vars %s'%repr(self.v)
        name = getattr(self.c,'__module__','')
        if name:
            name+='.'
        name += getattr(self.c,'__name__','')
        if not name:
            name = repr(self.c)
        return '<C:%s%s>'%(name,v)

class should_raise:

    raised = None

    def __init__(self,callable,exception=None):
        self.callable = callable
        self.expected = exception

    def __call__(self,*args,**kw):
        try:
            self.callable(*args,**kw)
        except Exception,actual:
            self.raised = actual
        if self.expected:
            if cmp(Comparison(self.expected),self.raised):
                raise AssertionError(
                    '%r raised, %r expected' % (self.raised,self.expected)
                    )
        
class LogCapture(logging.Handler):

    def __init__(self, *names):
        logging.Handler.__init__(self)
        if not names:
            names = (None,)
        self.names = names
        self.records = []
        self.oldlevels = {}

    def emit(self, record):
        self.records.append(record)

    def install(self):
        for name in self.names:
            logger = logging.getLogger(name)
            self.oldlevels[name] = logger.level
            logger.setLevel(1)
            logger.addHandler(self)

    def uninstall(self):
        for name in self.names:
            logger = logging.getLogger(name)
            logger.setLevel(self.oldlevels[name])
            logger.removeHandler(self)

    def actual(self):
        for r in self.records:
            yield (r.name,r.levelname,r.getMessage())
    
    def __str__(self):
        return '\n'.join(["%s %s\n  %s" % r for r in self.actual()])

    def check(self,*expected):
        return compare(
            expected,
            tuple(self.actual())
            )

class LogCaptureForDecorator(LogCapture):

    def install(self):
        LogCapture.install(self)
        return self
    
def log_capture(*names):
    l = LogCaptureForDecorator(*names)
    return wrap(l.install,l.uninstall)

@classmethod
def add(cls,*args):
    cls._q.append(cls(*args))

@classmethod
def instantiate(cls):
    r = cls._q.pop(0)
    if not cls._q:
        cls._gap += cls._gap_d
        cls._q.append(r+timedelta(**{cls._gap_t:cls._gap}))
    return r

def test_factory(n,type,gap_t,gap_d,default,args,**to_patch):    
    if args == (None,):
        q = []
    elif args:
        q = [type(*args)]
    else:
        q = [type(*default)]
    to_patch['_q']=q
    to_patch['_gap']=0
    to_patch['_gap_d']=gap_d
    to_patch['_gap_t']=gap_t
    to_patch['add']=add
    return classobj(n,(type,),to_patch)
    
def test_datetime(*args):
    return test_factory(
        'tdatetime',datetime,'seconds',10,(2001,1,1,0,0,0),args,now=instantiate
        )
    
def test_date(*args):
    return test_factory(
        'tdate',date,'days',1,(2001,1,1),args,today=instantiate
        )

class ttimec(datetime):

    def __new__(cls,*args):
        if args:
            return super(ttimec, cls).__new__(cls,*args)
        else:
            return mktime(cls.time().timetuple())

def test_time(*args):
    return test_factory(
        'ttime',ttimec,'seconds',1,(2001,1,1,0,0,0),args,time=instantiate
        )
