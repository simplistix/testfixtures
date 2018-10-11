# NB: This file is used in the documentation, if you make changes, ensure
#     you update the line numbers in popen.txt!

from subprocess import Popen, PIPE


def my_func():
    process = Popen('svn ls -R foo', stdout=PIPE, stderr=PIPE, shell=True)
    out, err = process.communicate()
    if process.returncode:
        raise RuntimeError('something bad happened')
    return (process, out)

dotted_path = 'testfixtures.tests.test_popen_docs.Popen'

from unittest import TestCase

from .mock import call
from testfixtures import Replacer, ShouldRaise, compare
from testfixtures.popen import MockPopen, PopenBehaviour


class TestMyFunc(TestCase):

    def setUp(self):
        self.Popen = MockPopen()
        self.r = Replacer()
        self.r.replace(dotted_path, self.Popen)
        self.addCleanup(self.r.restore)

    def test_example(self):
        # set up
        self.Popen.set_command('svn ls -R foo', stdout=b'o', stderr=b'e')

        # testing of results
        (process, out) = my_func()
        compare(out, b'o')

        # testing calls were in the right order and with the correct parameters:
        compare([
            call.Popen('svn ls -R foo',
                       shell=True, stderr=PIPE, stdout=PIPE),
            ], Popen.mock.method_calls)
        compare([
            call.communicate()
            ], process.method_calls)

    def test_example_bad_returncode(self):
        # set up
        Popen.set_command('svn ls -R foo', stdout=b'o', stderr=b'e',
                          returncode=1)

        # testing of error
        with ShouldRaise(RuntimeError('something bad happened')):
            my_func()

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
                ], Popen.mock.method_calls)
        compare([
                call.communicate('foo')
                ], process.method_calls)

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

    def test_write_to_stdin(self):
        # setup
        Popen = MockPopen()
        Popen.set_command('a command')
        # usage
        process = Popen('a command', stdin=PIPE, shell=True)
        process.stdin.write('some text')
        process.stdin.close()
        # test call list
        compare([
                call.Popen('a command', shell=True, stdin=PIPE),
                ], Popen.mock.method_calls)
        compare([
                call.stdin.write('some text'),
                call.stdin.close()
                ], process.method_calls)

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
                ], Popen.mock.method_calls)
        compare([
                call.wait(),
                ], process.method_calls)

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
                ], Popen.mock.method_calls)
        compare([
                call.send_signal(0)
                ], process.method_calls)

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
                ], Popen.mock.method_calls)
        compare([
                call.poll(),
                call.poll(),
                call.poll()
                ], process.method_calls)

    def test_default_behaviour(self):
        # set up
        self.Popen.set_default(stdout=b'o', stderr=b'e')

        # testing of results
        (process, out) = my_func()
        compare(out, b'o')

        # testing calls were in the right order and with the correct parameters:
        compare([
            call.Popen('svn ls -R foo',
                       shell=True, stderr=PIPE, stdout=PIPE),
            ], Popen.mock.method_calls)
        compare([
            call.communicate()
            ], process.method_calls)

    def test_callable(self):
        # set up
        def command_callable(command, stdin):
            return PopenBehaviour(stdout=b'stdout')
        self.Popen.set_default(behaviour=command_callable)

        # testing of results
        (process, out) = my_func()
        compare(out, b'stdout')

        # testing calls were in the right order and with the correct parameters:
        compare([
            call.Popen('svn ls -R foo',
                       shell=True, stderr=PIPE, stdout=PIPE),
        ], Popen.mock.method_calls)
        compare([
            call.communicate()
        ], process.method_calls)

    def test_multiple_responses(self):
        # set up
        behaviours = [
            PopenBehaviour(stderr=b'e', returncode=1),
            PopenBehaviour(stdout=b'o'),
        ]

        def behaviour(command, stdin):
            return behaviours.pop(0)

        self.Popen.set_command('svn ls -R foo', behaviour=behaviour)

        # testing of error:
        with ShouldRaise(RuntimeError('something bad happened')):
            my_func()
        # testing of second call:
        compare(my_func()[1], b'o')

    def test_count_down(self):
        # set up
        self.Popen.set_command('svn ls -R foo', behaviour=CustomBehaviour())
        # testing of error:
        with ShouldRaise(RuntimeError('something bad happened')):
            my_func()
        # testing of second call:
        compare(my_func()[1], b'o')


class CustomBehaviour(object):

    def __init__(self, fail_count=1):
        self.fail_count = fail_count

    def __call__(self, command, stdin):
        while self.fail_count > 0:
            self.fail_count -= 1
            return PopenBehaviour(stderr=b'e', returncode=1)
        return PopenBehaviour(stdout=b'o')
