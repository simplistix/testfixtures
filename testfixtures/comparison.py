from collections import OrderedDict
from decimal import Decimal
from difflib import unified_diff
from functools import partial as partial_type, partial, reduce
from operator import __or__
from pprint import pformat
from types import GeneratorType
import re

from testfixtures import not_there
from testfixtures.compat import ClassType, Iterable, Unicode, basestring, PY3, PY2
from testfixtures.resolve import resolve
from testfixtures.utils import indent
from testfixtures.mock import parent_name, mock_call, unittest_mock_call


def diff(x, y, x_label='', y_label=''):
    """
    A shorthand function that uses :mod:`difflib` to return a
    string representing the differences between the two string
    arguments.

    Most useful when comparing multi-line strings.
    """
    return '\n'.join(
        unified_diff(
            x.split('\n'),
            y.split('\n'),
            x_label or 'first',
            y_label or 'second',
            lineterm='')
    )


def compare_simple(x, y, context):
    """
    Returns a very simple textual difference between the two supplied objects.
    """
    if x != y:
        repr_x = repr(x)
        repr_y = repr(y)
        if repr_x == repr_y:
            if type(x) is not type(y):
                return compare_with_type(x, y, context)
            x_attrs = _extract_attrs(x)
            y_attrs = _extract_attrs(y)
            diff_ = None
            if not (x_attrs is None or y_attrs is None):
                diff_ = _compare_mapping(x_attrs, y_attrs, context, x,
                                         'attributes ', '.%s')
            if diff_:
                return diff_
            return 'Both %s and %s appear as %r, but are not equal!' % (
                context.x_label or 'x', context.y_label or 'y', repr_x
            )
        return context.label('x', repr_x) + ' != ' + context.label('y', repr_y)


def _extract_attrs(obj, ignore=None):
    try:
        attrs = vars(obj).copy()
    except TypeError:
        attrs = None
    else:
        if isinstance(obj, BaseException):
            attrs['args'] = obj.args

    has_slots = getattr(obj, '__slots__', not_there) is not not_there
    if has_slots:
        slots = set()
        for cls in type(obj).__mro__:
            slots.update(getattr(cls, '__slots__', ()))
        if slots and attrs is None:
            attrs = {}
        for n in slots:
            value = getattr(obj, n, not_there)
            if value is not not_there:
                attrs[n] = value

    if attrs is None:
        return None

    if ignore is not None:
        for attr in ignore:
            attrs.pop(attr, None)
    return attrs


def _attrs_to_ignore(context, ignore_attributes, obj):
    ignore = context.get_option('ignore_attributes', ())
    if isinstance(ignore, dict):
        ignore = ignore.get(type(obj), ())
    ignore = set(ignore)
    ignore.update(ignore_attributes)
    return ignore


def compare_object(x, y, context, ignore_attributes=()):
    """
    Compare the two supplied objects based on their type and attributes.

    :param ignore_attributes:

       Either a sequence of strings containing attribute names to be ignored
       when comparing or a mapping of type to sequence of strings containing
       attribute names to be ignored when comparing that type.

       This may be specified as either a parameter to this function or in the
       ``context``. If specified in both, they will both apply with precedence
       given to whatever is specified is specified as a parameter.
       If specified as a parameter to this fucntion, it may only be a list of
       strings.
    """
    if type(x) is not type(y) or isinstance(x, (ClassType, type)):
        return compare_simple(x, y, context)
    x_attrs = _extract_attrs(x, _attrs_to_ignore(context, ignore_attributes, x))
    y_attrs = _extract_attrs(y, _attrs_to_ignore(context, ignore_attributes, y))
    if x_attrs is None or y_attrs is None or not (x_attrs and y_attrs):
        return compare_simple(x, y, context)
    if context.ignore_eq or x_attrs != y_attrs:
        return _compare_mapping(x_attrs, y_attrs, context, x,
                                'attributes ', '.%s')


def compare_exception(x, y, context):
    """
    Compare the two supplied exceptions based on their message, type and
    attributes.
    """
    if x.args != y.args:
        return compare_simple(x, y, context)
    return compare_object(x, y, context)


