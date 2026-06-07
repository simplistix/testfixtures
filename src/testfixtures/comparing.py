from collections.abc import Iterable
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, time
from decimal import Decimal
from functools import partial as partial_type
from inspect import signature
from pathlib import Path
from types import GeneratorType
from typing import (
    Any,
    List,
    Callable,
    overload,
    Self,
    TypeAlias,
    Literal,
    Iterator,
)
from typing import _GenericAlias as GenericAlias  # type: ignore[attr-defined]
from unittest.mock import call as unittest_mock_call

from testfixtures import not_there, singleton
from testfixtures.mock import mock_call
from .comparers import *

# Some common types that are immutable, for optimisation purposes within CompareContext
IMMUTABLE_TYPEs = str, bytes, int, float, tuple, type(None)

# Container types whose `__eq__` delegates to their elements. When per-type
# ignore_eq is in play, we can't trust `x == y` on these because nested
# instances of an ignored type would silently leak through.
CONTAINER_TYPES = list, tuple, dict, set, frozenset

# Things that are iterable, but should not be treated as such.
UNSAFE_ITERABLES = str, bytes, dict, GenericAlias


Comparer = Callable[[Any, Any, 'CompareContext'], str | None]
Comparers: TypeAlias = dict[type, Comparer]


DEFAULT_COMPARERS: Comparers = {
    dict: compare_dict,
    set: compare_set,
    frozenset: compare_set,
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
}


@dataclass
class Registry:
    comparers: dict[type, Comparer]
    all_option_names: set[str]
    options_for: dict[Comparer, set[str]]
    ignore_eq_types: set[type]
    original: "Registry | None" = None

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
        if ((isinstance(x, Iterable) and isinstance(y, Iterable)) and not
            (isinstance(x, UNSAFE_ITERABLES) or
             isinstance(y, UNSAFE_ITERABLES))):
            return compare_generator

        return compare_object

    def __setitem__(self, key: type, value: Comparer) -> None:
        options = set(tuple(signature(value).parameters)[3:])
        self.options_for[value] = options
        self.all_option_names |= options
        self.comparers[key] = value

    @classmethod
    def initial(cls, comparers: Comparers | None = None) -> Self:
        registry = cls(
            comparers={},
            all_option_names = {'ignore_attributes'},
            options_for = {compare_object: {'ignore_attributes'}},
            ignore_eq_types = set(),
        )
        for name, value in (DEFAULT_COMPARERS if comparers is None else comparers).items():
            registry[name] = value
        return registry

    def copy(self) -> Self:
        return type(self)(
            comparers=self.comparers.copy(),
            all_option_names = self.all_option_names.copy(),
            options_for = self.options_for.copy(),
            ignore_eq_types = self.ignore_eq_types.copy(),
        )

    def overlay_with(self, comparers: Comparers) -> Self:
        registry = self.copy()
        for name, value in comparers.items():
            registry[name] = value
        return registry

    def install(self) -> Self:
        global _registry
        self.original = _registry
        _registry = self
        return self

    def uninstall(self) -> None:
        global _registry
        assert self.original is not None, "uninstall() called without install()"
        _registry = self.original
        del self.original

_registry = Registry.initial()


@contextmanager
def registry(comparers: Comparers | None = None) -> Iterator[Registry]:
    _registry = Registry.initial(comparers)
    _registry.install()
    try:
        yield _registry
    finally:
        _registry.uninstall()


@overload
def register(type_: type, comparer: Comparer) -> None: ...
@overload
def register(type_: type, comparer: Comparer, *, ignore_eq: bool) -> None: ...
@overload
def register(type_: type, *, ignore_eq: Literal[True]) -> None: ...


