import re
from collections import OrderedDict
from functools import reduce
from operator import __or__
from pprint import pformat
from types import NotImplementedType
from typing import (
    Any,
    Sequence,
    TypeVar,
    Mapping,
    Callable,
    cast,
    overload,
)
from typing import _GenericAlias as GenericAlias  # type: ignore[attr-defined]

from testfixtures import not_there, safe_pformat
from testfixtures.comparers import (
    _extract_attrs, AlreadySeen, _compare_mapping, safe_repr, compare_simple
)
from testfixtures.comparing import CompareContext, compare, register
from testfixtures.resolve import resolve
from testfixtures.utils import indent


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
        return safe_pformat(self.expected)[1:-1]

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
                rv = safe_repr(v)
                if '\n' in rv:
                    rv = indent(rv)
                lines.append(f'{k}: {rv}')
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
            part = f'{safe_repr(key)}: {safe_pformat(value)}'
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
                         any :class:`str` instance, or an already compiled
                         :class:`re.Pattern`.

    :param flags: Flags passed to :func:`re.compile`.

    :param flag_names: See the :ref:`examples <stringcomparison>`.
    """

    @overload
    def __init__(self, regex_source: re.Pattern[str]): ...

    @overload
    def __init__(self, regex_source: str, flags: int | None = None, **flag_names: bool): ...

    def __init__(
        self,
        regex_source: str | re.Pattern[str],
        flags: int | None = None,
        **flag_names: bool,
    ):
        if isinstance(regex_source, re.Pattern):
            self.re = regex_source
            return

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


class ReprComparison:
    """
    An object that can be used in comparisons to check that an object is both
    of an expected type and has an expected :func:`repr`.

    :param type_: the type the compared object must be an instance of.

    :param repr_: the :func:`repr` the compared object must have exactly.

    :param match: a regular expression, as either a :class:`str` or a compiled
                  :class:`re.Pattern`, that the compared object's :func:`repr`
                  must match. Mutually exclusive with ``repr_``.
    """
    @overload
    def __init__(self, type_: type, repr_: str): ...
    @overload
    def __init__(self, type_: type, *, match: str | re.Pattern[str]): ...

    def __init__(
        self,
        type_: type,
        repr_: str | None = None,
        *,
        match: str | re.Pattern[str] | None = None,
    ):
        if (repr_ is None) == (match is None):
            raise TypeError('provide either repr_ or match')
        self.type = type_
        self.repr = repr_
        self.match = match

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, self.type):
            return False
        if self.match is not None:
            return re.search(self.match, repr(other)) is not None
        return repr(other) == self.repr

    def __ne__(self, other: Any) -> bool:
        return not self == other

    def __repr__(self) -> str:
        module = getattr(self.type, '__module__', None)
        name = (module + '.' if module else '') + (
            getattr(self.type, '__name__', None) or repr(self.type)
        )
        detail = self.repr if self.repr is not None else f'match={self.match!r}'
        return f'<ReprComparison: {name}: {detail}>'


T = TypeVar('T')

@overload
def like(t: str | re.Pattern[str]) -> str: ...


@overload
def like(t: type[T], **attributes: Any) -> T: ...


def like(t: type[T] | str | re.Pattern[str], **attributes: Any) -> T | str:
    """
    Create a type-safe partial comparison for use in strictly typed code.

    This is a convenience function that creates a :class:`Comparison` with
    ``partial=True`` but is typed to return the type being compared, making it
    compatible with strict type checkers like mypy.

    If passed a :class:`str` pattern or a compiled :class:`re.Pattern`, a
    :class:`StringComparison` typed as a :class:`str` is returned instead.

    :param t: The type to compare against, or a regular expression pattern.
    :param attributes: Keyword arguments specifying the attributes to check.
    :return: A :class:`Comparison` typed as the input type, or a
             :class:`StringComparison` typed as a :class:`str`.
    """
    if isinstance(t, (str, re.Pattern)):
        return cast(str, StringComparison(t))
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


M = TypeVar("M", bound=Mapping[Any, Any])
M_ = TypeVar("M_", bound=Mapping[Any, Any])


@overload
def mapping(
    partial: bool = False,
    ordered: bool = False,
    recursive: bool = True,
) -> Callable[[M], M]: ...


@overload
def mapping(
    partial: bool = False,
    ordered: bool = False,
    recursive: bool = True,
    *,
    returns: type[M_],
) -> Callable[[M], M_]: ...


def mapping(
    partial: bool = False,
    ordered: bool = False,
    recursive: bool = True,
    *,
    returns: type[M_] | None = None,
) -> Callable[[M], M | M_]:
    """
    Create a type-safe mapping comparison with configurable key ordering and
    partial matching.

    This is the mapping equivalent of :func:`sequence`. It returns a callable
    that wraps a mapping in a :class:`MappingComparison`, typed to match the
    mapping being compared so that strict type checkers stay happy.

    :param partial: If ``True``, any keys not expected are ignored.
                    Defaults to ``False``.
    :param ordered: If ``True``, the keys must appear in the order given.
                    Defaults to ``False``.
    :param recursive: If ``True``, provide detailed recursive comparison when
                      differences are found. Defaults to ``True``.
    :param returns: Optional type hint for the return type, used to satisfy type
                    checkers when the comparison needs to appear as a different
                    mapping type.
    :return: A callable that takes a mapping and returns a comparison object
             typed as a mapping.
    """
    def maker(items: M) -> M | M_:
        return MappingComparison(  # type: ignore[return-value]
            items, ordered=ordered, partial=partial, recursive=recursive
        )

    return maker


register(StatefulComparison, compare_simple)