def compare_with_type(x, y, context):
    """
    Return a textual description of the difference between two objects
    including information about their types.
    """
    source = locals()
    to_render = {}
    for name in 'x', 'y':
        obj = source[name]
        to_render[name] = context.label(
            name,
            '{0} ({1!r})'.format(_short_repr(obj), type(obj))
        )
    return '{x} != {y}'.format(**to_render)


def compare_sequence(x, y, context, prefix=True):
    """
    Returns a textual description of the differences between the two
    supplied sequences.
    """
    l_x = len(x)
    l_y = len(y)
    i = 0
    while i < l_x and i < l_y:
        if context.different(x[i], y[i], '[%i]' % i):
            break
        i += 1

    if l_x == l_y and i == l_x:
        return

    return (('sequence not as expected:\n\n' if prefix else '')+
            'same:\n%s\n\n'
            '%s:\n%s\n\n'
            '%s:\n%s') % (pformat(x[:i]),
                          context.x_label or 'first', pformat(x[i:]),
                          context.y_label or 'second', pformat(y[i:]),
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

    if not context.ignore_eq and x == y:
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


def sorted_by_repr(sequence):
    return sorted(sequence, key=lambda o: repr(o))


def _compare_mapping(x, y, context, obj_for_class,
                     prefix='', breadcrumb='[%r]',
                     check_y_not_x=True):

    x_keys = set(x.keys())
    y_keys = set(y.keys())
    x_not_y = x_keys - y_keys
    y_not_x = y_keys - x_keys
    same = []
    diffs = []
    for key in sorted_by_repr(x_keys.intersection(y_keys)):
        if context.different(x[key], y[key], breadcrumb % (key, )):
            diffs.append('%r: %s != %s' % (
                key,
                context.label('x', pformat(x[key])),
                context.label('y', pformat(y[key])),
                ))
        else:
            same.append(key)

    if not (x_not_y or (check_y_not_x and y_not_x) or diffs):
        return

    if obj_for_class is not_there:
        lines = []
    else:
        lines = ['%s not as expected:' % obj_for_class.__class__.__name__]

    if same:
        try:
            same = sorted(same)
        except TypeError:
            pass
        lines.extend(('', '%ssame:' % prefix, repr(same)))

    x_label = context.x_label or 'first'
    y_label = context.y_label or 'second'

    if x_not_y:
        lines.extend(('', '%sin %s but not %s:' % (prefix, x_label, y_label)))
        for key in sorted_by_repr(x_not_y):
            lines.append('%r: %s' % (
                key,
                pformat(x[key])
                ))
    if y_not_x:
        lines.extend(('', '%sin %s but not %s:' % (prefix, y_label, x_label)))
        for key in sorted_by_repr(y_not_x):
            lines.append('%r: %s' % (
                key,
                pformat(y[key])
                ))
    if diffs:
        lines.extend(('', '%sdiffer:' % (prefix or 'values ')))
        lines.extend(diffs)
    return '\n'.join(lines)


def compare_set(x, y, context):
    """
    Returns a textual description of the differences between the two
    supplied sets.
    """
    x_not_y = x - y
    y_not_x = y - x
    if not (y_not_x or x_not_y):
        return
    lines = ['%s not as expected:' % x.__class__.__name__, '']
    x_label = context.x_label or 'first'
    y_label = context.y_label or 'second'
    if x_not_y:
        lines.extend((
            'in %s but not %s:' % (x_label, y_label),
            pformat(sorted_by_repr(x_not_y)),
            '',
            ))
    if y_not_x:
        lines.extend((
            'in %s but not %s:' % (y_label, x_label),
            pformat(sorted_by_repr(y_not_x)),
            '',
            ))
    return '\n'.join(lines)+'\n'


trailing_whitespace_re = re.compile(r'\s+$', re.MULTILINE)


def strip_blank_lines(text):
    result = []
    for line in text.split('\n'):
        if line and not line.isspace():
            result.append(line)
    return '\n'.join(result)


def split_repr(text):
    parts = text.split('\n')
    for i, part in enumerate(parts[:-1]):
        parts[i] = repr(part + '\n')
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
    if x == y:
        return
    labelled_x = context.label('x', repr(x))
    labelled_y = context.label('y', repr(y))
    if len(x) > 10 or len(y) > 10:
        if '\n' in x or '\n' in y:
            if show_whitespace:
                x = split_repr(x)
                y = split_repr(y)
            message = '\n' + diff(x, y, context.x_label, context.y_label)
        else:
            message = '\n%s\n!=\n%s' % (labelled_x, labelled_y)
    else:
        message = labelled_x+' != '+labelled_y
    return message


def compare_bytes(x, y, context):
    if x == y:
        return
    labelled_x = context.label('x', repr(x))
    labelled_y = context.label('y', repr(y))
    return '\n%s\n!=\n%s' % (labelled_x, labelled_y)


def compare_call(x, y, context):
    if x == y:
        return

    def extract(call):
        try:
            name, args, kwargs = call
        except ValueError:
            name = None
            args, kwargs = call
        return name, args, kwargs

    x_name, x_args, x_kw = extract(x)
    y_name, y_args, y_kw = extract(y)

    if x_name == y_name and x_args == y_args and x_kw == y_kw:
        return compare_call(getattr(x, parent_name), getattr(y, parent_name), context)

    if repr(x) != repr(y):
        return compare_text(repr(x), repr(y), context)

    different = (
        context.different(x_name, y_name, ' function name') or
        context.different(x_args, y_args, ' args') or
        context.different(x_kw, y_kw, ' kw')
    )
    if not different:
        return

    return 'mock.call not as expected:'



def compare_partial(x, y, context):
    x_attrs = dict(func=x.func, args=x.args, keywords=x.keywords)
    y_attrs = dict(func=y.func, args=y.args, keywords=y.keywords)
    if x_attrs != y_attrs:
        return _compare_mapping(x_attrs, y_attrs, context, x,
                                'attributes ', '.%s')


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
    int: compare_simple,
    float: compare_simple,
    Decimal: compare_simple,
    GeneratorType: compare_generator,
    mock_call.__class__: compare_call,
    unittest_mock_call.__class__: compare_call,
    BaseException: compare_exception,
    partial_type: compare_partial,
    }

