# Copyright (c) 2008-2011 Simplistix Ltd
# See license.txt for license details.

import logging,os,sys

from calendar import timegm
from cStringIO import StringIO
from datetime import datetime,timedelta,date
from difflib import unified_diff
from functools import partial,wraps
from inspect import getargspec
from new import classobj
from pprint import pformat
from re import compile, MULTILINE
from shutil import rmtree
from tempfile import mkdtemp
from types import ClassType,GeneratorType,MethodType
from zope.dottedname.resolve import resolve

class Wrappings:
    def __init__(self):
        self.before = []
        self.after = []
        
def wrap(before,after=None):
    """
    A decorator that causes the supplied callables to be called before
    or after the wrapped callable, as appropriate.
    """
    def wrapper(wrapped):
        if getattr(wrapped,'_wrappings',None) is None:
            w = Wrappings()
            @wraps(wrapped)
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

not_there =object()

class Replacer:
    """
    These are used to manage the mocking out of objects so that units
    of code can be tested without having to rely on their normal
    dependencies.
    """

    def __init__(self,replace_returns=False):
        self.originals = {}
        self.replace_returns=replace_returns

    def replace(self,target,replacement,strict=True):
        """
        Replace the specified target with the supplied replacement.

        :param target: A string containing the dotted-path to the
                       object to be replaced. This path may specify a
                       module in a package, an attribute of a module,
                       or any attribute of something contained within
                       a module.

        :param replacement: The object to use as a replacement.

        :param strict: When `True`, an exception will be raised if an
                       attempt is made to replace an object that does
                       not exist.
        """
        container,attribute = target.rsplit('.',1)
        container = resolve(container)
        t_obj = getattr(container,attribute,not_there)
        if t_obj is not_there and strict:
            raise AttributeError('Original %r not found'%attribute)
        if (isinstance(t_obj,MethodType)
            and t_obj.im_self is container
            and not isinstance(replacement,MethodType)):
            replacement_to_use = classmethod(replacement)
        else:
            replacement_to_use = replacement
        self.originals[target] = t_obj
        setattr(container,attribute,replacement_to_use)
        if self.replace_returns:
            return replacement

    def restore(self):
        """
        Restore all the original objects that have been replaced by
        calls to the :meth:`replace` method of this :class:`Replacer`.
        """
        for target,original in tuple(self.originals.items()):
            if original is not_there:
                container,attribute = target.rsplit('.',1)
                container = resolve(container)
                delattr(container,attribute)
            else:
                self.replace(target,original)
            del self.originals[target]
            
    def __enter__(self):
        return self
    
    def __exit__(self,type,value,traceback):
        self.restore()

def replace(target,replacement,strict=True):
    """
    A decorator to replace a target object for the duration of a test
    function.

    :param target: A string containing the dotted-path to the
                   object to be replaced. This path may specify a
                   module in a package, an attribute of a module,
                   or any attribute of something contained within
                   a module.

    :param replacement: The object to use as a replacement.

    :param strict: When `True`, an exception will be raised if an
                   attempt is made to replace an object that does
                   not exist.
    """
    r  = Replacer(replace_returns=True)
    return wrap(partial(r.replace,target,replacement,strict),r.restore)

def diff(x,y):
    """
    A shorthand function that uses :mod:`difflib` to return a
    string representing the differences between the two string
    arguments.

    Most useful when comparing multi-line strings.
    """
    return '\n'.join(
        tuple(unified_diff(
            x.split('\n'),
            y.split('\n'),
            lineterm='')
              )[2:]
        )

identity = object()

trailing_whitespace_re = compile('\s+$',MULTILINE)

def strip_blank_lines(text):
    result = []
    for line in text.split('\n'):
        if line and not line.isspace():
            result.append(line)
    return '\n'.join(result)

