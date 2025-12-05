import sys
from functools import wraps
from textwrap import dedent

from inspect import getfullargspec
from types import TracebackType
from typing import Callable, Sequence, Any, Generator, TypeVar, Generic, ParamSpec, TypeAlias

from .mock import DEFAULT, _Sentinel


def generator(*args: Any) -> Generator[Any, None, None]:
    """
    A utility function for creating a generator that will yield the
    supplied arguments.
    """
    for i in args:
        yield i

T = TypeVar("T")


class Wrapping(Generic[T]):

    attribute_name = None
    new = DEFAULT

    def __init__(self, before: Callable[[], T], after: Callable[[], None] | None):
        self.before, self.after = before, after

    def __enter__(self) -> T:
        return self.before()

    def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc_val: BaseException | None,
            exc_tb: TracebackType | None,
    ) -> None:
        if self.after is not None:
            self.after()

ExcInfo: TypeAlias = tuple[type[BaseException] | None, BaseException | None, TracebackType | None]
P = ParamSpec("P")
U = TypeVar("U")


def wrap(
        before: Callable[[], T], after: Callable[[], None] | None = None
) -> Callable[[Callable[P, U]], Callable[P, U]]:
    """
    A decorator that causes the supplied callables to be called before
    or after the wrapped callable, as appropriate.
    """

    wrapping = Wrapping(before, after)

    def wrapper(func: Callable[P, U]) -> Callable[P, U]:
        if hasattr(func, 'patchings'):
            func.patchings.append(wrapping)
            return func

        @wraps(func)
        def patched(*args: P.args, **keywargs: P.kwargs) -> U:
            extra_args = []
            entered_patchers = []

            to_add = len(getfullargspec(func).args[len(args):])
            added = 0

            exc_info: ExcInfo = (None, None, None)
            try:
                for patching in patched.patchings:  # type: ignore[attr-defined]
                    arg = patching.__enter__()
                    entered_patchers.append(patching)
                    if patching.attribute_name is not None:
                        keywargs.update(arg)
                    elif patching.new is DEFAULT and added < to_add:
                        extra_args.append(arg)
                        added += 1

                args += tuple(extra_args)  # type: ignore[assignment]
                return func(*args, **keywargs)
            except:
                # Pass the exception to __exit__
                exc_info = sys.exc_info()
                # re-raise the exception
                raise
            finally:
                for patching in reversed(entered_patchers):
                    patching.__exit__(*exc_info)

        patched.patchings = [wrapping]  # type: ignore[attr-defined]
        return patched

    return wrapper


def extend_docstring(docstring: str, objs: Sequence) -> None:
    for obj in objs:
        obj.__doc__ = dedent(obj.__doc__) + docstring


def indent(text: str, indent_size: int = 2) -> str:
    indented = []
    for do_indent, line in enumerate(text.splitlines(True)):
        if do_indent:
            line = ' '*indent_size + line
        indented.append(line)
    return ''.join(indented)