if PY3:
    _registry[bytes] = compare_bytes


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

    x_label = y_label = None

    def __init__(self, options):
        self.registries = []
        comparers = options.pop('comparers', None)
        if comparers:
            self.registries.append(comparers)
        self.registries.append(_registry)

        self.recursive = options.pop('recursive', True)
        self.strict = options.pop('strict', False)
        self.ignore_eq = options.pop('ignore_eq', False)

        if 'expected' in options or 'actual' in options:
            self.x_label = 'expected'
            self.y_label = 'actual'
        self.x_label = options.pop('x_label', self.x_label)
        self.y_label = options.pop('y_label', self.y_label)

        self.options = options
        self.message = ''
        self.breadcrumbs = []
        self._seen = set()

    def extract_args(self, args):

        possible = []
        expected = self.options.pop('expected', not_there)
        if expected is not not_there:
            possible.append(expected)
        possible.extend(args)
        actual = self.options.pop('actual', not_there)
        if actual is not not_there:
            possible.append(actual)

        x = self.options.pop('x', not_there)
        if x is not not_there:
            possible.append(x)
        y = self.options.pop('y', not_there)
        if y is not not_there:
            possible.append(y)

        if len(possible) != 2:
            message = 'Exactly two objects needed, you supplied:'
            if possible:
                message += ' {}'.format(possible)
            if self.options:
                message += ' {}'.format(self.options)
            raise TypeError(message)

        return possible

    def get_option(self, name, default=None):
        return self.options.get(name, default)

    def label(self, side, value):
        r = str(value)
        label = getattr(self, side+'_label')
        if label:
            r += ' ('+label+')'
        return r

    def _lookup(self, x, y):
        if self.strict and type(x) is not type(y):
            return compare_with_type

        for class_ in _shared_mro(x, y):
            for registry in self.registries:
                comparer = registry.get(class_)
                if comparer:
                    return comparer

        # fallback for iterables
        if ((isinstance(x, Iterable) and isinstance(y, Iterable)) and not
            (isinstance(x, _unsafe_iterables) or
             isinstance(y, _unsafe_iterables))):
            return compare_generator

        # special handling for Comparisons:
        if isinstance(x, Comparison) or isinstance(y, Comparison):
            return compare_simple

        return compare_object

    def _separator(self):
        return '\n\nWhile comparing %s: ' % ''.join(self.breadcrumbs[1:])

    def seen(self, x, y):
        # don't get confused by interning:
        singleton_types = basestring, int, float
        if isinstance(x, singleton_types) and isinstance(y, singleton_types):
            return False
        key = id(x), id(y)
        if key in self._seen:
            return True
        self._seen.add(key)

    def different(self, x, y, breadcrumb):

        if self.seen(x, y):
            # a self-referential hierarchy; so lets say this one is
            # equal and hope the first time we saw it covers things...
            return False

        recursed = bool(self.breadcrumbs)
        self.breadcrumbs.append(breadcrumb)
        existing_message = self.message
        self.message = ''
        current_message = ''
        try:

            if not (self.strict or self.ignore_eq) and x == y:
                return False

            comparer = self._lookup(x, y)

            result = comparer(x, y, self)
            specific_comparer = comparer is not compare_simple

            if self.strict:
                if x == y and not specific_comparer:
                    return False

            if result:

                if specific_comparer and recursed:
                    current_message = self._separator()

                if specific_comparer or not recursed:
                    current_message += result

                    if self.recursive:
                        current_message += self.message

            return result

        finally:
            self.message = existing_message + current_message
            self.breadcrumbs.pop()


