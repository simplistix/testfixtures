import re
from collections import defaultdict
from datetime import datetime
from difflib import unified_diff
from functools import partial as partial_type
from pathlib import Path
from pprint import pformat
from typing import (
    Any,
    Iterable,
    List,
    Mapping,
    Pattern,
    Sequence,
    TypeVar,
    TYPE_CHECKING,
)

from testfixtures import not_there
from testfixtures.mock import parent_name, _Call

if TYPE_CHECKING:
    from .comparison import CompareContext


def safe_repr(obj: Any) -> str:
    """
    A fault-tolerant version of :func:`repr`.

    :exc:`KeyboardInterrupt` and :exc:`SystemExit` are not caught.
    """
    try:
        return repr(obj)
    except Exception as e:
        type_ = type(obj)
        type_name = type_.__name__
        match obj:
            case list():
                return '[' + ', '.join(safe_repr(e) for e in obj) + ']'
            case tuple():
                body = ', '.join(safe_repr(e) for e in obj)
                suffix = ',)' if len(obj) == 1 else ')'
                return '(' + body + suffix
            case dict():
                body = ', '.join(f'{safe_repr(k)}: {safe_repr(v)}' for k, v in obj.items())
                return '{' + body + '}'
            case frozenset():
                if not obj:
                    return type_name
                return type_name + '({' + ', '.join(safe_repr(e) for e in obj) + '})'
            case set():
                if not obj:
                    return type_name + '()'
                return '{' + ', '.join(safe_repr(e) for e in obj) + '}'
            case _:
                try:
                    detail = f'{type(e).__name__}: {e}'
                except:
                    detail = type(e).__name__
                return f'<unrepresentable {type_.__module__}.{type_.__qualname__}: {detail}>'


def safe_pformat(obj: Any) -> str:
    """
    A fault-tolerant version of  :func:`pprint.pformat` but tolerant.
    Falls back to :func:`safe_repr` when :func:`~pprint.pformat` fails.
    """
    try:
        return pformat(obj)
    except:
        return safe_repr(obj)


class AlreadySeen:
    """
    A marker for an object that has already been seen during a :func:`~testfixtures.compare` call.
    These are used to prevent infinite recursion during comparison.
    """

    def __init__(self, id_: int, obj: Any, breadcrumb: str) -> None:
        self.id = id_
        self.obj = obj
        self.breadcrumb = breadcrumb

    def __repr__(self) -> str:
        return f'<AlreadySeen for {safe_repr(self.obj)} at {self.breadcrumb} with id {self.id}>'

    def __eq__(self, other: Any)-> bool:
        if isinstance(other, AlreadySeen):
            return self.breadcrumb == other.breadcrumb
        else:
            return self.obj == other


def diff(x: str, y: str, x_label: str | None = '', y_label: str | None = '') -> str:
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


def compare_simple(
        x: Any, y: Any, context: 'CompareContext', newline_threshold: int = 15
) -> str | None:
    """
    Returns a very simple textual difference between the two supplied objects.
    """
    if x != y:
        repr_x = safe_repr(x)
        repr_y = safe_repr(y)
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
            x_label = context.x_label or 'x'
            y_label = context.y_label or 'y'
            return f'Both {x_label} and {y_label} appear as {repr_x!r}, but are not equal!'
        labeled_x = context.label('x', repr_x)
        labeled_y = context.label('y', repr_y)
        if len(repr_x) > newline_threshold or len(repr_y) > newline_threshold:
            return f'not equal:\n{labeled_x}\n{labeled_y}'
        else:
            return f'{labeled_x} != {labeled_y}'
    return None


def _extract_attrs(obj: Any, ignore: Iterable[str] | None = None) -> dict[str, Any] | None:
    try:
        attrs = vars(obj).copy()
    except TypeError:
        attrs = None
    else:
        if isinstance(obj, BaseException):
            attrs['args'] = obj.args

    has_slots = getattr(obj, '__slots__', not_there) is not not_there
    if has_slots:
        slots = set[str]()
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


def merge_ignored_attributes(
    *ignored: Iterable[str] | Mapping[type, Iterable[str]] | str | None
) -> Mapping[type, set[str]]:
    """
    Merge multiple specifications of attributes to ignore into a single mapping.

    This is particularly useful when implementing custom comparers that need to
    combine their own attribute ignores with those passed via the context.

    Each argument can be:

    - ``None``: ignored
    - A :class:`~typing.Mapping` of type to iterable of attribute names:
      attributes for specific types
    - An iterable of attribute names: applies to all types
    - A single attribute name string: applies to all types

    Returns a mapping of types to sets of attribute names to ignore, where
    :data:`~typing.Any` is used as the key for attributes that apply to all types.
    """
    final = defaultdict[type, set[str]](set)
    for i in ignored:
        if i is None:
            pass
        elif isinstance(i, Mapping):
            for type_, values in i.items():
                final[type_].update(values)
        else:
            final[Any].update(i)
    return final


