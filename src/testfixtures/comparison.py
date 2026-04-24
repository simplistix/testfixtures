import re
from collections import OrderedDict
from collections.abc import Iterable as IterableABC
from dataclasses import dataclass
from datetime import datetime, time
from decimal import Decimal
from functools import partial as partial_type, reduce
from inspect import signature
from operator import __or__
from pathlib import Path
from pprint import pformat
from types import GeneratorType, NotImplementedType
from typing import (
    Any,
    Sequence,
    TypeVar,
    List,
    Mapping,
    Callable,
    Iterable,
    cast,
    overload,
    Self,
    TypeAlias,
)
from typing import _GenericAlias as GenericAlias  # type: ignore[attr-defined]

from unittest.mock import call as unittest_mock_call

from testfixtures import not_there, singleton
from testfixtures.mock import mock_call
from testfixtures.resolve import resolve
from testfixtures.utils import indent

from .comparers import *
from .comparers import _compare_mapping, _extract_attrs

# Some common types that are immutable, for optimisation purposes within CompareContext
IMMUTABLE_TYPEs = str, bytes, int, float, tuple, type(None)


Comparer = Callable[[Any, Any, 'CompareContext'], str | None]
Comparers: TypeAlias = dict[type, Comparer]

_UNSAFE_ITERABLES = str, bytes, dict, GenericAlias


@dataclass
class Registry:
    comparers: dict[type, Comparer]
    all_option_names: set[str]
    options_for: dict[Comparer, set[str]]

    @staticmethod
    def _shared_mro(x: Any, y: Any) -> Iterable[type]:
        y_mro = set(type(y).__mro__)
        for class_ in type(x).__mro__:
            if class_ in y_mro:
                yield class_

    def lookup(self, x: Any, y: Any, strict: bool) -> Comparer:
        if strict and type(x) is not type(y):
            return compare_with_type

        for class_ in self._shared_mro(x, y):
            comparer = self.comparers.get(class_)
            if comparer:
                return comparer

        # fallback for iterables
        if ((isinstance(x, IterableABC) and isinstance(y, IterableABC)) and not
            (isinstance(x, _UNSAFE_ITERABLES) or
             isinstance(y, _UNSAFE_ITERABLES))):
            return compare_generator

        # special handling for Comparisons:
        if isinstance(x, Comparison) or isinstance(y, Comparison):
            return compare_simple

        return compare_object

    def __setitem__(self, key: type, value: Comparer) -> None:
        options = set(tuple(signature(value).parameters)[3:])
        self.options_for[value] = options
        self.all_option_names |= options
        self.comparers[key] = value

    @classmethod
    def initial(cls, comparers: Comparers) -> Self:
        registry = cls(
            comparers={},
            all_option_names = {'ignore_attributes'},
            options_for = {compare_object: {'ignore_attributes'}}
        )
        for name, value in comparers.items():
            registry[name] = value
        return registry

    def copy(self) -> Self:
        return type(self)(
            comparers=self.comparers.copy(),
            all_option_names = self.all_option_names.copy(),
            options_for = self.options_for.copy()
        )

    def overlay_with(self, comparers: Comparers) -> Self:
        registry = self.copy()
        for name, value in comparers.items():
            registry[name] = value
        return registry


_registry = Registry.initial({
    dict: compare_dict,
    set: compare_set,
    list: compare_sequence,
    tuple: compare_tuple,
    str: compare_text,
    bytes: compare_bytes,
    int: compare_simple,
    float: compare_simple,
    Decimal: compare_simple,
    GeneratorType: compare_generator,
    mock_call.__class__: compare_call,
    unittest_mock_call.__class__: compare_call,
    BaseException: compare_exception,
    BaseExceptionGroup: compare_exception_group,
    partial_type: compare_partial,
    Path: compare_path,
    datetime: compare_with_fold,
    time: compare_with_fold,
})


def register(type_: type, comparer: Comparer) -> None:
    """
    Register the supplied comparer for the specified type.
    This registration is global and will be in effect from the point
    this function is called until the end of the current process.
    """
    _registry[type_] = comparer