def compare(x,y,blanklines=True,trailing_whitespace=True):
    """
    Compare the two supplied arguments and raise an
    :class:`AssertionError` if they are not the same.

    The :class:`AssertionError` raised will attempt to provide
    descriptions of the differences found.

    :param blanklines: If `False`, then when comparing multi-line
                       strings, any blank lines in either argument
                       will be ignored.

    :param trailing_whitespace: If `False`, then when comparing
                                multi-line strings, trailing
                                whilespace on lines will be ignored.
    """
    # pre-processing
    if isinstance(x,GeneratorType) and isinstance(x,GeneratorType):
        x = tuple(x)
        y = tuple(y)
    if isinstance(x,basestring) and isinstance(y,basestring):
        if not trailing_whitespace:
            x = trailing_whitespace_re.sub('',x)
            y = trailing_whitespace_re.sub('',y)
        if not blanklines:
            x = strip_blank_lines(x)
            y = strip_blank_lines(y)

    # the check
    if x==y:
        return identity

    # error reporting
    message = None
    if isinstance(x,basestring) and isinstance(y,basestring):
            
        if len(x)>10 or len(y)>10:
            if '\n' in x or '\n' in y:
                message = '\n'+diff(x,y)
            else:
                message = '\n%r\n!=\n%r'%(x,y)
    elif not (blanklines and trailing_whitespace):
        raise TypeError(
            "if blanklines or trailing_whitespace are not True, only string "
            "arguments should be passed, got %r and %r" % (x,y)
            )
    elif ((isinstance(x,tuple) and isinstance(y,tuple))
          or
          (isinstance(x,list) and isinstance(y,list))):
        l_x = len(x)
        l_y = len(y)
        i = 0
        while i<l_x and i<l_y:
            if x[i]!=y[i]:
                break
            i+=1
        message = (
            'Sequence not as expected:\n\n'
            'same:\n%s\n\n'
            'first:\n%s\n\n'
            'second:\n%s')%(
            pformat(x[:i]),
            pformat(x[i:]),
            pformat(y[i:]),
            )
    if message is None:
        message = '%r != %r'%(x,y)
    raise AssertionError(message)
    
def generator(*args):
    """
    A utility function for creating a generator that will yield the
    supplied arguments.
    """
    for i in args:
        yield i

class Comparison:
    """
    These are used when you need to compare objects
    that do not natively support comparison. 

    :param object_or_type: The object or class from which to create the
                           :class:`Comparison`.
    
    :param attribute_dict: An optional dictionary containing attibutes
                           to place on the :class:`Comparison`.
    
    :param strict: If true, any expected attributes not present or extra
                   attributes not expected on the object involved in the
                   comparison will cause the comparison to fail.

    :param attributes: Any other keyword parameters passed will placed
                       as attributes on the :class:`Comparison`.
    """
    
    failed = None
    def __init__(self,
                 object_or_type,
                 attribute_dict=None,
                 strict=True,
                 **attributes):
        if attributes:
            if attribute_dict is None:
                attribute_dict = attributes
            else:
                attribute_dict.update(attributes)
        if isinstance(object_or_type,basestring):
            c = resolve(object_or_type)
        elif isinstance(object_or_type,(ClassType,type)):
            c = object_or_type
        elif isinstance(object_or_type,BaseException):
            c = object_or_type.__class__
            if attribute_dict is None:
                attribute_dict = vars(object_or_type)
                attribute_dict['args']=object_or_type.args
        else:
            c = object_or_type.__class__
            if attribute_dict is None:
                attribute_dict=vars(object_or_type)
        self.c = c
        self.v = attribute_dict
        self.strict = strict
        
    def __eq__(self,other):
        if self.c is not other.__class__:
            self.failed = True
            return False
        if self.v is None:
            return True
        self.failed = {}
        if isinstance(other,BaseException):
            v = vars(other)
            v['args']=other.args
        else:
            try:
                v = vars(other)
            except TypeError:
                if self.strict:
                    raise TypeError(
                        '%r does not support vars() so cannot '
                        'do strict comparison' % other
                        )
                v = {}
                for k in self.v.keys():
                    try:
                        v[k]=getattr(other,k)
                    except AttributeError:
                        pass
        e = set(self.v.keys())
        a = set(v.keys())
        for k in e.difference(a):
            try:
                # class attribute?
                v[k]=getattr(other,k)
            except AttributeError:
                self.failed[k]='%s not in other' % repr(self.v[k])
            else:
                a.add(k)
        if self.strict:
            for k in a.difference(e):
                self.failed[k]='%s not in Comparison' % repr(v[k])
        for k in e.intersection(a):
            ev = self.v[k]
            av = v[k]
            if ev!=av:
                self.failed[k]='%r != %r' % (ev,av)
        if self.failed:
            return False
        return True

    def __ne__(self,other):
        return not(self==other)
    
    def __repr__(self,indent=2):
        full = False
        if self.failed is True:
            v = 'wrong type</C>'
        elif self.v is None:
            v = ''
        else:
            full = True
            v = '\n'
            if self.failed:
                vd = self.failed
                r = str
            else:
                vd = self.v
                r = repr
            for vk,vv in sorted(vd.items()):
                if isinstance(vv,Comparison):
                    vvr = vv.__repr__(indent+2)
                else:
                    vvr = r(vv)
                v+=(' '*indent+'%s:%s\n'%(vk,vvr))
            v+=(' '*indent)+'</C>'
        name = getattr(self.c,'__module__','')
        if name:
            name+='.'
        name += getattr(self.c,'__name__','')
        if not name:
            name = repr(self.c)
        r = '<C%s:%s>%s'%(self.failed and '(failed)' or '',name,v)
        if full:
            return '\n'+(' '*indent)+r
        else:
            return r

