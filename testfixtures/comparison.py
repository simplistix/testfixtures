# Copyright (c) 2008-2014 Simplistix Ltd
# See license.txt for license details.

from collections import Iterable
from difflib import unified_diff
from pprint import pformat
from re import compile, MULTILINE
from testfixtures import not_there
from testfixtures.compat import (
    ClassType, Unicode, basestring, PY3, mock_call, unittest_mock_call
    )
from testfixtures.resolve import resolve
from types import GeneratorType


def compare_simple(x, y, context):
    """
    Returns a very simple textual difference between the two supplied objects.
    """
    return '%r%s != %s%r' % (x,
                             context.maybe_include(' (expected)'),
                             context.maybe_include('(actual) '),
                             y)

def compare_with_type(x, y, context):
    """
    Return a textual description of the difference between two objects including
    information about their types.
    """
    source = locals()
    to_render = {}
    for name in 'x', 'y':
        obj = source[name]
        to_render[name] = '{0} ({1!r})'.format(_short_repr(obj), type(obj))
    to_render['x_label'] = context.maybe_include(' (expected)')
    to_render['y_label'] = context.maybe_include('(actual) ')
    return '{x}{x_label} != {y_label}{y}'.format(**to_render)

def compare_sequence(x, y, context):
    """
    Returns a textual description of the differences between the two
    supplied sequences.
    """
    l_x = len(x)
    l_y = len(y)
    i = 0
    while i<l_x and i<l_y:
        if context.different(x[i], y[i], '[%i]' % i):
            break
        i+=1
        
    if l_x == l_y and i ==l_x:
        return 
    
    return (
            'sequence not as expected:\n\n'
            'same:\n%s\n\n'
            '%s:\n%s\n\n'
            '%s:\n%s' ) % (
            pformat(x[:i]),
            context.maybe_include('expected') or 'first',
            pformat(x[i:]),
            context.maybe_include('actual') or 'second',
            pformat(y[i:]),
            )

def compare_generator(x, y, context):
    """
    Returns a textual description of the differences between the two
    supplied generators.

    This is done by first unwinding each of the generators supplied
    into tuples and then passing those tuples to
    :func:`compare_sequence`.
    """
    x = tuple(x)
    y = tuple(y)

    if x==y:
        return

    return compare_sequence(x, y, context)

def compare_tuple(x, y, context):
    """
    Returns a textual difference between two tuples or
    :func:`collections.namedtuple` instances.

    The presence of a ``_fields`` attribute on a tuple is used to
    decide whether or not it is a :func:`~collections.namedtuple`.
    """
    x_fields = getattr(x, '_fields', None)
    y_fields = getattr(y, '_fields', None)
    if x_fields and y_fields:
        if x_fields == y_fields:
            return _compare_mapping(dict(zip(x_fields, x)),
                                    dict(zip(y_fields, y)),
                                    context,
                                    x)
        else:
            return compare_with_type(x, y, context)
    return compare_sequence(x, y, context)

def compare_dict(x, y, context):
    """
    Returns a textual description of the differences between the two
    supplied dictionaries.
    """
    return _compare_mapping(x, y, context, x)

def _compare_mapping(x, y, context, obj_for_class):
    
    x_keys = set(x.keys())
    y_keys = set(y.keys())
    x_not_y = x_keys - y_keys
    y_not_x = y_keys - x_keys
    same = []
    diffs = []
    for key in sorted(x_keys.intersection(y_keys)):
        if context.different(x[key], y[key], '[%r]' % (key,)):
            diffs.append('%r: %s%s != %s%s' % (
                key,
                pformat(x[key]),
                context.maybe_include(' (expected)'),
                context.maybe_include('(actual) '),
                pformat(y[key]),
                ))
        else:
            same.append(key)
    lines = ['%s not as expected:' % obj_for_class.__class__.__name__]
    if same:
        set_same = set(same)
        if set_same == x_keys == y_keys:
            return
        lines.extend(('', 'same:', repr(same)))
    x_label = context.maybe_include('expected') or 'first'
    y_label = context.maybe_include('actual') or 'second'
    if x_not_y:
        lines.extend(('', 'in %s but not %s:' % (x_label, y_label)))
        for key in sorted(x_not_y):
            lines.append('%r: %s' % (
                key,
                pformat(x[key])
                ))
    if y_not_x:
        lines.extend(('', 'in %s but not %s:' % (y_label, x_label)))
        for key in sorted(y_not_x):
            lines.append('%r: %s' % (
                key,
                pformat(y[key])
                ))
    if diffs:
        lines.extend(('', 'values differ:'))
        lines.extend(diffs)
    return '\n'.join(lines)