class CompareContext:
    """
    Stores the context of the current comparison in process during a call to
    :func:`testfixtures.compare`.
    """

    def __init__(
            self,
            x_label: str | None,
            y_label: str | None,
            recursive: bool = True,
            strict: bool = False,
            ignore_eq: bool = False,
            comparers: Comparers | None = None,
            options: dict[str, Any] | None = None,
    ):
        self._registry = _registry.overlay_with(comparers) if comparers else _registry
        if options:
            invalid = set(options) - self._registry.all_option_names
            if invalid:
                raise TypeError(
                    'The following options are not valid: ' + ', '.join(invalid)
                )
        self.x_label = x_label
        self.y_label = y_label
        self.recursive: bool = recursive
        self.strict: bool = strict
        self.ignore_eq: bool = ignore_eq
        self.options: dict[str, Any] = options or {}
        self.message: str = ''
        self.breadcrumbs: List[str] = []
        self._seen: dict[int, str] = {}

    def extract_args(self, args: tuple, x: Any, y: Any, expected: Any, actual: Any) -> List:

        possible = list[Any]()

        def append_if_specified(source: Any) -> None:
            if source is not unspecified:
                possible.append(source)

        append_if_specified(expected)
        possible.extend(args)
        append_if_specified(actual)
        append_if_specified(x)
        append_if_specified(y)

        if len(possible) != 2:
            message = 'Exactly two objects needed, you supplied:'
            if possible:
                message += ' {}'.format(possible)
            raise TypeError(message)

        return possible

    def label(self, side: str, value: Any) -> str:
        r = str(value)
        label = getattr(self, side+'_label')
        if label:
            r += ' ('+label+')'
        return r

    def _separator(self) -> str:
        return '\n\nWhile comparing %s: ' % ''.join(self.breadcrumbs[1:])

    def _break_loops(self, obj: Any, breadcrumb: str) -> Any:
        # Don't bother with this process for simple, immutable types:
        if isinstance(obj, IMMUTABLE_TYPEs):
            return obj

        id_ = id(obj)
        breadcrumb_ = self._seen.get(id_)
        if breadcrumb_ is not None:
            return AlreadySeen(id_, obj, breadcrumb_)
        else:
            self._seen[id_] = breadcrumb
            return obj

    def simple_equals(self, x: Any, y: Any) -> bool:
        return not (self.strict or self.ignore_eq) and x == y

    def call(self, comparer: Comparer, x: Any, y: Any) -> str | None:
        kw = {}
        option_names = self._registry.options_for.get(comparer)
        if option_names:
            for name in option_names:
                value = self.options.get(name, not_there)
                if value is not not_there:
                    kw[name] = value
        return comparer(x, y, self, **kw)

    def different(self, x: Any, y: Any, breadcrumb: str) -> bool | str | None:

        x = self._break_loops(x, breadcrumb)
        y = self._break_loops(y, breadcrumb)

        recursed = bool(self.breadcrumbs)
        self.breadcrumbs.append(breadcrumb)
        existing_message = self.message
        self.message = ''
        current_message = ''
        try:

            if type(y) is AlreadySeen or not (self.strict or self.ignore_eq):
                try:
                    if x == y:
                        return False
                except RecursionError:
                    pass

            comparer: Comparer = self._registry.lookup(x, y, self.strict)

            result = self.call(comparer, x, y)
            specific_comparer = comparer is not compare_simple

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


def _resolve_lazy(source: Any) -> str:
    return str(source() if callable(source) else source)


unspecified = singleton('unspecified')


