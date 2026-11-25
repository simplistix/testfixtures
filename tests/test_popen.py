import subprocess
import sys
from pathlib import Path
from subprocess import PIPE, STDOUT
from unittest import TestCase

from testfixtures.mock import call
from testfixtures import ShouldRaise, compare, Replacer

from testfixtures.popen import MockPopen, Passthrough, PopenBehaviour, Raises

import signal


class Tests(TestCase):

    def test_command_min_args(self):
        # setup
        Popen = MockPopen()
        Popen.set_command('a command')
        # usage
        process = Popen('a command', stdout=PIPE, stderr=PIPE)
        # process started, no return code
        compare(process.pid, 1234)
        compare(None, process.returncode)

        out, err = process.communicate()

        # test the rest
        compare(out, b'')
        compare(err, b'')
        compare(process.returncode, 0)
        # test call list
        compare([
                call.Popen('a command', stderr=-1, stdout=-1),
                call.Popen_instance.communicate(),
                ], Popen.mock.method_calls)

    def test_command_max_args(self):

        Popen = MockPopen()
        Popen.set_command('a command', b'out', b'err', 1, 345)

        process = Popen('a command', stdout=PIPE, stderr=PIPE)
        compare(process.pid, 345)
        compare(None, process.returncode)

        out, err = process.communicate()

        # test the rest
        compare(out, b'out')
        compare(err, b'err')
        compare(process.returncode, 1)
        # test call list
        compare([
                call.Popen('a command', stderr=-1, stdout=-1),
                call.Popen_instance.communicate(),
                ], Popen.mock.method_calls)

    def test_callable_default_behaviour(self):
        def some_callable(command, stdin):
            return PopenBehaviour(bytes(command, 'ascii'), bytes(stdin, 'ascii'), 1, 345, 0)

        Popen = MockPopen()
        Popen.set_default(behaviour=some_callable)

        process = Popen('a command', stdin='some stdin', stdout=PIPE, stderr=PIPE)
        compare(process.pid, 345)

        out, err = process.communicate()

        compare(out, b'a command')
        compare(err, b'some stdin')
        compare(process.returncode, 1)

    def test_command_is_sequence(self):
        Popen = MockPopen()
        Popen.set_command('a command')

        process = Popen(['a', 'command'], stdout=PIPE, stderr=PIPE)

        compare(process.wait(), 0)
        compare([
                call.Popen(['a', 'command'], stderr=-1, stdout=-1),
                call.Popen_instance.wait(),
                ], Popen.mock.method_calls)

    def test_command_is_pathlike(self):
        Popen = MockPopen()
        Popen.set_command('a command')

        process = Popen(Path('a command'))

        compare(process.wait(), 0)
        compare([
                call.Popen(Path('a command')),
                call.Popen_instance.wait(),
                ], Popen.mock.method_calls)

    def test_command_is_bytes(self):
        Popen = MockPopen()
        Popen.set_command('a command')

        process = Popen(b'a command')

        compare(process.wait(), 0)
        compare([
                call.Popen(b'a command'),
                call.Popen_instance.wait(),
                ], Popen.mock.method_calls)

    def test_command_is_incorrect_type(self):
        Popen = MockPopen()
        Popen.set_command('a command')
        with ShouldRaise(TypeError("42 was <class 'int'>, must be str")):
            Popen(42)

    def test_command_is_sequence_of_pathlike(self):
        Popen = MockPopen()
        Popen.set_command('a command')

        process = Popen(['a', Path('command')])

        compare(process.wait(), 0)
        compare([
                call.Popen(['a', Path('command')]),
                call.Popen_instance.wait(),
                ], Popen.mock.method_calls)

    def test_command_is_sequence_of_bytes(self):
        Popen = MockPopen()
        Popen.set_command('a command')

        process = Popen(['a', b'command'])

        compare(process.wait(), 0)
        compare([
                call.Popen(['a', b'command']),
                call.Popen_instance.wait(),
                ], Popen.mock.method_calls)

    def test_command_is_sequence_of_incorrect_type(self):
        Popen = MockPopen()
        Popen.set_command('a command')
        with ShouldRaise(TypeError("42 in ['x', 42] was <class 'int'>, must be str")):
            Popen(['x', 42])

    def test_communicate_with_input(self):
        # setup
        Popen = MockPopen()
        Popen.set_command('a command')
        # usage
        process = Popen('a command', stdout=PIPE, stderr=PIPE, shell=True)
        out, err = process.communicate('foo')
        # test call list
        compare([
                call.Popen('a command', shell=True, stderr=-1, stdout=-1),
                call.Popen_instance.communicate('foo'),
                ], Popen.mock.method_calls)

    def test_communicate_with_timeout(self):
        Popen = MockPopen()
        Popen.set_command('a command', returncode=3)
        process = Popen('a command')
        process.communicate(timeout=1)
        process.communicate('foo', 1)
        compare([
            call.Popen('a command'),
            call.Popen_instance.communicate(timeout=1),
            call.Popen_instance.communicate('foo', 1),
        ], expected=Popen.mock.method_calls)

    def test_read_from_stdout(self):
        # setup
        Popen = MockPopen()
        Popen.set_command('a command', stdout=b'foo')
        # usage
        process = Popen('a command', stdout=PIPE, stderr=PIPE, shell=True)
        self.assertTrue(isinstance(process.stdout.fileno(), int))
        compare(process.stdout.read(), b'foo')
        # test call list
        compare([
                call.Popen('a command', shell=True, stderr=-1, stdout=-1),
                ], Popen.mock.method_calls)

    def test_read_from_stderr(self):
        # setup
        Popen = MockPopen()
        Popen.set_command('a command', stderr=b'foo')
        # usage
        process = Popen('a command', stdout=PIPE, stderr=PIPE, shell=True)
        self.assertTrue(isinstance(process.stdout.fileno(), int))
        compare(process.stderr.read(), b'foo')
        # test call list
        compare([
                call.Popen('a command', shell=True, stderr=-1, stdout=-1),
                ], Popen.mock.method_calls)

    def test_read_from_stdout_with_stderr_redirected_check_stdout_contents(self):
        # setup
        Popen = MockPopen()
        Popen.set_command('a command', stdout=b'foo', stderr=b'bar')
        # usage
        process = Popen('a command', stdout=PIPE, stderr=STDOUT, shell=True)
        # test stdout contents
        compare(b'foobar', process.stdout.read())
        compare(process.stderr, None)

    def test_read_from_stdout_with_stderr_redirected_check_stdout_stderr_interleaved(self):
        # setup
        Popen = MockPopen()
        Popen.set_command('a command', stdout=b'o1\no2\no3\no4\n', stderr=b'e1\ne2\n')
        # usage
        process = Popen('a command', stdout=PIPE, stderr=STDOUT, shell=True)
        self.assertTrue(isinstance(process.stdout.fileno(), int))
        # test stdout contents
        compare(b'o1\ne1\no2\ne2\no3\no4\n', process.stdout.read())

    def test_communicate_with_stderr_redirected_check_stderr_is_none(self):
        # setup
        Popen = MockPopen()
        Popen.set_command('a command', stdout=b'foo', stderr=b'bar')
        # usage
        process = Popen('a command', stdout=PIPE, stderr=STDOUT, shell=True)
        out, err = process.communicate()
        # test stderr is None
        compare(out, b'foobar')
        compare(err, None)

    def test_read_from_stdout_and_stderr(self):
        # setup
        Popen = MockPopen()
        Popen.set_command('a command', stdout=b'foo', stderr=b'bar')
        # usage
        process = Popen('a command', stdout=PIPE, stderr=PIPE, shell=True)
        compare(process.stdout.read(), b'foo')
        compare(process.stderr.read(), b'bar')
        # test call list
        compare([
                call.Popen('a command', shell=True, stderr=PIPE, stdout=PIPE),
                ], Popen.mock.method_calls)

    def test_communicate_text_mode(self):
        Popen = MockPopen()
        Popen.set_command('a command', stdout=b'foo', stderr=b'bar')
        # usage
        process = Popen('a command', stdout=PIPE, stderr=PIPE, text=True)
        actual = process.communicate()
        # check
        compare(actual, expected=(u'foo', u'bar'))

    def test_communicate_universal_newlines(self):
        Popen = MockPopen()
        Popen.set_command('a command', stdout=b'foo', stderr=b'bar')
        # usage
        process = Popen('a command', stdout=PIPE, stderr=PIPE, universal_newlines=True)
        actual = process.communicate()
        # check
        compare(actual, expected=(u'foo', u'bar'))

    def test_communicate_encoding(self):
        Popen = MockPopen()
        Popen.set_command('a command', stdout=b'foo', stderr=b'bar')
        # usage
        process = Popen('a command', stdout=PIPE, stderr=PIPE, encoding='ascii')
        actual = process.communicate()
        # check
        compare(actual, expected=(u'foo', u'bar'))

    def test_communicate_encoding_with_errors(self):
        Popen = MockPopen()
        Popen.set_command('a command', stdout=b'\xa3', stderr=b'\xa3')
        # usage
        process = Popen('a command', stdout=PIPE, stderr=PIPE, encoding='ascii', errors='ignore')
        actual = process.communicate()
        # check
        compare(actual, expected=(u'', u''))

    def test_read_from_stdout_and_stderr_text_mode(self):
        Popen = MockPopen()
        Popen.set_command('a command', stdout=b'foo', stderr=b'bar')
        # usage
        process = Popen('a command', stdout=PIPE, stderr=PIPE, text=True)
        actual = process.stdout.read(), process.stderr.read()
        # check
        compare(actual, expected=(u'foo', u'bar'))

    def test_write_to_stdin(self):
        # setup
        Popen = MockPopen()
        Popen.set_command('a command')
        # usage
        process = Popen('a command', stdin=PIPE, shell=True)
        process.stdin.write('some text')
        # test call list
        compare(Popen.mock.method_calls, expected=[
            call.Popen('a command', shell=True, stdin=PIPE),
            call.Popen_instance.stdin.write('some text'),
        ])
        compare(Popen.all_calls, expected=[
            call.Popen('a command', shell=True, stdin=PIPE),
            call.Popen('a command', shell=True, stdin=PIPE).stdin.write('some text'),
        ])
        compare(process.mock.method_calls, expected=[
            call.stdin.write('some text'),
        ])
        compare(process.calls, expected=[
            call.stdin.write('some text'),
        ])
        repr(call.stdin.write('some text'))

    def test_wait_and_return_code(self):
        # setup
        Popen = MockPopen()
        Popen.set_command('a command', returncode=3)
        # usage
        process = Popen('a command')
        compare(process.returncode, None)
        # result checking
        compare(process.wait(), 3)
        compare(process.returncode, 3)
        # test call list
        compare([
                call.Popen('a command'),
                call.Popen_instance.wait(),
                ], Popen.mock.method_calls)

    def test_wait_timeout(self):
        Popen = MockPopen()
        Popen.set_command('a command', returncode=3)
        process = Popen('a command')
        process.wait(timeout=1)
        process.wait(1)
        compare([
            call.Popen('a command'),
            call.Popen_instance.wait(timeout=1),
            call.Popen_instance.wait(1)
        ], expected=Popen.mock.method_calls)

    def test_multiple_uses(self):
        Popen = MockPopen()
        Popen.set_command('a command', b'a')
        Popen.set_command('b command', b'b')
        process = Popen('a command', stdout=PIPE, stderr=PIPE, shell=True)
        out, err = process.communicate('foo')
        compare(out, b'a')
        process = Popen(['b', 'command'], stdout=PIPE, stderr=PIPE, shell=True)
        out, err = process.communicate('foo')
        compare(out, b'b')
        compare([
                call.Popen('a command', shell=True, stderr=-1, stdout=-1),
                call.Popen_instance.communicate('foo'),
                call.Popen(['b', 'command'], shell=True, stderr=-1, stdout=-1),
                call.Popen_instance.communicate('foo'),
                ], Popen.mock.method_calls)

    def test_send_signal(self):
        # setup
        Popen = MockPopen()
        Popen.set_command('a command')
        # usage
        process = Popen('a command', stdout=PIPE, stderr=PIPE, shell=True)
        process.send_signal(0)
        # result checking
        compare([
                call.Popen('a command', shell=True, stderr=-1, stdout=-1),
                call.Popen_instance.send_signal(0),
                ], Popen.mock.method_calls)

    def test_terminate(self):
        # setup
        Popen = MockPopen()
        Popen.set_command('a command')
        # usage
        process = Popen('a command', stdout=PIPE, stderr=PIPE, shell=True)
        process.terminate()
        # result checking
        compare([
                call.Popen('a command', shell=True, stderr=-1, stdout=-1),
                call.Popen_instance.terminate(),
                ], Popen.mock.method_calls)

    def test_kill(self):
        # setup
        Popen = MockPopen()
        Popen.set_command('a command')
        # usage
        process = Popen('a command', stdout=PIPE, stderr=PIPE, shell=True)
        process.kill()
        # result checking
        compare([
                call.Popen('a command', shell=True, stderr=-1, stdout=-1),
                call.Popen_instance.kill(),
                ], Popen.mock.method_calls)

    def test_all_signals(self):
        # setup
        Popen = MockPopen()
        Popen.set_command('a command')
        # usage
        process = Popen('a command')
        process.send_signal(signal.SIGINT)
        process.terminate()
        process.kill()
        # test call list
        compare([
                call.Popen('a command'),
                call.Popen_instance.send_signal(signal.SIGINT),
                call.Popen_instance.terminate(),
                call.Popen_instance.kill(),
                ], Popen.mock.method_calls)

    def test_poll_no_setup(self):
        # setup
        Popen = MockPopen()
        Popen.set_command('a command')
        # usage
        process = Popen('a command', stdout=PIPE, stderr=PIPE, shell=True)
        compare(process.poll(), None)
        compare(process.poll(), None)
        compare(process.wait(), 0)
        compare(process.poll(), 0)
        # result checking
        compare([
                call.Popen('a command', shell=True, stderr=-1, stdout=-1),
                call.Popen_instance.poll(),
                call.Popen_instance.poll(),
                call.Popen_instance.wait(),
                call.Popen_instance.poll(),
                ], Popen.mock.method_calls)

    def test_poll_setup(self):
        # setup
        Popen = MockPopen()
        Popen.set_command('a command', poll_count=1)
        # usage
        process = Popen('a command', stdout=PIPE, stderr=PIPE, shell=True)
        compare(process.poll(), None)
        compare(process.poll(), 0)
        compare(process.wait(), 0)
        compare(process.poll(), 0)
        # result checking
        compare([
                call.Popen('a command', shell=True, stderr=-1, stdout=-1),
                call.Popen_instance.poll(),
                call.Popen_instance.poll(),
                call.Popen_instance.wait(),
                call.Popen_instance.poll(),
                ], Popen.mock.method_calls)

    def test_poll_until_result(self):
        # setup
        Popen = MockPopen()
        Popen.set_command('a command', returncode=3, poll_count=2)
        # example usage
        process = Popen('a command')
        while process.poll() is None:
            # you'd probably have a sleep here, or go off and
            # do some other work.
            pass
        # result checking
        compare(process.returncode, 3)
        compare([
                call.Popen('a command'),
                call.Popen_instance.poll(),
                call.Popen_instance.poll(),
                call.Popen_instance.poll(),
                ], Popen.mock.method_calls)

    def test_command_not_specified(self):
        Popen = MockPopen()
        with ShouldRaise(KeyError(
            "Nothing specified for command 'a command'"
        )):
            Popen('a command', stdout=PIPE, stderr=PIPE, shell=True)

    def test_default_command_min_args(self):
        # setup
        Popen = MockPopen()
        Popen.set_default()
        # usage
        process = Popen('a command', stdout=PIPE, stderr=PIPE)
        # process started, no return code
        compare(process.pid, 1234)
        compare(None, process.returncode)

        out, err = process.communicate()

        # test the rest
        compare(out, b'')
        compare(err, b'')
        compare(process.returncode, 0)
        # test call list
        compare([
            call.Popen('a command', stderr=-1, stdout=-1),
            call.Popen_instance.communicate(),
        ], Popen.mock.method_calls)

    def test_default_command_max_args(self):
        Popen = MockPopen()
        Popen.set_default(b'out', b'err', 1, 345)

        process = Popen('a command', stdout=PIPE, stderr=PIPE)
        compare(process.pid, 345)
        compare(None, process.returncode)

        out, err = process.communicate()

        # test the rest
        compare(out, b'out')
        compare(err, b'err')
        compare(process.returncode, 1)
        # test call list
        compare([
            call.Popen('a command', stderr=-1, stdout=-1),
            call.Popen_instance.communicate(),
        ], Popen.mock.method_calls)

    def test_invalid_parameters(self):
        message = "MockPopenInstance.__init__() got an unexpected keyword argument 'foo'"
        Popen = MockPopen()
        Popen.set_command('a command')
        with ShouldRaise(TypeError(message)):
            Popen('a command', foo='bar')

    def test_invalid_method_or_attr(self):
        Popen = MockPopen()
        Popen.set_command('command')
        process = Popen('command')
        with ShouldRaise(AttributeError):
            process.foo()

    def test_invalid_attribute(self):
        Popen = MockPopen()
        Popen.set_command('command')
        process = Popen('command')
        with ShouldRaise(AttributeError):
            process.foo

    def test_invalid_communicate_call(self):
        message = "MockPopenInstance.communicate() got an unexpected keyword argument 'foo'"
        Popen = MockPopen()
        Popen.set_command('bar')
        process = Popen('bar')
        with ShouldRaise(TypeError(message)):
            process.communicate(foo='bar')

    def test_invalid_wait_call(self):
        message = "MockPopenInstance.wait() got an unexpected keyword argument 'foo'"
        Popen = MockPopen()
        Popen.set_command('bar')
        process = Popen('bar')
        with ShouldRaise(TypeError(message)):
            process.wait(foo='bar')

    def test_invalid_send_signal(self):
        message = "MockPopenInstance.send_signal() got an unexpected keyword argument 'foo'"
        Popen = MockPopen()
        Popen.set_command('bar')
        process = Popen('bar')
        with ShouldRaise(TypeError(message)):
            process.send_signal(foo='bar')

    def test_invalid_terminate(self):
        message = "MockPopenInstance.terminate() got an unexpected keyword argument 'foo'"
        Popen = MockPopen()
        Popen.set_command('bar')
        process = Popen('bar')
        with ShouldRaise(TypeError(message)):
            process.terminate(foo='bar')

    def test_invalid_kill(self):
        Popen = MockPopen()
        Popen.set_command('bar')
        process = Popen('bar')
        text = 'MockPopenInstance.kill() takes 1 positional argument but 2 were given'
        with ShouldRaise(TypeError(text)):
            process.kill('moo')

    def test_invalid_poll(self):
        Popen = MockPopen()
        Popen.set_command('bar')
        process = Popen('bar')
        text = 'MockPopenInstance.poll() takes 1 positional argument but 2 were given'
        with ShouldRaise(TypeError(text)):
            process.poll('moo')

    def test_non_pipe(self):
        # setup
        Popen = MockPopen()
        Popen.set_command('a command')
        # usage
        process = Popen('a command')
        # checks
        compare(process.stdout, expected=None)
        compare(process.stderr, expected=None)
        out, err = process.communicate()
        # test the rest
        compare(out, expected=None)
        compare(err, expected=None)
        # test call list
        compare([
                call.Popen('a command'),
                call.Popen_instance.communicate(),
                ], Popen.mock.method_calls)

    def test_use_as_context_manager(self):
        # setup
        Popen = MockPopen()
        Popen.set_command('a command')
        # usage
        with Popen('a command', stdout=PIPE, stderr=PIPE) as process:
            # process started, no return code
            compare(process.pid, 1234)
            compare(None, process.returncode)

            out, err = process.communicate()

        # test the rest
        compare(out, b'')
        compare(err, b'')
        compare(process.returncode, 0)

        compare(process.stdout.closed, expected=True)
        compare(process.stderr.closed, expected=True)

        # test call list
        compare([
            call.Popen('a command', stderr=-1, stdout=-1),
            call.Popen_instance.communicate(),
            call.Popen_instance.wait(),
        ], Popen.mock.method_calls)

    def test_start_new_session(self):
        # setup
        Popen = MockPopen()
        Popen.set_command('a command')
        # usage
        Popen('a command', start_new_session=True)
        # test call list
        compare([
            call.Popen('a command', start_new_session=True),
        ], Popen.mock.method_calls)

    def test_simultaneous_processes(self):
        Popen = MockPopen()
        Popen.set_command('a command', b'a', returncode=1)
        Popen.set_command('b command', b'b', returncode=2)
        process_a = Popen('a command', stdout=PIPE, stderr=PIPE, shell=True)
        process_b = Popen(['b', 'command'], stdout=PIPE, stderr=PIPE, shell=True)
        compare(process_a.wait(), expected=1)
        compare(process_b.wait(), expected=2)
        a_call = call.Popen('a command', stdout=PIPE, stderr=PIPE, shell=True)
        b_call = call.Popen(['b', 'command'], stdout=PIPE, stderr=PIPE, shell=True)
        compare(Popen.all_calls, expected=[
                a_call,
                b_call,
                a_call.wait(),
                b_call.wait(),
        ])
        compare(process_a.mock.method_calls, expected=[
            call.wait()
        ])
        compare(process_b.mock.method_calls, expected=[
            call.wait()
        ])

    def test_pass_executable(self):
        Popen = MockPopen()
        Popen.set_command('a command', b'a', returncode=1)
        Popen('a command', executable='/foo/bar')
        compare(Popen.all_calls, expected=[
            call.Popen('a command', executable='/foo/bar')
        ])

    def test_set_command_with_list(self):
        Popen = MockPopen()
        Popen.set_command(['a', 'command'])
        Popen(['a', 'command'], stdout=PIPE, stderr=PIPE)
        compare([call.Popen(['a',  'command'], stderr=-1, stdout=-1)],
                actual=Popen.all_calls)