def register(
    type_: type,
    comparer: Comparer | None = None,
    *,
    ignore_eq: bool = False,
) -> None:
    """
    Register the supplied comparer for the specified type, and/or mark the
    type as one whose ``__eq__`` should be ignored during comparison.

    At least one of ``comparer`` or ``ignore_eq=True`` must be supplied.

    This registration is global and will be in effect from the point
    this function is called until the end of the current process.
    """
    if comparer is None and not ignore_eq:
        raise TypeError(
            "register() requires either a comparer or ignore_eq=True"
        )
    if comparer is not None:
        _registry[type_] = comparer
    if ignore_eq:
        _registry.ignore_eq_types.add(type_)


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
            ignore_eq: bool | type | Iterable[type] = False,
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
        self.ignore_eq_all: bool = False
        self.ignore_eq_types: set[type] = set(self._registry.ignore_eq_types)
        if ignore_eq is True:
            self.ignore_eq_all = True
        elif ignore_eq is False:
            pass
        elif isinstance(ignore_eq, type):
            self.ignore_eq_types.add(ignore_eq)
        else:
            self.ignore_eq_types.update(ignore_eq)
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

    def label(self, side: Literal["x", "y"], value: Any) -> str:
        """
        Generate a labelled representation of the value for one side of a comparison.
        """
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

    def qualified_equals(self, x: Any, y: Any) -> bool:
        """
        Determines if two objects are equal, taking ``strict``, ``ignore_eq`` and instances
        of :class:`~testfixtures.comparers.AlreadySeen` into account.
        """
        pair = x, y
        # When either side is an AlreadySeen wrapper for the other (same
        # underlying id), it's the same object we already handled —
        # equal by identity. Skipping __eq__ here keeps that guarantee
        # when __eq__ is broken, strict about unknown operands, or being
        # bypassed via ignore_eq.
        if any(type(o) is AlreadySeen for o in pair):
            a, b = (o.id if type(o) is AlreadySeen else id(o) for o in pair)
            if a == b:
                return True
        # AlreadySeen.__eq__ delegates to the wrapped object, so let
        # normal equality run when the wrapper is on the right.
        if type(y) is AlreadySeen:
            return x == y
        if self.strict or self.ignore_eq_all:
            return False
        # Containers delegate __eq__ to their elements, so when any
        # ignored type is in play we must block container == as well.
        types = self.ignore_eq_types
        if types and any(
            isinstance(o, CONTAINER_TYPES) or not types.isdisjoint(type(o).__mro__)
            for o in pair
        ):
            return False
        return x == y

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
        """
        Comparers can call this method to :ref:`hand off <custom-comparer-different>`
        comparison of elements within the objects they are currently comparing.
        """

        x = self._break_loops(x, breadcrumb)
        y = self._break_loops(y, breadcrumb)

        recursed = bool(self.breadcrumbs)
        self.breadcrumbs.append(breadcrumb)
        existing_message = self.message
        self.message = ''
        current_message = ''
        try:

            try:
                if self.qualified_equals(x, y):
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
    value = source() if callable(source) else source
    try:
        return str(value)
    except Exception:
        return safe_repr(value)


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
        ignore_eq: bool | type | Iterable[type] = False,
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

    :param ignore_eq: Controls when ``__eq__`` is skipped in favour of a
                      registered comparer (or the hash-equality fallback):

                      * ``True`` — skip ``__eq__`` for *every* object.
                      * ``False`` (default) — honour ``__eq__`` except for
                        types registered with ``ignore_eq=True``.
                      * a type — also skip ``__eq__`` whenever an instance of
                        that type is on either side of a comparison.
                      * an iterable of types — as above, for each type.

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


try:
    from django.db.models import Model
    from .django import compare_model
except ImportError:
    pass
else:
    register(Model, compare_model, ignore_eq=True)


try:
    from pandas import DataFrame as PandasDataFrame
    from .pandas import compare_dataframe as compare_pandas_dataframe
except ImportError:
    pass
else:
    register(PandasDataFrame, compare_pandas_dataframe, ignore_eq=True)


try:
    from polars import DataFrame as PolarsDataFrame
    from .polars import compare_dataframe as compare_polars_dataframe
except ImportError:
    pass
else:
    register(PolarsDataFrame, compare_polars_dataframe, ignore_eq=True)


try:
    from numpy import ndarray
    from numpy.ma import MaskedArray
    from .numpy import compare_masked_array, compare_ndarray
except ImportError:
    pass
else:
    register(ndarray, compare_ndarray, ignore_eq=True)
    register(MaskedArray, compare_masked_array, ignore_eq=True)