def compare(
        *args: Any,
        x: Any = unspecified,
        y: Any = unspecified,
        expected: Any = unspecified,
        actual: Any = unspecified,
        prefix: str | Callable[[], str] | None = None,
        suffix: str | Callable[[], str] | None = None,
        x_label: str | None = None,
        y_label: str | None = None,
        raises: bool = True,
        recursive: bool = True,
        strict: bool = False,
        ignore_eq: bool = False,
        comparers: Comparers | None = None,
        **options: Any
) -> str | None:
    """
    Compare two objects, raising an :class:`AssertionError` if they are not
    the same. The :class:`AssertionError` raised will attempt to provide
    descriptions of the differences found.

    The two objects to compare can be passed either positionally or using
    explicit keyword arguments named ``x`` and ``y``, or ``expected`` and
    ``actual``, or a mixture of these.

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

    Any other keyword parameters supplied will be passed to the functions
    that end up doing the comparison. See the
    :mod:`API documentation below <testfixtures.comparison>`
    for details of these.
    """

    __tracebackhide__ = True

    if not (expected is unspecified and actual is unspecified):
        x_label = x_label or 'expected'
        y_label = y_label or 'actual'

    context = CompareContext(x_label, y_label, recursive, strict, ignore_eq, comparers, options)
    x, y = context.extract_args(args, x, y, expected, actual)
    if not context.different(x, y, ''):
        return None

    message = context.message
    if prefix:
        message = _resolve_lazy(prefix) + ': ' + message
    if suffix:
        message += '\n' + _resolve_lazy(suffix)

    if raises:
        raise AssertionError(message)
    return message


class StatefulComparison:
    """
    A base class for stateful comparison objects.
    """

    failed: str | None = ''
    expected: Any = None
    name_attrs: Sequence[str] = ()

    def __eq__(self, other: Any) -> bool:
        return not(self != other)

    def name(self) -> str:
        name = type(self).__name__
        if self.name_attrs:
            name += '(%s)' % ', '.join('%s=%r' % (n, getattr(self, n)) for n in self.name_attrs)
        return name

    def body(self) -> str:
        return pformat(self.expected)[1:-1]

    def __repr__(self) -> str:
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

    """

    def __init__(self,
                 object_or_type: Any,
                 attribute_dict: dict[str, Any] | None = None,
                 partial: bool = False,
                 **attributes: Any):
        self.partial = partial
        if attributes:
            if attribute_dict is None:
                attribute_dict = attributes
            else:
                attribute_dict.update(attributes)
        if isinstance(object_or_type, str):
            c = resolve(object_or_type).found
            if c is not_there:
                raise AttributeError(
                    '%r could not be resolved' % object_or_type
                )
        elif isinstance(object_or_type, type):
            c = object_or_type
        else:
            c = object_or_type.__class__
            if attribute_dict is None:
                attribute_dict = _extract_attrs(object_or_type)
        self.expected_type = c
        self.expected_attributes = attribute_dict

    def __ne__(self, other: Any) -> bool:

        if isinstance(other, AlreadySeen):
            other = other.obj

        other_type = type(other)
        if self.expected_type is not other_type:
            self.failed = f'wrong type: {other_type.__module__}.{other_type.__qualname__}'
            return True

        if self.expected_attributes is None:
            return False

        attribute_names = set(self.expected_attributes.keys())
        actual_attributes: dict[str, Any]
        if self.partial:
            actual_attributes = {}
        else:
            actual_attributes = cast(dict[str, Any], _extract_attrs(other))
            attribute_names -= set(actual_attributes)

        for name in attribute_names:
            try:
                actual_attributes[name] = getattr(other, name)
            except AttributeError:
                pass

        context = CompareContext(x_label='Comparison', y_label='actual')
        self.failed = _compare_mapping(self.expected_attributes,
                                       actual_attributes,
                                       context,
                                       obj_for_class=not_there,
                                       prefix='attributes ',
                                       breadcrumb='.%s',
                                       check_y_not_x=not self.partial)
        return bool(self.failed)

    def name(self) -> str:
        name = 'C:'
        module = getattr(self.expected_type, '__module__', None)
        if module:
            name = name + module + '.'
        name += (getattr(self.expected_type, '__name__', None) or repr(self.expected_type))
        return name

    def body(self) -> str:
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
      If ``True``, then the items are expected to be in the order specified.
      If ``False``, they may be in any order.
      Defaults to ``True``.
    :param partial:
      If ``True``, then any keys not expected will be ignored.
      Defaults to ``False``.
    :param recursive:
      If a difference is found, recursively compare the item where
      the difference was found to highlight exactly what was different.
      Defaults to ``False``.
    """

    name_attrs: Sequence[str] = ('ordered', 'partial')

    def __init__(
            self,
            *expected: Any,
            ordered: bool = True,
            partial: bool = False,
            recursive: bool = False,
    ):
        self.expected = expected
        self.ordered = ordered
        self.partial = partial
        self.recursive = recursive
        self.checked_indices = set[int]()

    def __ne__(self, other: Any) -> bool:
        actual: list[Any]
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
            missing_from_expected = []
        else:
            actual_indices += missing_from_expected_indices
            ignored = None

        message = []

        def add_section(name: str, content: Any) -> None:
            if content:
                message.append(name+':\n'+pformat(content))

        add_section('ignored', ignored)

        if self.ordered:
            message.append(cast(str, compare(
                expected=[self.expected[i] for i in sorted(expected_indices)],
                actual=[original_actual[i] for i in sorted(actual_indices)],
                recursive=self.recursive,
                raises=False
            )).split('\n\n', 1)[1])
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

    def __init__(self, *expected: Any) -> None:
        super(Subset, self).__init__(*expected, ordered=False, partial=True)