def compare_set(x, y, context):
    """
    Returns a textual description of the differences between the two
    supplied sets.
    """
    x_not_y = x - y
    y_not_x = y - x
    lines = ['%s not as expected:' % x.__class__.__name__,'']
    x_label = context.maybe_include('expected') or 'first'
    y_label = context.maybe_include('actual') or 'second'
    if x_not_y:
        lines.extend((
            'in %s but not %s:' % (x_label, y_label),
            pformat(sorted(x_not_y)),
            '',
            ))
    if y_not_x:
        lines.extend((
            'in %s but not %s:' % (y_label, x_label),
            pformat(sorted(y_not_x)),
            '',
            ))
    return '\n'.join(lines)+'\n'

trailing_whitespace_re = compile('\s+$',MULTILINE)

def strip_blank_lines(text):
    result = []
    for line in text.split('\n'):
        if line and not line.isspace():
            result.append(line)
    return '\n'.join(result)

def split_repr(text):
    parts = text.split('\n')
    for i, part in enumerate(parts[:-1]):
        parts[i] = repr(part +'\n')
    parts[-1] = repr(parts[-1])
    return '\n'.join(parts)

def compare_text(x, y, context):
    """
    Returns an informative string describing the differences between the two
    supplied strings. The way in which this comparison is performed
    can be controlled using the following parameters:

    :param blanklines: If `False`, then when comparing multi-line
                       strings, any blank lines in either argument
                       will be ignored.

    :param trailing_whitespace: If `False`, then when comparing
                                multi-line strings, trailing
                                whilespace on lines will be ignored.
                                
    :param show_whitespace: If `True`, then whitespace characters in
                            multi-line strings will be replaced with their
                            representations.
    """
    blanklines = context.get_option('blanklines', True)
    trailing_whitespace = context.get_option('trailing_whitespace', True)
    show_whitespace = context.get_option('show_whitespace', False)
    
    if not trailing_whitespace:
        x = trailing_whitespace_re.sub('', x)
        y = trailing_whitespace_re.sub('', y)
    if not blanklines:
        x = strip_blank_lines(x)
        y = strip_blank_lines(y)
    if x==y:
        return
    if len(x) > 10 or len(y) > 10:
        if '\n' in x or '\n' in y:
            if show_whitespace:
                x = split_repr(x)
                y = split_repr(y)
            message = '\n' + diff(x, y,
                                  context.maybe_include('expected'),
                                  context.maybe_include('actual'),)
        else:
            message = '\n%r%s\n!=\n%s%r' % (x,
                                            context.maybe_include('\n(expected)'),
                                            context.maybe_include('(actual)\n'),
                                            y)
    else:
        message = '%r%s != %s%r' % (x,
                                    context.maybe_include(' (expected)'),
                                    context.maybe_include('(actual) '),
                                    y)
    return message

def _short_repr(obj):
    repr_ = repr(obj)
    if len(repr_) > 30:
        repr_ = repr_[:30] + '...'
    return repr_

_registry = {
    dict: compare_dict,
    set: compare_set,
    list: compare_sequence,
    tuple: compare_tuple,
    str: compare_text,
    Unicode: compare_text,
    GeneratorType: compare_generator,
    mock_call.__class__: compare_simple,
    unittest_mock_call.__class__: compare_simple,
    }

def register(type, comparer):
    """
    Register the supplied comparer for the specified type.
    This registration is global and will be in effect from the point
    this function is called until the end of the current process.
    """
    _registry[type] = comparer