class TestRaises:

    def test_communicate(self):
        Popen = MockPopen()
        exception = subprocess.TimeoutExpired(cmd='a command', timeout=5)
        Popen.set_command('a command', raises=Raises(communicate=exception))
        process = Popen('a command')
        with ShouldRaise(exception):
            process.communicate()

    def test_wait(self):
        Popen = MockPopen()
        exception = subprocess.TimeoutExpired(cmd='a command', timeout=5)
        Popen.set_command('a command', raises=Raises(wait=exception))
        process = Popen('a command')
        with ShouldRaise(exception):
            process.wait()

    def test_send_signal(self):
        Popen = MockPopen()
        exception = ProcessLookupError('no such process')
        Popen.set_command('a command', raises=Raises(send_signal=exception))
        process = Popen('a command')
        with ShouldRaise(exception):
            process.send_signal(signal.SIGTERM)

    def test_terminate(self):
        Popen = MockPopen()
        exception = ProcessLookupError('no such process')
        Popen.set_command('a command', raises=Raises(terminate=exception))
        process = Popen('a command')
        with ShouldRaise(exception):
            process.terminate()

    def test_kill(self):
        Popen = MockPopen()
        exception = ProcessLookupError('no such process')
        Popen.set_command('a command', raises=Raises(kill=exception))
        process = Popen('a command')
        with ShouldRaise(exception):
            process.kill()

    def test_via_set_default(self):
        Popen = MockPopen()
        exception = subprocess.TimeoutExpired(cmd='a command', timeout=5)
        Popen.set_default(raises=Raises(communicate=exception))
        process = Popen('a command')
        with ShouldRaise(exception):
            process.communicate()

    def test_call_still_recorded(self):
        Popen = MockPopen()
        exception = subprocess.TimeoutExpired(cmd='a command', timeout=5)
        Popen.set_command('a command', raises=Raises(communicate=exception))
        process = Popen('a command')
        with ShouldRaise(exception):
            process.communicate()
        compare(Popen.all_calls, expected=[
            call.Popen('a command'),
            call.Popen('a command').communicate(),
        ])

    def test_cleanup_after_communicate_raises(self):
        # mirrors subprocess.run's except TimeoutExpired: process.kill(); process.wait()
        Popen = MockPopen()
        exception = subprocess.TimeoutExpired(cmd='a command', timeout=5)
        Popen.set_command('a command', returncode=-9, raises=Raises(communicate=exception))
        process = Popen('a command')
        with ShouldRaise(exception):
            process.communicate()
        process.kill()
        compare(process.wait(), expected=-9)