def _attrs_to_ignore(
        ignore_attributes: Iterable[str] | Mapping[type, Iterable[str]], obj: Any
) -> set[str]:
    ignored = set()
    if isinstance(ignore_attributes, dict):
        ignored |= set(ignore_attributes.get(type(obj), ()))
        ignored |= set(ignore_attributes.get(Any, ()))
    else:
        ignored.update(ignore_attributes)
    return ignored


def compare_object(
        x: object,
        y: object,
        context: 'CompareContext',
        ignore_attributes: Iterable[str] | Mapping[type, Iterable[str]] = ()
) -> str | None:
    """
    Compare the two supplied objects based on their type and attributes.

    :param ignore_attributes:

       Either a sequence of strings containing attribute names to be ignored
       when comparing, or a :class:`~typing.Mapping` of type to sequence of
       strings containing attribute names to be ignored when comparing that type.

       When specified as a mapping, you can use :data:`~typing.Any` as a key to
       specify attributes that should be ignored for all types.

    """
    if type(x) is not type(y) or isinstance(x, type):
        return compare_simple(x, y, context)
    x_attrs = _extract_attrs(x, _attrs_to_ignore(ignore_attributes, x))
    y_attrs = _extract_attrs(y, _attrs_to_ignore(ignore_attributes, y))
    if x_attrs is None or y_attrs is None or not (x_attrs and y_attrs):
        return compare_simple(x, y, context)
    if not context.simple_equals(x_attrs, y_attrs):
        return _compare_mapping(x_attrs, y_attrs, context, x,
                                'attributes ', '.%s')
    return None


def compare_exception(
        x: BaseException, y: BaseException, context: 'CompareContext'
) -> str | None:
    """
    Compare the two supplied exceptions based on their message, type and
    attributes.
    """
    if x.args != y.args:
        return compare_simple(x, y, context)
    return context.call(compare_object, x, y)


def compare_with_type(x: Any, y: Any, context: 'CompareContext') -> str:
    """
    Return a textual description of the difference between two objects
    including information about their types.
    """
    if type(x) is AlreadySeen and type(x.obj) is type(y) and x.obj == y:
        return ''
    source = locals()
    to_render = {}
    for name in 'x', 'y':
        obj = source[name]
        to_render[name] = context.label(
            name,
            '{0} ({1!r})'.format(_short_repr(obj), type(obj))
        )
    return '{x} != {y}'.format(**to_render)


def compare_sequence(
        x: Sequence, y: Sequence, context: 'CompareContext', prefix: bool = True
) -> str | None:
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
        return None

    header = 'sequence not as expected:\n\n' if prefix else ''
    same = safe_pformat(x[:i])
    x_label = context.x_label or 'first'
    y_label = context.y_label or 'second'
    return (
        f'{header}same:\n{same}\n\n'
        f'{x_label}:\n{safe_pformat(x[i:])}\n\n'
        f'{y_label}:\n{safe_pformat(y[i:])}'
    )


def compare_generator(x: Iterable, y: Iterable, context: 'CompareContext') -> str | None:
    """
    Returns a textual description of the differences between the two
    supplied generators.

    This is done by first unwinding each of the generators supplied
    into tuples and then passing those tuples to
    :func:`compare_sequence`.
    """
    x = tuple(x)
    y = tuple(y)

    if context.simple_equals(x, y):
        return None

    return compare_sequence(x, y, context)


def compare_tuple(x: tuple, y: tuple, context: 'CompareContext') -> str | None:
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


def compare_dict(x: dict, y: dict, context: 'CompareContext') -> str | None:
    """
    Returns a textual description of the differences between the two
    supplied dictionaries.
    """
    return _compare_mapping(x, y, context, x)


Item = TypeVar('Item')


def sorted_by_repr(sequence: Iterable[Item]) -> List[Item]:
    return sorted(sequence, key=safe_repr)


def _compare_mapping(
        x: Mapping, y: Mapping, context: 'CompareContext', obj_for_class: Any,
        prefix: str = '', breadcrumb: str = '[%r]',
        check_y_not_x: bool = True
) -> str | None:

    x_keys = set(x.keys())
    y_keys = set(y.keys())
    x_not_y = x_keys - y_keys
    y_not_x = y_keys - x_keys
    same = []
    diffs = []
    for key in sorted_by_repr(x_keys.intersection(y_keys)):
        if context.different(x[key], y[key], breadcrumb % (key, )):
            labelled_x = context.label('x', safe_pformat(x[key]))
            labelled_y = context.label('y', safe_pformat(y[key]))
            diffs.append(f'{safe_repr(key)}: {labelled_x} != {labelled_y}')
        else:
            same.append(key)

    if not (x_not_y or (check_y_not_x and y_not_x) or diffs):
        return None

    if obj_for_class is not_there:
        lines = []
    else:
        lines = [f'{obj_for_class.__class__.__name__} not as expected:']

    if same:
        try:
            same = sorted(same)
        except TypeError:
            pass
        lines.extend(('', f'{prefix}same:', safe_repr(same)))

    x_label = context.x_label or 'first'
    y_label = context.y_label or 'second'

    if x_not_y:
        lines.extend(('', f'{prefix}in {x_label} but not {y_label}:'))
        for key in sorted_by_repr(x_not_y):
            lines.append(f'{safe_repr(key)}: {safe_pformat(x[key])}')
    if y_not_x:
        lines.extend(('', f'{prefix}in {y_label} but not {x_label}:'))
        for key in sorted_by_repr(y_not_x):
            lines.append(f'{safe_repr(key)}: {safe_pformat(y[key])}')
    if diffs:
        lines.extend(('', f"{prefix or 'values '}differ:"))
        lines.extend(diffs)
    return '\n'.join(lines)


