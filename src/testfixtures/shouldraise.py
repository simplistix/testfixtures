import re
from contextlib import contextmanager
from functools import wraps
from types import TracebackType
from typing import Callable, TypeAlias, Iterator, Self, ParamSpec, TypeVar, Generic, cast, overload

from testfixtures import diff, compare, not_there, singleton
from .comparers import split_repr


param_docs = """

    :param exception: This can be one of the following:

                      * Not passed, indicating that an exception must be
                        raised, but the type is unimportant.

                      * ``None``, indicating that no exception should be raised.
                        This is useful for parameterised tests where the parameter
                        may be either an exception or ``None``.

                      * An exception class, indicating that the type
                        of the exception is important but not the
                        parameters it is created with.

                      * An exception instance, indicating that an
                        exception exactly matching the one supplied
                        should be raised.

    :param unless: Can be passed a boolean that, when ``True`` indicates that
                   no exception is expected. This is useful when checking
                   that exceptions are only raised on certain versions of
                   Python.
"""


class NoException(AssertionError):
    """
    A marker class indicating no exception has been raised.

    .. currentmodule:: testfixtures

    :attr:`ShouldRaise.raised` is set to an instance of this class unless an
    exception has otherwise been seen.
    """

    def __init__(self) -> None:
        super().__init__('No exception raised!')


E = TypeVar("E", bound=BaseException)


class ShouldRaise(Generic[E]):
    __doc__ = """
    This context manager is used to assert that an exception is raised
    within the context it is managing.
    """ + param_docs

    #: The exception captured by the context manager.
    #: Can be used to inspect specific attributes of the exception.
    raised: E = NoException()  # type: ignore[assignment]
    exception: E | type[E] | None
    expected: bool
    match: str | re.Pattern[str] | None

    @overload
    def __init__(self, exception: type[E], *, match: str | re.Pattern[str] | None = None, unless: bool | None = False) -> None: ...
    @overload
    def __init__(self, exception: singleton = not_there, *, match: str | re.Pattern[str] | None = None, unless: bool | None = False) -> None: ...
    @overload
    def __init__(self, exception: E | None, *, match: None = None, unless: bool | None = False) -> None: ...

    def __init__(
            self,
            exception: E | type[E] | None | singleton = not_there,
            *,
            match: str | re.Pattern[str] | None = None,
            unless: bool | None = False,
    ) -> None:
        if match is not None and (exception is None or (exception is not not_there and not isinstance(exception, type))):
            raise TypeError('match can only be used when an exception type is provided')
        self.exception = None if exception in (None, not_there) else cast('E | type[E]', exception)
        self.expected = False if exception is None else not unless
        self.match = match

    def __enter__(self) -> Self:
        return self

    def _check_match(self, actual: BaseException) -> None:
        __tracebackhide__ = True
        if self.match is not None and not re.search(self.match, str(actual)):
            raise AssertionError(
                f'Pattern did not match:\n{self.match!r} (expected)\n{str(actual)!r} (actual)'
            )

    def __exit__(
            self,
            exc_type: type[BaseException] | None,
            actual: BaseException | None,
            traceback: TracebackType | None,
    ) -> bool:
        __tracebackhide__ = True
        self.raised = actual or NoException()  # type: ignore[assignment]
        if self.expected:
            if self.exception:
                actual_: type[BaseException] | BaseException | None = actual
                if actual is not None:
                    if isinstance(self.exception, type):
                        actual_ = type(actual)
                        if self.exception is not actual_:
                            return False
                        self._check_match(actual)
                    else:
                        if type(self.exception) is not type(actual):
                            return False
                compare(self.exception,
                        actual_,
                        x_label='expected',
                        y_label='raised')
            elif not actual:
                raise NoException()
            else:
                self._check_match(actual)
        elif actual:
            return False
        return True


P = ParamSpec("P")
T = TypeVar("T")


class should_raise(Generic[E]):
    __doc__ = """
    A decorator to assert that the decorated function will raised
    an exception. An exception class or exception instance may be
    passed to check more specifically exactly what exception will be
    raised.
    """ + param_docs

    @overload
    def __init__(self, exception: type[E], *, match: str | re.Pattern[str] | None = None, unless: bool | None = None) -> None: ...
    @overload
    def __init__(self, exception: singleton = not_there, *, match: str | re.Pattern[str] | None = None, unless: bool | None = None) -> None: ...
    @overload
    def __init__(self, exception: E | None, *, match: None = None, unless: bool | None = None) -> None: ...

    def __init__(
            self,
            exception: E | type[E] | None | singleton = not_there,
            *,
            match: str | re.Pattern[str] | None = None,
            unless: bool | None = None,
    ) -> None:
        self.exception: E | type[E] | None | singleton = exception
        self.match = match
        self.unless = unless

    def __call__(self, target: Callable[P, T]) -> Callable[P, None]:

        @wraps(target)
        def _should_raise_wrapper(*args: P.args, **kw: P.kwargs) -> None:
            with ShouldRaise(self.exception, match=self.match, unless=self.unless):  # type: ignore[arg-type]
                target(*args, **kw)

        return _should_raise_wrapper


@contextmanager
def ShouldAssert(expected_text: str, show_whitespace: bool = False) -> Iterator[None]:
    """
    A context manager to check that an :class:`AssertionError`
    is raised and its text is as expected.

    :param show_whitespace: If `True`, then whitespace characters in
                            multi-line strings will be replaced with their
                            representations.
    """
    __tracebackhide__ = True
    try:
        yield
    except AssertionError as e:
        actual_text = str(e)
        if expected_text != actual_text:
            if show_whitespace:
                expected_text = split_repr(expected_text)
                actual_text = split_repr(actual_text)
            raise AssertionError(diff(expected_text, actual_text,
                                      x_label='expected', y_label='actual'))
    else:
        raise AssertionError('Expected AssertionError(%r), None raised!' %
                             expected_text)
