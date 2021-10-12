import pipes
from functools import wraps, partial
from io import TextIOWrapper
from itertools import chain
from subprocess import STDOUT, PIPE
from tempfile import TemporaryFile
from testfixtures.compat import basestring, PY3, zip_longest, reduce, PY2
from testfixtures.utils import extend_docstring

from .mock import Mock, call


def shell_join(command):
    if not isinstance(command, basestring):
        command = " ".join(pipes.quote(part) for part in command)
    return command


class PopenBehaviour(object):
    """
    An object representing the behaviour of a :class:`MockPopen` when
    simulating a particular command.
    """

    def __init__(self, stdout=b'', stderr=b'', returncode=0, pid=1234,
                 poll_count=3):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode
        self.pid = pid
        self.poll_count = poll_count


def record(func):
    @wraps(func)
    def recorder(self, *args, **kw):
        self._record((func.__name__,), *args, **kw)
        return func(self, *args, **kw)
    return recorder


class MockPopenInstance(object):
    """
    A mock process as returned by :class:`MockPopen`.
    """

    #: A :class:`~unittest.mock.Mock` representing the pipe into this process.
    #: This is only set if ``stdin=PIPE`` is passed the constructor.
    #: The mock records writes and closes in :attr:`MockPopen.all_calls`.
    stdin = None

    #: A file representing standard output from this process.
    stdout = None

    #: A file representing error output from this process.
    stderr = None

    def __init__(self, mock_class, root_call,
                 args, bufsize=0, executable=None,
                 stdin=None, stdout=None, stderr=None,
                 preexec_fn=None, close_fds=False, shell=False, cwd=None,
                 env=None, universal_newlines=False,
                 startupinfo=None, creationflags=0, restore_signals=True,
                 start_new_session=False, pass_fds=(),
                 encoding=None, errors=None, text=None):
        self.mock = Mock()
        self.class_instance_mock = mock_class.mock.Popen_instance
        #: A :func:`unittest.mock.call` representing the call made to instantiate
        #: this mock process.
        self.root_call = root_call
        #: The calls made on this mock process, represented using
        #: :func:`~unittest.mock.call` instances.
        self.calls = []
        self.all_calls = mock_class.all_calls

        cmd = shell_join(args)

        behaviour = mock_class.commands.get(cmd, mock_class.default_behaviour)
        if behaviour is None:
            raise KeyError('Nothing specified for command %r' % cmd)

        if callable(behaviour):
            behaviour = behaviour(command=cmd, stdin=stdin)

        self.behaviour = behaviour

        stdout_value = behaviour.stdout
        stderr_value = behaviour.stderr

        if stderr == STDOUT:
            line_iterator = chain.from_iterable(zip_longest(
                stdout_value.splitlines(True),
                stderr_value.splitlines(True)
            ))
            stdout_value = b''.join(l for l in line_iterator if l)
            stderr_value = None

        self.poll_count = behaviour.poll_count
        for name, option, mock_value in (
            ('stdout', stdout, stdout_value),
            ('stderr', stderr, stderr_value)
        ):
            value = None
            if option is PIPE:
                value = TemporaryFile()
                value.write(mock_value)
                value.flush()
                value.seek(0)
                if PY3 and (universal_newlines or text or encoding):
                    value = TextIOWrapper(value, encoding=encoding, errors=errors)
            setattr(self, name, value)

        if stdin == PIPE:
            self.stdin = Mock()
            for method in 'write', 'close':
                record_writes = partial(self._record, ('stdin', method))
                getattr(self.stdin, method).side_effect = record_writes

        self.pid = behaviour.pid
        #: The return code of this mock process.
        self.returncode = None
        if PY3:
            self.args = args

    def _record(self, names, *args, **kw):
        for mock in self.class_instance_mock, self.mock:
            reduce(getattr, names, mock)(*args, **kw)
        for base_call, store in (
            (call, self.calls),
            (self.root_call, self.all_calls)
        ):
            store.append(reduce(getattr, names, base_call)(*args, **kw))

    if PY3:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.wait()
            for stream in self.stdout, self.stderr:
                if stream:
                    stream.close()

        @record
        def wait(self, timeout=None):
            "Simulate calls to :meth:`subprocess.Popen.wait`"
            self.returncode = self.behaviour.returncode
            return self.returncode

        @record
        def communicate(self, input=None, timeout=None):
            "Simulate calls to :meth:`subprocess.Popen.communicate`"
            self.returncode = self.behaviour.returncode
            return (self.stdout and self.stdout.read(),
                    self.stderr and self.stderr.read())
    else:
        @record
        def wait(self):  # pragma: no cover
            "Simulate calls to :meth:`subprocess.Popen.wait`"
            self.returncode = self.behaviour.returncode
            return self.returncode

        @record
        def communicate(self, input=None):
            "Simulate calls to :meth:`subprocess.Popen.communicate`"
            self.returncode = self.behaviour.returncode
            return (self.stdout and self.stdout.read(),
                    self.stderr and self.stderr.read())

    @record
    def poll(self):
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
    def send_signal(self, signal):
        "Simulate calls to :meth:`subprocess.Popen.send_signal`"
        pass

    @record
    def terminate(self):
        "Simulate calls to :meth:`subprocess.Popen.terminate`"
        pass

    @record
    def kill(self):
        "Simulate calls to :meth:`subprocess.Popen.kill`"
        pass


