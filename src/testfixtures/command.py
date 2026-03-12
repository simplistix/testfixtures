import sys
from typing import Callable, Generic, TypeVar, overload

from testfixtures import OutputCapture


class Result:
    def __init__(self, return_code: int, output: OutputCapture) -> None:
        self.return_code = return_code
        self.output = output

    def check(self, output: str = '', return_code: int = 0) -> None:
        __tracebackhide__ = True

        if self.return_code != return_code:
            raise AssertionError(f'return code {self.return_code!r} != {return_code!r}')
        self.output.compare(output)


T = TypeVar("T", bound=Result)


class Command(Generic[T]):
    @overload
    def __init__(self: "Command[Result]", main: Callable[[], None]) -> None: ...

    @overload
    def __init__(self: "Command[T]", main: Callable[[], None], result: type[T]) -> None: ...

    def __init__(self, main: Callable[[], None], result: type[Result] = Result) -> None:
        self.main = main
        self.result = result

    def run(self, *argv: str) -> T:
        capture = OutputCapture()
        return_code = 0
        old_argv = sys.argv
        sys.argv = [getattr(self.main, '__name__', 'main')] + list(argv)
        try:
            with capture:
                try:
                    self.main()
                except SystemExit as e:
                    return_code = e.code if isinstance(e.code, int) else 0
        finally:
            sys.argv = old_argv
        return self.result(return_code, capture)  # type: ignore[return-value]

    __call__ = run