def _mro(obj):
    class_ = getattr(obj, '__class__', None)
    if class_ is None:
        # must be an old-style class object in Python 2!
        return (obj, )
    mro = getattr(class_, '__mro__', None)
    if mro is None:
        # instance of old-style class in Python 2!
        return (class_, )
    return mro

def _shared_mro(x, y):
    y_mro = set(_mro(y))
    for class_ in _mro(x):
        if class_ in y_mro:
            yield class_

_unsafe_iterables = basestring, dict


class CompareContext(object):

    def __init__(self, expected_actual, options):
        self._expected_actual = expected_actual
        comparers = options.pop('comparers', None)
        if comparers:
            self.registry = dict(_registry)
            self.registry.update(comparers)
        else:
            self.registry = _registry
            
        self.recursive = options.pop('recursive', True)
        self.strict = options.pop('strict', False)
        self.options = options
        self.message = ''
        self.breadcrumbs = []

    def get_option(self, name, default=None):
        return self.options.get(name, default)

    def maybe_include(self, s):
        if self._expected_actual:
            return s
        return ''

    def _lookup(self, x, y):
        if self.strict and type(x) is not type(y):
            return compare_with_type
        
        for class_ in _shared_mro(x, y):
            comparer = self.registry.get(class_)
            if comparer:
                return comparer
            
        # fallback for iterables
        if ((isinstance(x, Iterable) and isinstance(y, Iterable)) and not
            (isinstance(x, _unsafe_iterables) or isinstance(y, _unsafe_iterables))):
            return compare_generator
        
        return compare_simple

    def _seperator(self):
        return '\n\nWhile comparing %s: ' % ''.join(self.breadcrumbs[1:])

    def different(self, x, y, breadcrumb):
        
        recursed = bool(self.breadcrumbs)
        self.breadcrumbs.append(breadcrumb)
        existing_message = self.message
        self.message = ''
        current_message = ''
        try:

            if not self.strict and x == y:
                return False
            
            comparer = self._lookup(x, y)

            result = comparer(x, y, self)
            specific_comparer = comparer is not compare_simple

            if self.strict:
                if type(x) is type(x) and x==y and not specific_comparer:
                    return False
            
            if result:
                
                if specific_comparer and recursed:
                    current_message = self._seperator()

                if specific_comparer or not recursed:
                    current_message += result

                    if self.recursive:
                        current_message += self.message

            return result
        
        finally:
            self.message = existing_message + current_message
            self.breadcrumbs.pop()
        

def compare(x=not_there, y=not_there, expected=not_there, actual=not_there, **kw):
    """
    Compare two supplied arguments and raise an
    :class:`AssertionError` if they are not the same.
    The :class:`AssertionError` raised will attempt to provide
    descriptions of the differences found.

    Using the expected and actual keyword arguments to indicate which is the
    expected and which is the actual value will make for more informative error
    messages. (You can also specify x as a positional argument together with
    either expected or actual as a keyword argument.)

    Any extra keywords parameters supplied will be passed to the functions
    that ends up doing the comparison. See the API documentation below
    for details of these.
    
    :param prefix: If provided, in the event of an :class:`AssertionError` being
                   raised, the prefix supplied will be prepended to the message
                   in the :class:`AssertionError`.
                   
    :param recursive: If ``True``, when a difference is found in a nested data
                      structure, attempt to highlight the location of the
                      difference. Defaults to ``True``.
                   
    :param strict: If ``True``, objects will only compare equal if
                   they are of the same type as well as being equal.
                   Defaults to ``False``.
                   
    :param comparers: If supplied, should be a dictionary mapping
                      types to comparer functions for those types. These will be
                      added to the global comparer registry for the duration
                      of this call.
    """
    prefix = kw.pop('prefix', None)
    (x, y, expected_actual) = _get_expected_actual(x, y, expected, actual)
    context = CompareContext(expected_actual, kw)

    if not context.different(x, y, not_there):
        return
    
    message = context.message
    if prefix:
        message = prefix + ': ' + message

    raise AssertionError(message)