class StringComparison:
    """
    An object that can be used in comparisons of expected and actual
    strings where the string expected matches a pattern rather than a
    specific concrete string.

    :param regex_source: A string containing the source for a regular
                         expression that will be used whenever this
                         :class:`StringComparison` is compared with
                         any :class:`basestring` instance.
    
    """
    def __init__(self,regex_source):
        self.re = compile(regex_source)

    def __eq__(self,other):
        if not isinstance(other,basestring):
            return
        if self.re.match(other):
            return True
        return False

    def __ne__(self,other):
        return not self==other

    def __repr__(self):
        return '<S:%s>' % self.re.pattern

    def __lt__(self,other):
        return self.re.pattern<other
        
    def __gt__(self,other):
        return self.re.pattern>other
        
    def __cmp__(self,other):
        return cmp(self.re.pattern,other)
        
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
            
class should_raise:
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
        self.sr = should_raise(None,self.exception)
        return self.sr
    
    def __exit__(self,type,value,traceback):
        # bug in python :-(
        if isinstance(value,str):
            value = type(value)
        self.sr.handle(value)
        return True
        
class LogCapture(logging.Handler):
    """
    These are used to capture entries logged to the Python logging
    framework and make assertions about what was logged.

    :param names: A sequence of strings containing the dotted names of
                  loggers to capture. By default, the root logger is
                  captured.
                  
    :param install: If `True`, the :class:`LogCapture` will be
                    installed as part of its instantiation.
    """
    
    instances = set()
    
    def __init__(self, names=None, install=True):
        logging.Handler.__init__(self)
        if not isinstance(names,tuple):
            names = (names,)
        self.names = names
        self.oldlevels = {}
        self.oldhandlers = {}
        self.clear()
        if install:
            self.install()

    def clear(self):
        "Clear any entries that have been captured."
        self.records = []
        
    def emit(self, record):
        self.records.append(record)

    def install(self):
        """
        Install this :class:`LogHandler` into the Python logging
        framework for the named loggers.

        This will remove any existing handlers for those loggers and
        drop their level to 1 in order to capture all logging.
        """
        for name in self.names:
            logger = logging.getLogger(name)
            self.oldlevels[name] = logger.level
            self.oldhandlers[name] = logger.handlers
            logger.setLevel(1)
            logger.handlers = [self]
        self.instances.add(self)

    def uninstall(self):
        """
        Un-install this :class:`LogHandler` from the Python logging
        framework for the named loggers.

        This will re-instate any existing handlers for those loggers
        that were removed during installation and retore their level
        that prior to installation.
        """
        if self in self.instances:
            for name in self.names:
                logger = logging.getLogger(name)
                logger.setLevel(self.oldlevels[name])
                logger.handlers = self.oldhandlers[name]
            self.instances.remove(self)

    @classmethod
    def uninstall_all(cls):
        "This will uninstall all existing :class:`LogHandler` objects."
        for i in tuple(cls.instances):
            i.uninstall()
        
    def actual(self):
        for r in self.records:
            yield (r.name,r.levelname,r.getMessage())
    
    def __str__(self):
        if not self.records:
            return 'No logging captured'
        return '\n'.join(["%s %s\n  %s" % r for r in self.actual()])

    def check(self,*expected):
        """
        This will compare the captured entries with the expected
        entries provided and raise an :class:`AssertionError` if they
        do not match.

        :param expected: A sequence of 3-tuples containing the
                         expected log entries. Each tuple should be of
                         the form (logger_name, string_level, message)
        """
        return compare(
            expected,
            tuple(self.actual())
            )

    def __enter__(self):
        return self
    
    def __exit__(self,type,value,traceback):
        self.uninstall()