def _resolve_lazy(source):
    return str(source() if callable(source) else source)


def compare(*args, **kw):
    """
    Compare two objects, raising an :class:`AssertionError` if they are not
    the same. The :class:`AssertionError` raised will attempt to provide
    descriptions of the differences found.

    The two objects to compare can be passed either positionally or using
    explicit keyword arguments named ``x`` and ``y``, or ``expected`` and
    ``actual``.

    Any other keyword parameters supplied will be passed to the functions
    that end up doing the comparison. See the
    :mod:`API documentation below <testfixtures.comparison>`
    for details of these.

    :param prefix: If provided, in the event of an :class:`AssertionError`
                   being raised, the prefix supplied will be prepended to the
                   message in the :class:`AssertionError`. This may be a
                   callable, in which case it will only be resolved if needed.

    :param suffix: If provided, in the event of an :class:`AssertionError`
                   being raised, the suffix supplied will be appended to the
                   message in the :class:`AssertionError`. This may be a
                   callable, in which case it will only be resolved if needed.

    :param x_label: If provided, in the event of an :class:`AssertionError`
                    being raised, the object passed as the first positional
                    argument, or ``x`` keyword argument, will be labelled
                    with this string in the message in the
                    :class:`AssertionError`.

    :param y_label: If provided, in the event of an :class:`AssertionError`
                    being raised, the object passed as the second positional
                    argument, or ``y`` keyword argument, will be labelled
                    with this string in the message in the
                    :class:`AssertionError`.

    :param raises: If ``False``, the message that would be raised in the
                   :class:`AssertionError` will be returned instead of the
                   exception being raised.

    :param recursive: If ``True``, when a difference is found in a
                      nested data structure, attempt to highlight the location
                      of the difference.

    :param strict: If ``True``, objects will only compare equal if they are
                   of the same type as well as being equal.

    :param ignore_eq: If ``True``, object equality, which relies on ``__eq__``
                      being correctly implemented, will not be used.
                      Instead, comparers will be looked up and used
                      and, if no suitable comparer is found, objects will
                      be considered equal if their hash is equal.

    :param comparers: If supplied, should be a dictionary mapping
                      types to comparer functions for those types. These will
                      be added to the comparer registry for the duration
                      of this call.
    """

    __tracebackhide__ = True

    prefix = kw.pop('prefix', None)
    suffix = kw.pop('suffix', None)
    raises = kw.pop('raises', True)
    context = CompareContext(kw)

    x, y = context.extract_args(args)

    if not context.different(x, y, not_there):
        return

    message = context.message
    if prefix:
        message = _resolve_lazy(prefix) + ': ' + message
    if suffix:
        message += '\n' + _resolve_lazy(suffix)

    if raises:
        raise AssertionError(message)
    return message