def compare_set(x: set, y: set, context: 'CompareContext') -> str | None:
    """
    Returns a textual description of the differences between the two
    supplied sets.
    """
    x_not_y = x - y
    y_not_x = y - x
    if not (y_not_x or x_not_y):
        return None
    lines = [f'{x.__class__.__name__} not as expected:', '']
    x_label = context.x_label or 'first'
    y_label = context.y_label or 'second'
    if x_not_y:
        lines.extend((
            f'in {x_label} but not {y_label}:',
            safe_pformat(sorted_by_repr(x_not_y)),
            '',
            ))
    if y_not_x:
        lines.extend((
            f'in {y_label} but not {x_label}:',
            safe_pformat(sorted_by_repr(y_not_x)),
            '',
            ))
    return '\n'.join(lines)+'\n'


trailing_whitespace_re: Pattern = re.compile(r'\s+$', re.MULTILINE)


def strip_blank_lines(text: str) -> str:
    result = []
    for line in text.split('\n'):
        if line and not line.isspace():
            result.append(line)
    return '\n'.join(result)


def split_repr(text: str) -> str:
    parts = text.split('\n')
    for i, part in enumerate(parts[:-1]):
        parts[i] = repr(part + '\n')
    parts[-1] = repr(parts[-1])
    return '\n'.join(parts)


def compare_text(
        x: str,
        y: str,
        context: 'CompareContext',
        blanklines: bool = True,
        trailing_whitespace: bool = True,
        show_whitespace: bool = False,
) -> str | None:
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
    if not trailing_whitespace:
        x = trailing_whitespace_re.sub('', x)
        y = trailing_whitespace_re.sub('', y)
    if not blanklines:
        x = strip_blank_lines(x)
        y = strip_blank_lines(y)
    if x == y:
        return None
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


def compare_bytes(x: bytes, y: bytes, context: 'CompareContext') -> str | None:
    if x == y:
        return None
    labelled_x = context.label('x', repr(x))
    labelled_y = context.label('y', repr(y))
    return '\n%s\n!=\n%s' % (labelled_x, labelled_y)


def compare_call(x: _Call, y: _Call, context: 'CompareContext') -> str | None:
    if x == y:
        return None

    def extract(call: _Call) -> tuple[str, tuple[Any], dict[str, Any]]:
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
        return None

    return 'mock.call not as expected:'


def compare_partial(x: partial_type, y: partial_type, context: 'CompareContext') -> str | None:
    x_attrs = dict(func=x.func, args=x.args, keywords=x.keywords)
    y_attrs = dict(func=y.func, args=y.args, keywords=y.keywords)
    if x_attrs != y_attrs:
        return _compare_mapping(x_attrs, y_attrs, context, x,
                                'attributes ', '.%s')
    return None


def compare_path(x: Path, y: Path, context: 'CompareContext') -> str | None:
    return compare_text(str(x), str(y), context)


def compare_with_fold(x: datetime, y: datetime, context: 'CompareContext') -> str | None:
    if not (x == y and x.fold == y.fold):
        repr_x = repr(x)
        repr_y = repr(y)
        if repr_x == repr_y:
            repr_x += f' (fold={x.fold})'
            repr_y += f' (fold={y.fold})'
        return context.label('x', repr_x)+' != '+context.label('y', repr_y)
    return None


def _short_repr(obj: Any) -> str:
    repr_ = safe_repr(obj)
    if len(repr_) > 30:
        repr_ = repr_[:30] + '...'
    return repr_


def compare_exception_group(
    x: BaseExceptionGroup, y: BaseExceptionGroup, context: 'CompareContext'
) -> str | None:
    """
    Compare the two supplied exception groups
    """

    x_msg, x_excs = x.args
    y_msg, y_excs = y.args
    msg_different = context.different(x_msg, y_msg, 'msg')
    excs_different = context.different(x_excs, y_excs, 'excs')
    if msg_different or excs_different:
        return 'exception group not as expected:'
    return None
