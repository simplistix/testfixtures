import shlex
from dataclasses import dataclass
from functools import wraps, partial, reduce
from io import TextIOWrapper
from itertools import chain, zip_longest
from os import PathLike
from subprocess import STDOUT, PIPE
# Captured at import time so that Passthrough can delegate to the real
# Popen even when a test has since patched subprocess.Popen itself.
from subprocess import Popen as RealPopen
from tempfile import TemporaryFile
from types import TracebackType
from typing import (
    Callable, List, Sequence, Tuple, Iterable, TypeAlias, ParamSpec,
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


@dataclass
class Raises:
    """
    Specifies exceptions to be raised by particular methods of a
    :class:`MockPopenInstance`, instead of that method's normal simulated
    behaviour, when supplied as the ``raises`` of a :class:`PopenBehaviour`.
    """
    #: If not ``None``, raised by :meth:`~MockPopenInstance.communicate`.
    communicate: BaseException | None = None
    #: If not ``None``, raised by :meth:`~MockPopenInstance.wait`.
    wait: BaseException | None = None
    #: If not ``None``, raised by :meth:`~MockPopenInstance.send_signal`.
    send_signal: BaseException | None = None
    #: If not ``None``, raised by :meth:`~MockPopenInstance.terminate`.
    terminate: BaseException | None = None
    #: If not ``None``, raised by :meth:`~MockPopenInstance.kill`.
    kill: BaseException | None = None


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
            poll_count: int = 3,
            raises: Raises | None = None,
    ):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode
        self.pid = pid
        self.poll_count = poll_count
        #: A :class:`Raises` specifying exceptions to raise instead of
        #: simulating particular method calls.
        self.raises: Raises = raises if raises is not None else Raises()


class CallableBehaviour(Protocol):

    def __call__(self, command: str, stdin: File) -> PopenBehaviour: ...


class Passthrough:
    """
    A sentinel behaviour that, when supplied as the ``behaviour`` of
    :meth:`~MockPopen.set_command` or :meth:`~MockPopen.set_default`,
    causes the matching command to be passed through to the real
    :class:`subprocess.Popen` instead of being simulated.
    """


P = ParamSpec('P')
R = TypeVar('R')
Instance = TypeVar('Instance', bound='MockPopenInstance')