class StatefulComparison(object):
    """
    A base class for stateful comparison objects.
    """

    failed = ''
    expected = None
    name_attrs = ()

    def __eq__(self, other):
        return not(self != other)

    def name(self):
        name = type(self).__name__
        if self.name_attrs:
            name += '(%s)' % ', '.join('%s=%r' % (n, getattr(self, n)) for n in self.name_attrs)
        return name

    def body(self):
        return pformat(self.expected)[1:-1]

    def __repr__(self):
        name = self.name()
        body = self.failed or self.body()
        prefix = '<%s%s>' % (name, self.failed and '(failed)' or '')
        if '\n' in body:
            return '\n'+prefix+'\n'+body.strip('\n')+'\n'+'</%s>' % name
        elif body:
            return prefix + body + '</>'
        return prefix


class Comparison(StatefulComparison):
    """
    These are used when you need to compare an object's type, a subset of its attributes
    or make equality checks with objects that do not natively support comparison.

    :param object_or_type: The object or class from which to create the
                           :class:`Comparison`.

    :param attribute_dict: An optional dictionary containing attributes
                           to place on the :class:`Comparison`.

    :param partial:
      If true, only the specified attributes will be checked and any extra attributes
      of the object being compared with will be ignored.

    :param attributes: Any other keyword parameters passed will placed
                       as attributes on the :class:`Comparison`.

    :param strict:

      .. deprecated:: 6.16.0

        Use ``partial`` instead.
    """

    def __init__(self,
                 object_or_type,
                 attribute_dict=None,
                 partial=False,
                 **attributes):
        self.partial = partial or not attributes.pop('strict', True)
        if attributes:
            if attribute_dict is None:
                attribute_dict = attributes
            else:
                attribute_dict.update(attributes)
        if isinstance(object_or_type, basestring):
            container, method, name, c = resolve(object_or_type)
            if c is not_there:
                raise AttributeError(
                    '%r could not be resolved' % object_or_type
                )
        elif isinstance(object_or_type, (ClassType, type)):
            c = object_or_type
        else:
            c = object_or_type.__class__
            if attribute_dict is None:
                attribute_dict = _extract_attrs(object_or_type)
        self.expected_type = c
        self.expected_attributes = attribute_dict

    def __ne__(self, other):
        # .__class__ is important for Py2 compatibility.
        if self.expected_type is not other.__class__:
            self.failed = 'wrong type'
            return True

        if self.expected_attributes is None:
            return False

        attribute_names = set(self.expected_attributes.keys())
        if self.partial:
            actual_attributes = {}
        else:
            actual_attributes = _extract_attrs(other)
            attribute_names -= set(actual_attributes)

        for name in attribute_names:
            try:
                actual_attributes[name] = getattr(other, name)
            except AttributeError:
                pass

        kw = {'x_label': 'Comparison', 'y_label': 'actual'}
        context = CompareContext(kw)
        self.failed = _compare_mapping(self.expected_attributes,
                                       actual_attributes,
                                       context,
                                       obj_for_class=not_there,
                                       prefix='attributes ',
                                       breadcrumb='.%s',
                                       check_y_not_x=not self.partial)
        return bool(self.failed)

    def name(self):
        name = 'C:'
        module = getattr(self.expected_type, '__module__', None)
        if module:
            name = name + module + '.'
        name += (getattr(self.expected_type, '__name__', None) or repr(self.expected_type))
        return name

    def body(self):
        if self.expected_attributes:
            # if we're not failed, show what we will expect:
            lines = []
            for k, v in sorted(self.expected_attributes.items()):
                rv = repr(v)
                if '\n' in rv:
                    rv = indent(rv)
                lines.append('%s: %s' % (k, rv))
            return '\n'.join(lines)
        return ''