class MockPopen(object):
    """
    A specialised mock for testing use of :class:`subprocess.Popen`.
    An instance of this class can be used in place of the
    :class:`subprocess.Popen` and is often inserted where it's needed using
    :func:`unittest.mock.patch` or a :class:`~testfixtures.Replacer`.
    """

    default_behaviour = None

    def __init__(self):
        self.commands = {}
        self.mock = Mock()
        #: All calls made using this mock and the objects it returns, represented using
        #: :func:`~unittest.mock.call` instances.
        self.all_calls = []

    def _resolve_behaviour(self, stdout, stderr, returncode,
                           pid, poll_count, behaviour):
        if behaviour is None:
            return PopenBehaviour(
                stdout, stderr, returncode, pid, poll_count
            )
        else:
            return behaviour

    def set_command(self, command, stdout=b'', stderr=b'', returncode=0,
                    pid=1234, poll_count=3, behaviour=None):
        """
        Set the behaviour of this mock when it is used to simulate the
        specified command.

        :param command: A string representing the command to be simulated.
        """
        self.commands[shell_join(command)] = self._resolve_behaviour(
            stdout, stderr, returncode, pid, poll_count, behaviour
        )

    def set_default(self, stdout=b'', stderr=b'', returncode=0,
                    pid=1234, poll_count=3, behaviour=None):
        """
        Set the behaviour of this mock when it is used to simulate commands
        that have no explicit behavior specified using
        :meth:`~MockPopen.set_command` or :meth:`~MockPopen.set_callable`.
        """
        self.default_behaviour = self._resolve_behaviour(
            stdout, stderr, returncode, pid, poll_count, behaviour
        )

    def __call__(self, *args, **kw):
        self.mock.Popen(*args, **kw)
        root_call = call.Popen(*args, **kw)
        self.all_calls.append(root_call)
        return MockPopenInstance(self, root_call, *args, **kw)


set_command_params = """
:param stdout:
    A string representing the simulated content written by the process
    to the stdout pipe.
:param stderr:
    A string representing the simulated content written by the process
    to the stderr pipe.
:param returncode:
    An integer representing the return code of the simulated process.
:param pid:
    An integer representing the process identifier of the simulated
    process. This is useful if you have code the prints out the pids
    of running processes.
:param poll_count:
    Specifies the number of times :meth:`MockPopen.poll` can be
    called before :attr:`MockPopen.returncode` is set and returned
    by :meth:`MockPopen.poll`.

If supplied, ``behaviour`` must be either a :class:`PopenBehaviour`
instance or a callable that takes the ``command`` string representing
the command to be simulated and the ``stdin`` for that command and
returns a :class:`PopenBehaviour` instance.
"""


# add the param docs, so we only have one copy of them!
extend_docstring(set_command_params,
                 [MockPopen.set_command, MockPopen.set_default])