class Permutation(SequenceComparison):
    """
    A shortcut for :class:`SequenceComparison` that checks if the set of items
    in the sequence is as expected, but without checking ordering.
    """

    def __init__(self, *expected: Any) -> None:
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
      If ``True``, then the keys in the mapping are expected to be in the order specified.
      Defaults to ``False``.
    :param partial:
      If ``True``, then any keys not expected will be ignored.
      Defaults to ``False``.
    :param recursive:
      If a difference is found, recursively compare the value where
      the difference was found to highlight exactly what was different.
      Defaults to ``False``.
    """

    name_attrs = ('ordered', 'partial')

    def __init__(
            self,
            *expected_mapping: tuple[Any, Any] | Mapping[Any, Any],
            ordered: bool = False,
            partial: bool = False,
            recursive: bool = False,
            **expected_items: Any,
    ):
        self.ordered = ordered
        self.partial = partial
        self.recursive = recursive

        if len(expected_mapping) == 1:
            expected = OrderedDict(*expected_mapping)
        else:
            expected = OrderedDict(expected_mapping)  # type: ignore[arg-type]
        expected.update(expected_items)

        self.expected = expected

    def body(self) -> str:
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

    def __ne__(self, other: Any) -> bool:
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
                         any :class:`str` instance.

    :param flags: Flags passed to :func:`re.compile`.

    :param flag_names: See the :ref:`examples <stringcomparison>`.
    """
    def __init__(self, regex_source: str, flags: int | None = None, **flag_names: str):
        args: list[Any] = [regex_source]

        flags_ = []
        if flags:
            flags_.append(flags)
        flags_.extend(getattr(re, f.upper()) for f in flag_names)
        if flags_:
            args.append(reduce(__or__, flags_))

        self.re = re.compile(*args)

    def __eq__(self, other: Any) -> bool | NotImplementedType:
        if not isinstance(other, str):
            return NotImplemented
        return self.re.match(other) is not None

    def __repr__(self) -> str:
        return '<S:%s>' % self.re.pattern

    def __lt__(self, other: Any) -> bool:
        return self.re.pattern < other

    def __gt__(self, other: Any) -> bool:
        return self.re.pattern > other


class RoundComparison:
    """
    An object that can be used in comparisons of expected and actual
    numerics to a specified precision.

    :param value: numeric to be compared.

    :param precision: Number of decimal places to round to in order
                      to perform the comparison.
    """
    def __init__(self, value: float, precision: int):
        self.rounded = round(value, precision)
        self.precision = precision

    def __eq__(self, other: Any) -> bool:
        other_rounded = round(other, self.precision)
        if type(self.rounded) is not type(other_rounded):
            raise TypeError('Cannot compare %r with %r' % (self, type(other)))
        return self.rounded == other_rounded

    def __ne__(self, other: Any) -> bool:
        return not self == other

    def __repr__(self) -> str:
        return '<R:%s to %i digits>' % (self.rounded, self.precision)


