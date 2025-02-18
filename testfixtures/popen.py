import shlex
from functools import wraps, partial, reduce
from io import TextIOWrapper
from itertools import chain, zip_longest
from os import PathLike
from subprocess import STDOUT, PIPE
from tempfile import TemporaryFile
from types import TracebackType
from typing import (
    Callable, List, Sequence, Tuple, Iterable, TextIO, TypeAlias, ParamSpec,
    TypeVar, Concatenate, IO, Any, Mapping, Collection, Literal, Self, Protocol
)

from .mock import Mock, call, _Call as Call
from .utils import extend_docstring

StrOrBytesPath: TypeAlias = str | bytes | PathLike
Command: TypeAlias = StrOrBytesPath | Sequence[StrOrBytesPath]
File : TypeAlias = None | int | IO[Any]


def shell_join(command: Command) -> str:
    if isinstance(command, str):
        return command
    elif isinstance(command, bytes):
        return command.decode()
    elif isinstance(command, PathLike):
        return str(command)
    elif isinstance(command, Iterable):
        quoted_parts = []
        for part in command:
            if isinstance(part, str):
                pass
            elif isinstance(part, bytes):
                part = part.decode()
            elif isinstance(part, PathLike):
                part = str(part)
            elif not isinstance(part, (str, bytes)):
                raise TypeError(f'{part!r} in {command!r} was {type(part)}, must be str')
            quoted_parts.append(shlex.quote(part))
        return " ".join(quoted_parts)
    else:
        raise TypeError(f'{command!r} was {type(command)}, must be str')

class PopenBehaviour:
    """
    An object representing the behaviour of a :class:`MockPopen` when
    simulating a particular command.
    """

    def __init__(
            self,
            stdout: bytes = b'',
            stderr: bytes = b'',
            returncode: int = 0,
            pid: int = 1234,
            poll_count: int = 3
    ):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode
        self.pid = pid
        self.poll_count = poll_count


class CallableBehaviour(Protocol):

    def __call__(self, command: str, stdin: File) -> PopenBehaviour: ...


P = ParamSpec('P')
R = TypeVar('R')


def record(
        func: Callable[Concatenate['MockPopenInstance', P], R]
) -> Callable[Concatenate['MockPopenInstance', P], R]:
    @wraps(func)
    def recorder(self: 'MockPopenInstance', *args: P.args, **kw: P.kwargs) -> R:
        self._record((func.__name__,), *args, **kw)
        return func(self, *args, **kw)
    return recorder


class MockPopenInstance:
    """
    A mock process as returned by :class:`MockPopen`.
    """

    #: A :class:`~unittest.mock.Mock` representing the pipe into this process.
    #: This is only set if ``stdin=PIPE`` is passed the constructor.
    #: The mock records writes and closes in :attr:`MockPopen.all_calls`.
    stdin: Mock | None = None

    #: A file representing standard output from this process.
    stdout: TextIO | None = None

    #: A file representing error output from this process.
    stderr: TextIO | None = None

    # These are not types as instantiation of this class is an internal implementation detail.
    def __init__(
            self,
            mock_class: 'MockPopen',
            root_call: Call,
            args: Command,
            bufsize: int = 0,
            executable: StrOrBytesPath | None = None,
            stdin: File = None,
            stdout: File = None,
            stderr: File = None,
            preexec_fn: Callable[[], Any] | None = None,
            close_fds: bool = False,
            shell: bool = False,
            cwd: StrOrBytesPath | None = None,
            env: Mapping[str, str] | None = None,
            universal_newlines: bool = False,
            startupinfo: Any = None,
            creationflags: int = 0,
            restore_signals: bool = True,
            start_new_session: bool = False,
            pass_fds: Collection[int] = (),
            *,
            encoding: str | None = None,
            errors: str | None = None,
            text: bool | None = None,
    ) -> None:
        self.mock: Mock = Mock()
        self.class_instance_mock: Mock = mock_class.mock.Popen_instance
        #: A :func:`unittest.mock.call` representing the call made to instantiate
        #: this mock process.
        self.root_call: Call = root_call
        #: The calls made on this mock process, represented using
        #: :func:`~unittest.mock.call` instances.
        self.calls: List[Call] = []
        self.all_calls: List[Call] = mock_class.all_calls

        cmd = shell_join(args)

        behaviour: Any
        behaviour = mock_class.commands.get(cmd, mock_class.default_behaviour)
        if behaviour is None:
            raise KeyError('Nothing specified for command %r' % cmd)

        if callable(behaviour):
            behaviour = behaviour(command=cmd, stdin=stdin)

        self.behaviour: PopenBehaviour = behaviour

        stdout_value = behaviour.stdout
        stderr_value = behaviour.stderr

        if stderr == STDOUT:
            line_iterator = chain.from_iterable(zip_longest(
                stdout_value.splitlines(True),
                stderr_value.splitlines(True)
            ))
            stdout_value = b''.join(l for l in line_iterator if l)
            stderr_value = None

        self.poll_count: int = behaviour.poll_count
        for name, option, mock_value in (
            ('stdout', stdout, stdout_value),
            ('stderr', stderr, stderr_value)
        ):
            value: Any = None
            if option is PIPE:
                value = TemporaryFile()
                value.write(mock_value)
                value.flush()
                value.seek(0)
                if universal_newlines or text or encoding:
                    value = TextIOWrapper(value, encoding=encoding, errors=errors)
            setattr(self, name, value)

        if stdin == PIPE:
            self.stdin = Mock()
            for method in 'write', 'close':
                record_writes = partial(self._record, ('stdin', method))
                getattr(self.stdin, method).side_effect = record_writes

        self.pid: int = behaviour.pid
        #: The return code of this mock process.
        self.returncode: int | None = None
        self.args: Command = args

    def _record(self, names: Sequence[str], *args: Any, **kw: Any) -> None:
        for mock in self.class_instance_mock, self.mock:
            reduce(getattr, names, mock)(*args, **kw)
        for base_call, store in (
            (call, self.calls),
            (self.root_call, self.all_calls)
        ):
            store.append(reduce(getattr, names, base_call)(*args, **kw))

    def __enter__(self) -> Self:
        return self

    def __exit__(
            self,
            exc_type: type[BaseException] | None,
            value: BaseException | None,
            traceback: TracebackType | None,
    ) -> None:
        self.wait()
        for stream in self.stdout, self.stderr:
            if stream:
                stream.close()

    @record
    def wait(self, timeout: float | None = None) -> int:
        "Simulate calls to :meth:`subprocess.Popen.wait`"
        self.returncode = self.behaviour.returncode
        return self.returncode

    @record
    def communicate(
            self, input: str | bytes | None = None, timeout: float | None = None
    ) -> Tuple[str | bytes | None, str | bytes | None]:
        "Simulate calls to :meth:`subprocess.Popen.communicate`"
        self.returncode = self.behaviour.returncode
        stdout = None if self.stdout is None else self.stdout.read()
        stderr = None if self.stderr is None else self.stderr.read()
        return stdout, stderr

    @record
    def poll(self) -> int | None:
        "Simulate calls to :meth:`subprocess.Popen.poll`"
        while self.poll_count and self.returncode is None:
            self.poll_count -= 1
            return None
        # This call to wait() is NOT how poll() behaves in reality.
        # poll() NEVER sets the returncode.
        # The returncode is *only* ever set by process completion.
        # The following is an artifact of the fixture's implementation.
        self.returncode = self.behaviour.returncode
        return self.returncode

    @record
    def send_signal(self, signal: int) -> None:
        "Simulate calls to :meth:`subprocess.Popen.send_signal`"
        pass

    @record
    def terminate(self) -> None:
        "Simulate calls to :meth:`subprocess.Popen.terminate`"
        pass

    @record
    def kill(self) -> None:
        "Simulate calls to :meth:`subprocess.Popen.kill`"
        pass