def _get_expected_actual(x, y, expected, actual):
    """
    Helper method for compare() to work out if it is being invoked with unnamed
    positional arguments x and y, or if expected/actual kwargs have been
    specified allowing us to provide more helpful error messages.

    Returns a tuple (x, y, actual_expected) where actual_expected is a bool
    indicating if x and y are named the actual and expected values,
    respectively.

    not_there is a singleton value used as the default for all four arguments
    to compare() to differentiate them from an explicitly passed None value.

    Here are the possible inputs and corresponding outputs:
        (x=a, y=b, expected=not_there, actual=not_there) -> (a, b, False)
        (x=not_there, y=not_there, expected=a, actual=b) -> (a, b, True)
        (x=a, y=not_there, expected=a, actual=not_there) -> (b, a, True)
        (x=a, y=not_there, expected=not_there, actual=b) -> (a, b, True)
        Anything else -> ValueError
    """
    count = sum((0 if x is not_there else 1 for x in (x, y, expected, actual)))
    if count != 2:
        raise ValueError('Exactly 2 of the arguments (x, y, expected, actual) '
                         'must be specified.')

    if x is not_there and y is not not_there:
        raise ValueError('Must specify x and y together, '
                         'or x with one of expected/actual.')

    if expected is not_there and actual is not_there:
        return x, y, False
    if x is not_there and y is not_there:
        return expected, actual, True
    if actual is not_there:
        return expected, x, True
    return x, actual, True


class Comparison(object):
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
        if isinstance(object_or_type, basestring):
            container, method, name, c = resolve(object_or_type)
            if c is not_there:
                raise AttributeError('%r could not be resolved' % object_or_type)
        elif isinstance(object_or_type, (ClassType, type)):
            c = object_or_type
        elif isinstance(object_or_type, BaseException):
            c = object_or_type.__class__
            if attribute_dict is None:
                attribute_dict = vars(object_or_type)
                attribute_dict['args'] = object_or_type.args
        else:
            c = object_or_type.__class__
            if attribute_dict is None:
                attribute_dict=vars(object_or_type)
        self.c = c
        self.v = attribute_dict
        self.strict = strict

    def __eq__(self, other):
        if self.c is not other.__class__:
            self.failed = True
            return False
        if self.v is None:
            return True
        self.failed = {}
        if isinstance(other, BaseException):
            v = dict(vars(other))
            v['args'] = other.args
            if PY3 and '_not_found' in v:
                del v['_not_found']
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
                        v[k]=getattr(other, k)
                    except AttributeError:
                        pass
        
        e = set(self.v.keys())
        a = set(v.keys())
        for k in e.difference(a):
            try:
                # class attribute?
                v[k]= getattr(other, k)
            except AttributeError:
                self.failed[k] = '%s not in other' % repr(self.v[k])
            else:
                a.add(k)
        if self.strict:
            for k in a.difference(e):
                self.failed[k] = '%s not in Comparison' % repr(v[k])
        for k in e.intersection(a):
            ev = self.v[k]
            av = v[k]
            if ev != av:
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


class RoundComparison:
    """
    An object that can be used in comparisons of expected and actual
    numerics to a specified precision.

    :param value: numeric to be compared.

    :param precision: Number of decimal places to round to in order
                      to perform the comparison.
    """
    def __init__(self, value, precision):
        self.rounded = round(value, precision)
        self.precision = precision

    def __eq__(self, other):
        other_rounded = round(other, self.precision)
        if type(self.rounded) is not type(other_rounded):
            raise TypeError('Cannot compare %r with %r' % (self, type(other)))
        return self.rounded == other_rounded

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        return '<R:%s to %i digits>' % (self.rounded, self.precision)


def diff(x, y, x_label='', y_label=''):
    """
    A shorthand function that uses :mod:`difflib` to return a
    string representing the differences between the two string
    arguments.

    Most useful when comparing multi-line strings.
    """
    skip_lines = 0 if (x_label or y_label) else 2
    return '\n'.join(
        tuple(unified_diff(
            x.split('\n'),
            y.split('\n'),
            x_label,
            y_label,
            lineterm='')
              )[skip_lines:]
        )