class LogCaptureForDecorator(LogCapture):

    def install(self):
        LogCapture.install(self)
        return self
    
def log_capture(*names):
    """
    A decorator for making a :class:`LogCapture` installed an
    available for the duration of a test function.

    :param names: An optional sequence of names specifying the loggers
                  to be captured. If not specified, the root logger
                  will be captured.
    """
    l = LogCaptureForDecorator(names or None,install=False)
    return wrap(l.install,l.uninstall)

# stuff for date, time and datetime mocking below:

@classmethod
def add(cls,*args):
    cls._q.append(cls(*args))

@classmethod
def set_(cls,*args):
    if cls._q:
        cls._q.pop()
    cls.add(*args)

def __add__(self,other):
    r = super(self.__class__,self).__add__(other)
    if self._ct:
        r = self._ct(r)
    return r

@classmethod
def instantiate(cls):
    r = cls._q.pop(0)
    if not cls._q:
        cls._gap += cls._gap_d
        n = r+timedelta(**{cls._gap_t:cls._gap})
        if cls._ct:
            n = cls._ct(n)
        cls._q.append(n)
    return r

def test_factory(n,type,default,args,**to_patch):    
    q = []
    to_patch['_q']=q
    to_patch['add']=add
    to_patch['set']=set_
    to_patch['__add__']=__add__
    class_ = classobj(n,(type,),to_patch)
    if args==(None,):
        pass
    elif args:
        q.append(class_(*args))
    else:
        q.append(class_(*default))
    return class_
    
def correct_date_method(self):
    return self._date_type(
        self.year,
        self.month,
        self.day
        )

@classmethod
def correct_datetime(cls,dt):
    return cls(
        dt.year,
        dt.month,
        dt.day,
        dt.hour,
        dt.minute,
        dt.second,
        dt.microsecond,
        dt.tzinfo,
        )

def test_datetime(*args,**kw):
    if 'delta' in kw:
        gap = kw['delta']
        gap_delta = 0
    else:
        gap = 0
        gap_delta = 10
    delta_type = kw.get('delta_type','seconds')
    date_type = kw.get('date_type',date)
    return test_factory(
        'tdatetime',datetime,(2001,1,1,0,0,0),args,
        _ct=correct_datetime,
        now=instantiate,
        _gap = gap,
        _gap_d = gap_delta,
        _gap_t = delta_type,
        date = correct_date_method,
        _date_type = date_type,
        )
    
@classmethod
def correct_date(cls,d):
    return cls(
        d.year,
        d.month,
        d.day,
        )

def test_date(*args,**kw):
    if 'delta' in kw:
        gap = kw['delta']
        gap_delta = 0
    else:
        gap = 0
        gap_delta = 1
    delta_type = kw.get('delta_type','days')
    return test_factory(
        'tdate',date,(2001,1,1),args,
        _ct=correct_date,
        today=instantiate,
        _gap = gap,
        _gap_d = gap_delta,
        _gap_t = delta_type,
        )

class ttimec(datetime):

    def __new__(cls,*args):
        if args:
            return super(ttimec, cls).__new__(cls,*args)
        else:
            return float(timegm(cls.instantiate().utctimetuple()))