class MockPopen:
    """
    A specialised mock for testing use of :class:`subprocess.Popen`.
    An instance of this class can be used in place of the
    :class:`subprocess.Popen` and is often inserted where it's needed using
    :func:`unittest.mock.patch` or a :class:`~testfixtures.Replacer`.
    """

    default_behaviour: PopenBehaviour | CallableBehaviour | None = None

    def __init__(self) -> None:
        self.commands: dict[str, PopenBehaviour | CallableBehaviour] = {}
        self.mock: Mock = Mock()
        #: All calls made using this mock and the objects it returns, represented using
        #: :func:`~unittest.mock.call` instances.
        self.all_calls: List[Call] = []

    def _resolve_behaviour(
            self,
            stdout: bytes,
            stderr: bytes,
            returncode: int,
            pid: int,
            poll_count: int,
            behaviour: PopenBehaviour | CallableBehaviour | None
    ) -> PopenBehaviour | CallableBehaviour:
        if behaviour is None:
            return PopenBehaviour(
                stdout, stderr, returncode, pid, poll_count
            )
        else:
            return behaviour

    def set_command(
            self,
            command: str,
            stdout: bytes = b'',
            stderr: bytes = b'',
            returncode: int = 0,
            pid: int = 1234,
            poll_count: int = 3,
            behaviour: PopenBehaviour | CallableBehaviour | None = None
    ) -> None:
        """
        Set the behaviour of this mock when it is used to simulate the
        specified command.

        :param command: A :class:`str` representing the command to be simulated.
        """
        self.commands[shell_join(command)] = self._resolve_behaviour(
            stdout, stderr, returncode, pid, poll_count, behaviour
        )

    def set_default(
            self,
            stdout: bytes = b'',
            stderr: bytes = b'',
            returncode: int =0,
            pid: int = 1234,
            poll_count: int = 3,
            behaviour: PopenBehaviour | CallableBehaviour | None = None
    ) -> None:
        """
        Set the behaviour of this mock when it is used to simulate commands
        that have no explicit behavior specified using
        :meth:`~MockPopen.set_command`.
        """
        self.default_behaviour = self._resolve_behaviour(
            stdout, stderr, returncode, pid, poll_count, behaviour
        )

    def __call__(self, *args: Any, **kw: Any) -> MockPopenInstance:
        self.mock.Popen(*args, **kw)
        root_call = call.Popen(*args, **kw)
        self.all_calls.append(root_call)
        return MockPopenInstance(self, root_call, *args, **kw)


set_command_params = """
:param stdout:
    :class:`bytes` representing the simulated content written by the process
    to the stdout pipe.
:param stderr:
    :class:`bytes` representing the simulated content written by the process
    to the stderr pipe.
:param returncode:
    An integer representing the return code of the simulated process.
:param pid:
    An integer representing the process identifier of the simulated
    process. This is useful if you have code the prints out the pids
    of running processes.
:param poll_count:
    Specifies the number of times :meth:`~MockPopenInstance.poll` can be
    called before :attr:`~MockPopenInstance.returncode` is set and returned
    by :meth:`~MockPopenInstance.poll`.

If supplied, ``behaviour`` must be either a :class:`PopenBehaviour`
instance or a callable that takes the ``command`` string representing
the command to be simulated and the ``stdin`` supplied when instantiating
the :class:`subprocess.Popen` with that command and should
return a :class:`PopenBehaviour` instance.
"""


# add the param docs, so we only have one copy of them!
extend_docstring(set_command_params,
                 [MockPopen.set_command, MockPopen.set_default])