def record(
        func: Callable[Concatenate[Instance, P], R]
) -> Callable[Concatenate[Instance, P], R]:
    @wraps(func)
    def recorder(self: Instance, *args: P.args, **kw: P.kwargs) -> R:
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
    stdin: Mock | IO[Any] | None = None

    #: A file representing standard output from this process.
    stdout: IO[Any] | None = None

    #: A file representing error output from this process.
    stderr: IO[Any] | None = None

    #: A :func:`unittest.mock.call` representing the call made to instantiate
    #: this mock process.
    root_call: Call

    #: The calls made on this mock process, represented using
    #: :func:`~unittest.mock.call` instances.
    calls: List[Call]

    # These are not types as instantiation of this class is an internal implementation detail.
    def __init__(
            self,
            mock_class: 'MockPopen',
            root_call: Call,
            behaviour: PopenBehaviour | CallableBehaviour,
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
            universal_newlines: bool | None = None,
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
        self._setup_recording(mock_class, root_call)

        if callable(behaviour):
            behaviour = behaviour(command=shell_join(args), stdin=stdin)

        self.behaviour: PopenBehaviour = behaviour

        stdout_value = behaviour.stdout
        stderr_value: bytes | None = behaviour.stderr

        if stderr == STDOUT:
            line_iterator = chain.from_iterable(zip_longest(
                stdout_value.splitlines(True),
                behaviour.stderr.splitlines(True)
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

    def _setup_recording(self, mock_class: 'MockPopen', root_call: Call) -> None:
        self.mock: Mock = Mock()
        self.class_instance_mock: Mock = mock_class.mock.Popen_instance
        self.root_call = root_call
        self.calls = []
        self.all_calls: List[Call] = mock_class.all_calls

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
        if self.behaviour.raises.wait is not None:
            raise self.behaviour.raises.wait
        self.returncode = self.behaviour.returncode
        return self.returncode

    @record
    def communicate(
            self, input: str | bytes | None = None, timeout: float | None = None
    ) -> Tuple[str | bytes | None, str | bytes | None]:
        "Simulate calls to :meth:`subprocess.Popen.communicate`"
        if self.behaviour.raises.communicate is not None:
            raise self.behaviour.raises.communicate
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
        if self.behaviour.raises.send_signal is not None:
            raise self.behaviour.raises.send_signal

    @record
    def terminate(self) -> None:
        "Simulate calls to :meth:`subprocess.Popen.terminate`"
        if self.behaviour.raises.terminate is not None:
            raise self.behaviour.raises.terminate

    @record
    def kill(self) -> None:
        "Simulate calls to :meth:`subprocess.Popen.kill`"
        if self.behaviour.raises.kill is not None:
            raise self.behaviour.raises.kill


class PassthroughPopenInstance(MockPopenInstance):
    """
    A process as returned by :class:`MockPopen` for a command whose behaviour
    is :class:`Passthrough`. Calls are recorded just as for a
    :class:`MockPopenInstance`, but are delegated to a real
    :class:`subprocess.Popen`, whose :attr:`~subprocess.Popen.stdin`,
    :attr:`~subprocess.Popen.stdout` and :attr:`~subprocess.Popen.stderr`
    are used directly.
    """

    # These are not types as instantiation of this class is an internal implementation detail.
    def __init__(
            self, mock_class: 'MockPopen', root_call: Call, *args: Any, **kw: Any
    ) -> None:
        self._setup_recording(mock_class, root_call)
        #: The real :class:`subprocess.Popen` this process delegates to.
        self.real: RealPopen[Any] = RealPopen(*args, **kw)
        self.args = self.real.args
        self.pid = self.real.pid
        self.stdin = self.real.stdin
        self.stdout = self.real.stdout
        self.stderr = self.real.stderr
        self.returncode = self.real.returncode

    def __exit__(
            self,
            exc_type: type[BaseException] | None,
            value: BaseException | None,
            traceback: TracebackType | None,
    ) -> None:
        # As with the real Popen, stdin must be closed before waiting, or a
        # process reading it until EOF would never exit.
        if self.stdin:
            self.stdin.close()
        super().__exit__(exc_type, value, traceback)

    @record
    def wait(self, timeout: float | None = None) -> int:
        "Delegate to :meth:`subprocess.Popen.wait`"
        self.returncode = self.real.wait(timeout=timeout)
        return self.returncode

    @record
    def communicate(
            self, input: str | bytes | None = None, timeout: float | None = None
    ) -> Tuple[str | bytes | None, str | bytes | None]:
        "Delegate to :meth:`subprocess.Popen.communicate`"
        stdout, stderr = self.real.communicate(input=input, timeout=timeout)
        self.returncode = self.real.returncode
        return stdout, stderr

    @record
    def poll(self) -> int | None:
        "Delegate to :meth:`subprocess.Popen.poll`"
        self.returncode = self.real.poll()
        return self.returncode

    @record
    def send_signal(self, signal: int) -> None:
        "Delegate to :meth:`subprocess.Popen.send_signal`"
        self.real.send_signal(signal)

    @record
    def terminate(self) -> None:
        "Delegate to :meth:`subprocess.Popen.terminate`"
        self.real.terminate()

    @record
    def kill(self) -> None:
        "Delegate to :meth:`subprocess.Popen.kill`"
        self.real.kill()


class MockPopen:
    """
    A specialised mock for testing use of :class:`subprocess.Popen`.
    An instance of this class can be used in place of the
    :class:`subprocess.Popen` and is often inserted where it's needed using
    :func:`unittest.mock.patch` or a :class:`~testfixtures.Replacer`.
    """

    default_behaviour: PopenBehaviour | CallableBehaviour | Passthrough | None = None

    def __init__(self) -> None:
        self.commands: dict[str, PopenBehaviour | CallableBehaviour | Passthrough] = {}
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
            behaviour: PopenBehaviour | CallableBehaviour | Passthrough | None,
            raises: Raises | None,
    ) -> PopenBehaviour | CallableBehaviour | Passthrough:
        if behaviour is None:
            return PopenBehaviour(
                stdout, stderr, returncode, pid, poll_count, raises
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
            behaviour: PopenBehaviour | CallableBehaviour | Passthrough | None = None,
            raises: Raises | None = None,
    ) -> None:
        """
        Set the behaviour of this mock when it is used to simulate the
        specified command.

        :param command: A :class:`str` representing the command to be simulated.
        """
        self.commands[shell_join(command)] = self._resolve_behaviour(
            stdout, stderr, returncode, pid, poll_count, behaviour, raises
        )

    def set_default(
            self,
            stdout: bytes = b'',
            stderr: bytes = b'',
            returncode: int =0,
            pid: int = 1234,
            poll_count: int = 3,
            behaviour: PopenBehaviour | CallableBehaviour | Passthrough | None = None,
            raises: Raises | None = None,
    ) -> None:
        """
        Set the behaviour of this mock when it is used to simulate commands
        that have no explicit behavior specified using
        :meth:`~MockPopen.set_command`.
        """
        self.default_behaviour = self._resolve_behaviour(
            stdout, stderr, returncode, pid, poll_count, behaviour, raises
        )

    def __call__(self, args: Command, *popenargs: Any, **kw: Any) -> MockPopenInstance:
        self.mock.Popen(args, *popenargs, **kw)
        root_call = call.Popen(args, *popenargs, **kw)
        self.all_calls.append(root_call)
        cmd = shell_join(args)
        behaviour = self.commands.get(cmd, self.default_behaviour)
        if behaviour is None:
            raise KeyError('Nothing specified for command %r' % cmd)
        if isinstance(behaviour, Passthrough):
            return PassthroughPopenInstance(self, root_call, args, *popenargs, **kw)
        return MockPopenInstance(self, root_call, behaviour, args, *popenargs, **kw)


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
:param raises:
    A :class:`Raises` specifying exceptions to be raised by particular
    methods of the simulated process, instead of their normal simulated
    behaviour.

If supplied, ``behaviour`` must be one of:

- A :class:`PopenBehaviour` instance.
- A callable that takes the ``command`` string representing the command to
  be simulated and the ``stdin`` supplied when instantiating the
  :class:`subprocess.Popen` with that command and should return a
  :class:`PopenBehaviour` instance.
- A :class:`Passthrough` instance, causing the command to be passed
  through to the real :class:`subprocess.Popen` instead of being
  simulated.
"""


# add the param docs, so we only have one copy of them!
extend_docstring(set_command_params,
                 [MockPopen.set_command, MockPopen.set_default])