class SequenceComparison(StatefulComparison):
    """
    An object that can be used in comparisons of expected and actual
    sequences.

    :param expected: The items expected to be in the sequence.
    :param ordered:
      If the items are expected to be in the order specified.
      Defaults to ``True``.
    :param partial:
      If any items not expected should be ignored.
      Defaults to ``False``.
    :param recursive:
      If a difference is found, recursively compare the item where
      the difference was found to highlight exactly what was different.
      Defaults to ``False``.
    """

    name_attrs = ('ordered', 'partial')

    def __init__(self, *expected, **kw):
        self.expected = expected
        # py2 :-(
        self.ordered = kw.pop('ordered', True)
        self.partial = kw.pop('partial', False)
        self.recursive = kw.pop('recursive', False)
        assert not kw, 'unexpected parameter'
        self.checked_indices = set()

    def __ne__(self, other):
        try:
            actual = original_actual = list(other)
        except TypeError:
            self.failed = 'bad type'
            return True
        expected = list(self.expected)
        actual = list(actual)

        matched = []
        matched_expected_indices = []
        matched_actual_indices = []

        missing_from_expected = actual
        missing_from_expected_indices = actual_indices = list(range(len(actual)))

        missing_from_actual = []
        missing_from_actual_indices = []

        start = 0
        for e_i, e in enumerate(expected):
            try:
                i = actual.index(e, start)
                a_i = actual_indices.pop(i)
            except ValueError:
                missing_from_actual.append(e)
                missing_from_actual_indices.append(e_i)
            else:
                matched.append(missing_from_expected.pop(i))
                matched_expected_indices.append(e_i)
                matched_actual_indices.append(a_i)
                self.checked_indices.add(a_i)
                if self.ordered:
                    start = i

        matches_in_order = matched_actual_indices == sorted(matched_actual_indices)
        all_matched = not (missing_from_actual or missing_from_expected)
        partial_match = self.partial and not missing_from_actual

        if (matches_in_order or not self.ordered) and (all_matched or partial_match):
            return False

        expected_indices = matched_expected_indices+missing_from_actual_indices
        actual_indices = matched_actual_indices

        if self.partial:
            # try to give a clue as to what didn't match:
            if self.recursive and self.ordered and missing_from_expected:
                actual_indices.append(missing_from_expected_indices.pop(0))
                missing_from_expected.pop(0)

            ignored = missing_from_expected
            missing_from_expected = None
        else:
            actual_indices += missing_from_expected_indices
            ignored = None

        message = []

        def add_section(name, content):
            if content:
                message.append(name+':\n'+pformat(content))

        add_section('ignored', ignored)

        if self.ordered:
            message.append(compare(
                expected=[self.expected[i] for i in sorted(expected_indices)],
                actual=[original_actual[i] for i in sorted(actual_indices)],
                recursive=self.recursive,
                raises=False
            ).split('\n\n', 1)[1])
        else:
            add_section('same', matched)
            add_section('in expected but not actual', missing_from_actual)
            add_section('in actual but not expected', missing_from_expected)

        self.failed = '\n\n'.join(message)
        return True


class Subset(SequenceComparison):
    """
    A shortcut for :class:`SequenceComparison` that checks if the
    specified items are present in the sequence.
    """

    name_attrs = ()

    def __init__(self, *expected):
        super(Subset, self).__init__(*expected, ordered=False, partial=True)


class Permutation(SequenceComparison):
    """
    A shortcut for :class:`SequenceComparison` that checks if the set of items
    in the sequence is as expected, but without checking ordering.
    """

    def __init__(self, *expected):
        super(Permutation, self).__init__(*expected, ordered=False, partial=False)


