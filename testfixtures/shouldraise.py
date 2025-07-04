from contextlib import contextmanager
from functools import wraps
from types import TracebackType
from typing import Callable, TypeAlias, Iterator, Self, ParamSpec, TypeVar

from testfixtures import diff, compare
from .comparison import split_repr

ExceptionOrType: TypeAlias = BaseException | type[BaseException]


param_docs = """

    :param exception: This can be one of the following:

                      * `None`, indicating that an exception must be
                        raised, but the type is unimportant.

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


class ShouldRaise:
    __doc__ = """
    This context manager is used to assert that an exception is raised
    within the context it is managing.
    """ + param_docs

    #: The exception captured by the context manager.
    #: Can be used to inspect specific attributes of the exception.
    raised: BaseException = NoException()

    def __init__(self, exception: ExceptionOrType | None = None, unless: bool | None = False):
        self.exception = exception
        self.expected = not unless

    def __enter__(self) -> Self:
        return self

    def __exit__(
            self,
            exc_type: type[BaseException] | None,
            actual: BaseException | None,
            traceback: TracebackType | None,
    ) -> bool:
        __tracebackhide__ = True
        self.raised = actual or NoException()
        if self.expected:
            if self.exception:
                actual_: type[BaseException] | BaseException | None = actual
                if actual is not None:
                    if isinstance(self.exception, type):
                        actual_ = type(actual)
                        if self.exception is not actual_:
                            return False
                    else:
                        if type(self.exception) is not type(actual):
                            return False
                compare(self.exception,
                        actual_,
                        x_label='expected',
                        y_label='raised')
            elif not actual:
                raise NoException()
        elif actual:
            return False
        return True


P = ParamSpec("P")
T = TypeVar("T")


class should_raise:
    __doc__ = """
    A decorator to assert that the decorated function will raised
    an exception. An exception class or exception instance may be
    passed to check more specifically exactly what exception will be
    raised.
    """ + param_docs

    def __init__(self, exception: ExceptionOrType | None = None, unless: bool | None = None):
        self.exception = exception
        self.unless = unless

    def __call__(self, target: Callable[P, T]) -> Callable[P, None]:

        @wraps(target)
        def _should_raise_wrapper(*args: P.args, **kw: P.kwargs) -> None:
            with ShouldRaise(self.exception, self.unless):
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