class IntegrationTests(TestCase):

    def setUp(self):
        self.popen = MockPopen()
        replacer = Replacer()
        replacer.replace('tests.test_popen.subprocess.Popen', self.popen)
        self.addCleanup(replacer.restore)

    def test_command_called_with_check_call_check_returncode(self):
        self.popen.set_command('ls')
        compare(0, subprocess.check_call(['ls']))

    def test_command_called_with_check_output_check_stdout_returned(self):
        self.popen.set_command('ls', stdout=b'abc')
        compare(b'abc', subprocess.check_output(['ls']))

    def test_command_called_with_check_output_stderr_to_stdout_check_returned(self):
        self.popen.set_command('ls', stderr=b'xyz')
        compare(b'xyz', subprocess.check_output(['ls'], stderr=STDOUT))

    def test_command_called_with_check_call_failing_command_check_exception(self):
        self.popen.set_command('ls', returncode=1)
        with self.assertRaises(subprocess.CalledProcessError):
            subprocess.check_output(['ls'])

    def test_command_called_with_check_output_passthrough_for_other_commands(self):
        self.popen.set_command('ls', stdout=b'mocked')
        self.popen.set_default(behaviour=Passthrough())

        compare(b'mocked', subprocess.check_output(['ls']))

        real_cmd = [sys.executable, '-c', 'import sys; sys.stdout.write("real")']
        compare('real', subprocess.check_output(real_cmd, text=True))