class MappingComparison(StatefulComparison):
    """
    An object that can be used in comparisons of expected and actual
    mappings.

    :param expected_mapping:
      The mapping that should be matched expressed as either a sequence of
      ``(key, value)`` tuples or a mapping.
    :param expected_items: The items that should be matched.
    :param ordered:
      If the keys in the mapping are expected to be in the order specified.
      Defaults to ``False``.
    :param partial:
      If any keys not expected should be ignored.
      Defaults to ``False``.
    :param recursive:
      If a difference is found, recursively compare the value where
      the difference was found to highlight exactly what was different.
      Defaults to ``False``.
    """

    name_attrs = ('ordered', 'partial')

    def __init__(self, *expected_mapping, **expected_items):
        # py2 :-(
        self.ordered = expected_items.pop('ordered', False)
        self.partial = expected_items.pop('partial', False)
        self.recursive = expected_items.pop('recursive', False)

        if PY2 and self.ordered:
            if expected_items:
                raise TypeError('order undefined on Python 2')
            elif expected_mapping and type(expected_mapping[0]) is dict:
                raise TypeError('dict order undefined on Python 2')

        if len(expected_mapping) == 1:
            expected = OrderedDict(*expected_mapping)
        else:
            expected = OrderedDict(expected_mapping)
        expected.update(expected_items)

        self.expected = expected

    def body(self):
        # this can all go away and use the super class once py2 is gone :'(
        parts = []
        text_length = 0
        for key, value in self.expected.items():
            part = repr(key)+': '+pformat(value)
            text_length += len(part)
            parts.append(part)
        if text_length > 60:
            sep = ',\n'
        else:
            sep = ', '
        return sep.join(parts)

    def __ne__(self, other):
        try:
            actual_keys = other.keys()
            actual_mapping = dict(other.items())
        except AttributeError:
            self.failed = 'bad type'
            return True

        expected_keys = self.expected.keys()
        expected_mapping = self.expected

        if self.partial:
            ignored_keys = set(actual_keys) - set(expected_keys)
            for key in ignored_keys:
                del actual_mapping[key]
            # preserve the order:
            actual_keys = [k for k in actual_keys if k not in ignored_keys]
        else:
            ignored_keys = None

        mapping_differences = compare(
            expected=expected_mapping,
            actual=actual_mapping,
            recursive=self.recursive,
            raises=False
        )

        if self.ordered:
            key_differences = compare(
                expected=list(expected_keys),
                actual=list(actual_keys),
                recursive=self.recursive,
                raises=False
            )
        else:
            key_differences = None

        if key_differences or mapping_differences:

            message = []

            if ignored_keys:
                message.append('ignored:\n'+pformat(sorted(ignored_keys)))

            if mapping_differences:
                message.append(mapping_differences.split('\n\n', 1)[1])

            if key_differences:
                message.append('wrong key order:\n\n'+key_differences.split('\n\n', 1)[1])

            self.failed = '\n\n'.join(message)

            return True
        return False


class StringComparison:
    """
    An object that can be used in comparisons of expected and actual
    strings where the string expected matches a pattern rather than a
    specific concrete string.

    :param regex_source: A string containing the source for a regular
                         expression that will be used whenever this
                         :class:`StringComparison` is compared with
                         any :class:`basestring` instance.

    :param flags: Flags passed to :func:`re.compile`.

    :param flag_names: See the :ref:`examples <stringcomparison>`.
    """
    def __init__(self, regex_source, flags=None, **flag_names):
        args = [regex_source]

        flags_ = []
        if flags:
            flags_.append(flags)
        flags_.extend(getattr(re, f.upper()) for f in flag_names)
        if flags_:
            args.append(reduce(__or__, flags_))

        self.re = re.compile(*args)

    def __eq__(self, other):
        if not isinstance(other, basestring):
            return
        if self.re.match(other):
            return True
        return False

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        return '<S:%s>' % self.re.pattern

    def __lt__(self, other):
        return self.re.pattern < other

    def __gt__(self, other):
        return self.re.pattern > other


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


class RangeComparison:
    """
    An object that can be used in comparisons of orderable types to
    check that a value specified within the given range.

    :param lower_bound: the inclusive lower bound for the acceptable range.

    :param upper_bound: the inclusive upper bound for the acceptable range.
    """
    def __init__(self, lower_bound, upper_bound):
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound

    def __eq__(self, other):
        return self.lower_bound <= other <= self.upper_bound

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        return '<Range: [%s, %s]>' % (self.lower_bound, self.upper_bound)