def test_time(*args,**kw):
    if 'delta' in kw:
        gap = kw['delta']
        gap_delta = 0
    else:
        gap = 0
        gap_delta = 1
    delta_type = kw.get('delta_type','seconds')
    return test_factory(
        'ttime',ttimec,(2001,1,1,0,0,0),args,
        _ct=None,
        instantiate=instantiate,
        _gap = gap,
        _gap_d = gap_delta,
        _gap_t = delta_type,
        )

# this marks the end of the test date, datetime and time stuff

class TempDirectory:
    """
    A class representing a temporary directory on disk.

    :param ignore: A sequence of strings containing regular expression
                   patterns that match filenames that should be
                   ignored by the :class:`TempDirectory` listing and
                   checking methods.

    :param create: If `True`, the temporary directory will be created
                   as part of class instantiation.

    :param path: If passed, this should be a string containing a
                 physical path to use as the temporary directory. When
                 passed, :class:`TempDirectory` will not create a new
                 directory to use.
    """
    
    instances = set()

    #: The physical path of the :class:`TempDirectory` on disk
    path = None
    
    def __init__(self,ignore=(),create=True,path=None):
        self.ignore = []
        for regex in ignore:
            self.ignore.append(compile(regex))
        self.path = path
        if create:
            self.create()

    def create(self):
        """
        Create a temporary directory for this instance to use if one
        has not already been created.
        """
        if self.path:
            return self
        self.path = mkdtemp()
        self.instances.add(self)
        return self

    def cleanup(self):
        """
        Delete the temporary directory and anything in it.
        This :class:`TempDirectory` cannot be used again unless
        :meth:`create` is called.
        """
        if self in self.instances and os.path.exists(self.path):
            rmtree(self.path)
            self.instances.remove(self)

    @classmethod
    def cleanup_all(cls):
        """
        Delete all temporary directories associated with all
        :class:`TempDirectory` objects.
        """
        for i in tuple(cls.instances):
            i.cleanup()

    def actual(self,path=None,recursive=False):
        if path:
            path = self._join(path)
        else:
            path = self.path
        result = []
        if recursive:
            for dirpath,dirnames,filenames in os.walk(path):
                dirpath = '/'.join(dirpath[len(path)+1:].split(os.sep))
                if dirpath:
                    dirpath += '/'
                    result.append(dirpath)
                for name in sorted(filenames):
                    result.append(dirpath+name)
        else:
            for n in os.listdir(path):
                result.append(n)
        filtered = []
        for path in sorted(result):
            ignore = False
            for regex in self.ignore:
                if regex.search(path):
                    ignore = True
                    break
            if ignore:
                continue
            filtered.append(path)
        return filtered
    
    def listdir(self,path=None,recursive=False):
        """
        Print the contents of the specified directory.

        :param path: The path to list, which can be:

                     * `None`, indicating the root of the temporary
                       directory should be listed.

                     * A tuple of strings, indicating that the
                       elements of the tuple should be used as directory
                       names to traverse from the root of the
                       temporary directory to find the directory to be
                       listed.

                     * A forward-slash separated string, indicating
                       the directory or subdirectory that should be
                       traversed to from the temporary directory and
                       listed.

        :param recursive: If `True`, the directory specified will have
                          its subdirectories recursively listed too.
        """
        actual = self.actual(path,recursive)
        if not actual:
            print 'No files or directories found.'
        for n in actual:
            print n

    def check(self,*expected):
        """
        Compare the contents of the temporary directory with the
        expected contents supplied.

        This method only checks the root of the temporary directory.

        :param expected: A sequence of strings containing the names
                         expected in the directory.
        """
        compare(expected,tuple(self.actual()))

    def check_dir(self,dir,*expected):
        """
        Compare the contents of the specified subdirectory of the
        temporary directory with the expected contents supplied.

        This method will only check the contents of the subdirectory
        specified and will not recursively check subdirectories.
        
        :param dir: The subdirectory to check, which can be:

                     * A tuple of strings, indicating that the
                       elements of the tuple should be used as directory
                       names to traverse from the root of the
                       temporary directory to find the directory to be
                       checked.

                     * A forward-slash separated string, indicating
                       the directory or subdirectory that should be
                       traversed to from the temporary directory and
                       checked.

        :param expected: A sequence of strings containing the names
                         expected in the directory.
        """
        compare(expected,tuple(self.actual(dir)))

    def check_all(self,dir,*expected):
        """
        Recursively compare the contents of the specified directory
        with the expected contents supplied.

        :param dir: The directory to check, which can be:

                     * A tuple of strings, indicating that the
                       elements of the tuple should be used as directory
                       names to traverse from the root of the
                       temporary directory to find the directory to be
                       checked.

                     * A forward-slash separated string, indicating
                       the directory or subdirectory that should be
                       traversed to from the temporary directory and
                       checked.

                     * An empty string, indicating that the whole
                       temporary directory should be checked.

        :param expected: A sequence of strings containing the paths
                         expected in the directory. These paths should
                         be forward-slash separated and relative to
                         the root of the temporary directory.
        """
        compare(expected,tuple(self.actual(dir,recursive=True)))

    def _join(self,name):
        if isinstance(name,basestring):
            name = name.split('/')
        if not name[0]:
            raise ValueError(
                'Attempt to read or write outside the temporary Directory'
                )
        return os.path.join(self.path,*name)
        
    def makedir(self,dirpath,
                # for backwards compatibility
                path=True):
        """
        Make an empty directory at the specified path within the
        temporary directory. Any intermediate subdirectories that do
        not exist will also be created.

        :param dirpath: The directory to create, which can be:
        
                        * A tuple of strings. 

                        * A forward-slash separated string.

        :returns: The full path of the created directory.
        """
        thepath = self._join(dirpath)
        os.makedirs(thepath)
        if path:
            return thepath
    
    def write(self,filepath,data,
              # for backwards compatibility
              path=True):
        """
        Write the supplied data to a file at the specified path within
        the temporary directory. Any subdirectories specified that do
        not exist will also be created.

        The file will always be written in binary mode.
        
        :param filepath: The path to the file to create, which can be:
        
                         * A tuple of strings. 

                         * A forward-slash separated string.

        :param data: A string containing the data to be written.
        
        :returns: The full path of the file written.
        """
        if isinstance(filepath,basestring):
            filepath = filepath.split('/')
        if len(filepath)>1:
            dirpath = self._join(filepath[:-1])
            if not os.path.exists(dirpath):
                os.makedirs(dirpath)
        thepath = self._join(filepath)
        f = open(thepath,'wb')
        f.write(data)
        f.close()
        if path:
            return thepath

    def getpath(self,path):
        """
        Return the full path on disk that corresponds to the path
        relative to the temporary directory that is passed in.

        :param path: The path to the file to create, which can be:
        
                     * A tuple of strings. 

                     * A forward-slash separated string.

        :returns: A string containing the full path.
        """
        return self._join(path)
    
    def read(self,filepath):
        """
        Reading the file at the specified path within the temporary
        directory.

        The file is always read in binary mode.

        :param filepath: The path to the file to read, which can be:
        
                         * A tuple of strings. 

                         * A forward-slash separated string.

        :returns: A string containing the data read.
        """
        f = open(self._join(filepath),'rb')
        data = f.read()
        f.close()
        return data

    def __enter__(self):
        return self
    
    def __exit__(self,type,value,traceback):
        self.cleanup()

def tempdir(*args,**kw):
    """
    A decorator for making a :class:`TempDirectory` available for the
    duration of a test function.

    All arguments and parameters are passed through to the
    :class:`TempDirectory` constructor.
    """
    kw['create']=False
    l = TempDirectory(*args,**kw)
    return wrap(l.create,l.cleanup)

class OutputCapture:
    """
    A context manager for capturing output to the
    :attr:`sys.stdout` and :attr:`sys.stderr` streams.
    """
    def __enter__(self):
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        self.output = sys.stdout = sys.stderr = StringIO()
        return self

    def __exit__(self,*args):
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr

    def compare(self,expected):
        """
        Compare the captured output to that expected. If the output is
        not the same, an :class:`AssertionError` will be raised.

        :param expected: A string containing the expected output.
        """
        compare(expected.strip(),self.output.getvalue().strip())