class RangeComparison:
    """
    An object that can be used in comparisons of orderable types to
    check that a value specified within the given range.

    :param lower_bound: the inclusive lower bound for the acceptable range.

    :param upper_bound: the inclusive upper bound for the acceptable range.
    """
    def __init__(self, lower_bound: Any, upper_bound: Any) -> None:
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound

    def __eq__(self, other: Any) -> bool:
        return self.lower_bound <= other <= self.upper_bound

    def __ne__(self, other: Any) -> bool:
        return not self == other

    def __repr__(self) -> str:
        return '<Range: [%s, %s]>' % (self.lower_bound, self.upper_bound)

T = TypeVar('T')

def like(t: type[T], **attributes: Any) -> T:
    """
    Create a type-safe partial comparison for use in strictly typed code.

    This is a convenience function that creates a :class:`Comparison` with
    ``partial=True`` but is typed to return the type being compared, making it
    compatible with strict type checkers like mypy.

    :param t: The type to compare against.
    :param attributes: Keyword arguments specifying the attributes to check.
    :return: A :class:`Comparison` object typed as the input type.
    """
    return Comparison(t, attribute_dict=attributes, partial=True)  # type: ignore[return-value]


S = TypeVar("S", bound=Sequence[Any])
S_ = TypeVar("S_", bound=Sequence[Any])


@overload
def sequence(
    partial: bool = False,
    ordered: bool = True,
    recursive: bool = True,
) -> Callable[[S], S]: ...


@overload
def sequence(
    partial: bool = False,
    ordered: bool = True,
    recursive: bool = True,
    *,
    returns: type[S_],
) -> Callable[[S], S_]: ...


def sequence(
    partial: bool = False,
    ordered: bool = True,
    recursive: bool = True,
    *,
    returns: type[S_] | None = None,
) -> Callable[[S], S | S_]:
    """
    Create a type-safe sequence comparison with configurable partial matching
    and ordering requirements.

    This function returns a callable that wraps a sequence in a comparison object,
    making it compatible with strict type checkers.

    :param partial: If ``True``, only items in the expected sequence need to be present
                    in the actual sequence. Defaults to ``False``.
    :param ordered: If ``True``, items must appear in the same order. Defaults to ``True``.
    :param recursive: If ``True``, provide detailed recursive comparison when differences
                      are found. Defaults to ``True``.
    :param returns: Optional type hint for the return type, used to satisfy type checkers
                    when the comparison needs to appear as a different sequence type.
    :return: A callable that takes a sequence and returns a comparison object typed
             as a sequence.
    """
    def maker(items: S) -> S | S_:
        return SequenceComparison(  # type: ignore[return-value]
            *items, partial=partial, ordered=ordered, recursive=recursive
        )

    return maker


@overload
def contains(
    items: S,
) -> S: ...


@overload
def contains(
    items: S,
    *,
    returns: type[S_],
) -> S_: ...


def contains(
    items: S,
    *,
    returns: type[S_] | None = None,
) -> S | S_:
    """
    Create a type-safe partial sequence comparison that ignores order.

    Checks that the specified items are present in the actual sequence, regardless
    of their order or what other items are present. This is useful when you only
    care that certain elements exist in a collection.

    :param items: The sequence of items that must be present.
    :param returns: Optional type hint for the return type, used to satisfy type checkers
                    when the comparison needs to appear as a different sequence type.
    :return: A comparison object typed as a sequence.
    """
    return SequenceComparison(  # type: ignore[return-value]
        *items, ordered=False, partial=True, recursive=True
    )


@overload
def unordered(
    items: S,
) -> S: ...


@overload
def unordered(
    items: S,
    *,
    returns: type[S_],
) -> S_: ...


def unordered(
    items: S,
    *,
    returns: type[S_] | None = None,
) -> S | S_:
    """
    Create a type-safe sequence comparison that ignores order but requires all
    items to match.

    Checks that the actual sequence contains exactly the same items as specified,
    but in any order. This is useful when order doesn't matter but you want to
    ensure no extra or missing items.

    :param items: The sequence of items that must match exactly.
    :param returns: Optional type hint for the return type, used to satisfy type checkers
                    when the comparison needs to appear as a different sequence type.
    :return: A comparison object typed as a sequence.
    """
    return SequenceComparison(  # type: ignore[return-value]
        *items, ordered=False, partial=False, recursive=True
    )