class TestPassthrough:

    def test_command(self):
        Popen = MockPopen()
        cmd = [sys.executable, '-c', 'import sys; sys.stdout.write("out"); sys.stderr.write("err")']
        Popen.set_command(cmd, behaviour=Passthrough())
        process = Popen(cmd, stdout=PIPE, stderr=PIPE, text=True)
        out, err = process.communicate()
        compare(out, expected='out')
        compare(err, expected='err')
        compare(process.returncode, expected=0)
        process_call = call.Popen(cmd, stdout=PIPE, stderr=PIPE, text=True)
        compare(Popen.all_calls, expected=[
            process_call,
            process_call.communicate(),
        ])

    def test_default(self):
        Popen = MockPopen()
        Popen.set_command('mocked command', stdout=b'mocked out')
        Popen.set_default(behaviour=Passthrough())

        mocked = Popen('mocked command', stdout=PIPE)
        compare(mocked.communicate()[0], expected=b'mocked out')

        cmd = [sys.executable, '-c', 'import sys; sys.stdout.write("real out")']
        real = Popen(cmd, stdout=PIPE, text=True)
        out, _ = real.communicate()
        compare(out, expected='real out')

        mocked_call = call.Popen('mocked command', stdout=PIPE)
        real_call = call.Popen(cmd, stdout=PIPE, text=True)
        compare(Popen.all_calls, expected=[
            mocked_call,
            mocked_call.communicate(),
            real_call,
            real_call.communicate(),
        ])

    def test_returncode(self):
        Popen = MockPopen()
        cmd = [sys.executable, '-c', 'import sys; sys.exit(3)']
        Popen.set_command(cmd, behaviour=Passthrough())
        process = Popen(cmd)
        process.wait()
        compare(process.returncode, expected=3)
        compare(Popen.all_calls, expected=[
            call.Popen(cmd),
            call.Popen(cmd).wait(),
        ])

    def test_stdin(self):
        Popen = MockPopen()
        cmd = [sys.executable, '-c', 'import sys; sys.stdout.write(sys.stdin.read().upper())']
        Popen.set_command(cmd, behaviour=Passthrough())
        process = Popen(cmd, stdin=PIPE, stdout=PIPE, text=True)
        out, _ = process.communicate('hello')
        compare(out, expected='HELLO')
        process_call = call.Popen(cmd, stdin=PIPE, stdout=PIPE, text=True)
        compare(Popen.all_calls, expected=[
            process_call,
            process_call.communicate('hello'),
        ])

    def test_terminate(self):
        Popen = MockPopen()
        cmd = [sys.executable, '-c', 'import time; time.sleep(10)']
        Popen.set_command(cmd, behaviour=Passthrough())
        process = Popen(cmd)
        process.terminate()
        process.wait()
        compare(process.returncode, expected=-signal.SIGTERM)
        compare(Popen.all_calls, expected=[
            call.Popen(cmd),
            call.Popen(cmd).terminate(),
            call.Popen(cmd).wait(),
        ])

    def test_kill(self):
        Popen = MockPopen()
        cmd = [sys.executable, '-c', 'import time; time.sleep(10)']
        Popen.set_command(cmd, behaviour=Passthrough())
        process = Popen(cmd)
        process.kill()
        process.wait()
        compare(process.returncode, expected=-signal.SIGKILL)
        compare(Popen.all_calls, expected=[
            call.Popen(cmd),
            call.Popen(cmd).kill(),
            call.Popen(cmd).wait(),
        ])

    def test_send_signal(self):
        Popen = MockPopen()
        cmd = [sys.executable, '-c', 'import time; time.sleep(10)']
        Popen.set_command(cmd, behaviour=Passthrough())
        process = Popen(cmd)
        process.send_signal(0)
        process.kill()
        process.wait()
        compare(Popen.all_calls, expected=[
            call.Popen(cmd),
            call.Popen(cmd).send_signal(0),
            call.Popen(cmd).kill(),
            call.Popen(cmd).wait(),
        ])

    def test_use_as_context_manager(self):
        Popen = MockPopen()
        cmd = [sys.executable, '-c', 'import sys; sys.stdout.write("out")']
        Popen.set_command(cmd, behaviour=Passthrough())
        with Popen(cmd, stdout=PIPE, text=True) as process:
            out = process.stdout.read()
        compare(out, expected='out')
        compare(process.stdout.closed, expected=True)
        process_call = call.Popen(cmd, stdout=PIPE, text=True)
        compare(Popen.all_calls, expected=[
            process_call,
            process_call.wait(),
        ])

    def test_use_as_context_manager_closes_stdin(self):
        Popen = MockPopen()
        cmd = [sys.executable, '-c', 'import sys; sys.exit(0)']
        Popen.set_command(cmd, behaviour=Passthrough())
        with Popen(cmd, stdin=PIPE) as process:
            pass
        compare(process.stdin.closed, expected=True)
        process_call = call.Popen(cmd, stdin=PIPE)
        compare(Popen.all_calls, expected=[
            process_call,
            process_call.wait(),
        ])
