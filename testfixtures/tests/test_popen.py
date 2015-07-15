from subprocess import PIPE
from unittest import TestCase

from mock import call
from testfixtures import ShouldRaise, compare

from ..popen import MockPopen

class Tests(TestCase):

    def test_command_min_args(self):
        # setup
        Popen = MockPopen()
        Popen.setCommand('a command')
        # usage
        process = Popen('a command', stdout=PIPE, stderr=PIPE)
        # process started, no return code
        compare(process.pid, 1234)
        compare(None, process.returncode)
        
        out, err = process.communicate()

        # test the rest
        compare(out, '')
        compare(err, '')
        compare(process.returncode, 0)
        # test call list
        compare([
                call.Popen('a command', stderr=-1, stdout=-1),
                call.Popen_instance.communicate(),
                ], Popen.mock.method_calls)

    def test_command_max_args(self):

        Popen = MockPopen()
        Popen.setCommand('a command', 'out', 'err', 1, 345)
        
        process = Popen('a command', stdout=PIPE, stderr=PIPE)
        compare(process.pid, 345)
        compare(None, process.returncode)
        
        out, err = process.communicate()

        # test the rest
        compare(out, 'out')
        compare(err, 'err')
        compare(process.returncode, 1)
        # test call list
        compare([
                call.Popen('a command', stderr=-1, stdout=-1),
                call.Popen_instance.communicate(),
                ], Popen.mock.method_calls)

    def test_command_is_sequence(self):
        Popen = MockPopen()
        Popen.setCommand('a command')
        
        process = Popen(['a', 'command'], stdout=PIPE, stderr=PIPE)
        
        compare(process.wait(), 0)
        compare([
                call.Popen(['a', 'command'], stderr=-1, stdout=-1),
                call.Popen_instance.wait(),
                ], Popen.mock.method_calls)

    def test_communicate_with_input(self):
        # setup
        Popen = MockPopen()
        Popen.setCommand('a command')
        # usage
        process = Popen('a command', stdout=PIPE, stderr=PIPE, shell=True)
        out, err = process.communicate('foo')
        # test call list
        compare([
                call.Popen('a command', shell=True, stderr=-1, stdout=-1),
                call.Popen_instance.communicate('foo'),
                ], Popen.mock.method_calls)
    
    def test_read_from_stdout(self):
        # setup
        Popen = MockPopen()
        Popen.setCommand('a command', stdout='foo')
        # usage
        process = Popen('a command', stdout=PIPE, stderr=PIPE, shell=True)
        self.assertTrue(isinstance(process.stdout.fileno(), int))
        compare(process.stdout.read(), 'foo')
        # test call list
        compare([
                call.Popen('a command', shell=True, stderr=-1, stdout=-1),
                ], Popen.mock.method_calls)
    
    def test_read_from_stderr(self):
        # setup
        Popen = MockPopen()
        Popen.setCommand('a command', stderr='foo')
        # usage
        process = Popen('a command', stdout=PIPE, stderr=PIPE, shell=True)
        self.assertTrue(isinstance(process.stdout.fileno(), int))
        compare(process.stderr.read(), 'foo')
        # test call list
        compare([
                call.Popen('a command', shell=True, stderr=-1, stdout=-1),
                ], Popen.mock.method_calls)
    
    def test_wait(self):
        # setup
        Popen = MockPopen()
        Popen.setCommand('a command')
        # usage
        process = Popen('a command', stdout=PIPE, stderr=PIPE, shell=True)
        compare(process.pid, 1234)
        compare(None, process.returncode)
        # result checking
        compare(process.wait(), 0)
        compare(process.returncode, 0)
        # test call list
        compare([
                call.Popen('a command', shell=True, stderr=-1, stdout=-1),
                call.Popen_instance.wait(),
                ], Popen.mock.method_calls)
    
    def test_multiple_uses(self):
        Popen = MockPopen()
        Popen.setCommand('a command', 'a')
        Popen.setCommand('b command', 'b')
        process = Popen('a command', stdout=PIPE, stderr=PIPE, shell=True)
        out, err = process.communicate('foo')
        compare(out, 'a')
        process = Popen(['b', 'command'], stdout=PIPE, stderr=PIPE, shell=True)
        out, err = process.communicate('foo')
        compare(out, 'b')
        compare([
                call.Popen('a command', shell=True, stderr=-1, stdout=-1),
                call.Popen_instance.communicate('foo'),
                call.Popen(['b', 'command'], shell=True, stderr=-1, stdout=-1),
                call.Popen_instance.communicate('foo'),
                ], Popen.mock.method_calls)
    
    def test_send_signal(self):
        # setup
        Popen = MockPopen()
        Popen.setCommand('a command')
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
        Popen.setCommand('a command')
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
        Popen.setCommand('a command')
        # usage
        process = Popen('a command', stdout=PIPE, stderr=PIPE, shell=True)
        process.kill()
        # result checking
        compare([
                call.Popen('a command', shell=True, stderr=-1, stdout=-1),
                call.Popen_instance.kill(),
                ], Popen.mock.method_calls)
    
    def test_poll_no_setup(self):
        # setup
        Popen = MockPopen()
        Popen.setCommand('a command')
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
        Popen.setCommand('a command', poll_count=1)
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
        Popen.setCommand('a command', returncode=3)
        # example usage
        process = Popen('a command', stdout=PIPE, stderr=PIPE, shell=True)
        while process.poll() is None:
            # you'd probably have a sleep here, or go off and
            # do some other work.
            pass
        # okay, but the mock should now have its returncode set
        compare(process.returncode, 3)
    
    def test_command_not_specified(self):
        Popen = MockPopen()
        with ShouldRaise(KeyError("Nothing specified for command 'a command'")):
            Popen('a command', stdout=PIPE, stderr=PIPE, shell=True)

    def test_invalid_parameters(self):
        Popen = MockPopen()
        with ShouldRaise(TypeError("Popen() got an unexpected keyword argument 'foo'")):
            Popen(foo='bar')

    def test_invalid_method_or_attr(self):
        Popen = MockPopen()
        Popen.setCommand('command')
        process = Popen('command')
        with ShouldRaise(AttributeError("Mock object has no attribute 'foo'")):
            process.foo()

    def test_invalid_attribute(self):
        Popen = MockPopen()
        Popen.setCommand('command')
        process = Popen('command')
        with ShouldRaise(AttributeError("Mock object has no attribute 'foo'")):
            process.foo
            
    def test_invalid_communicate_call(self):
        Popen = MockPopen()
        Popen.setCommand('bar')
        process = Popen('bar')
        with ShouldRaise(TypeError("communicate() got an unexpected keyword argument 'foo'")):
            process.communicate(foo='bar')
            
    def test_invalid_wait_call(self):
        Popen = MockPopen()
        Popen.setCommand('bar')
        process = Popen('bar')
        with ShouldRaise(TypeError("wait() got an unexpected keyword argument 'foo'")):
            process.wait(foo='bar')

    def test_invalid_send_signal(self):
        Popen = MockPopen()
        Popen.setCommand('bar')
        process = Popen('bar')
        with ShouldRaise(TypeError("send_signal() got an unexpected keyword argument 'foo'")):
            process.send_signal(foo='bar')

    def test_invalid_terminate(self):
        Popen = MockPopen()
        Popen.setCommand('bar')
        process = Popen('bar')
        with ShouldRaise(TypeError("terminate() got an unexpected keyword argument 'foo'")):
            process.terminate(foo='bar')

    def test_invalid_kill(self):
        Popen = MockPopen()
        Popen.setCommand('bar')
        process = Popen('bar')
        with ShouldRaise(TypeError('kill() takes exactly 1 argument (2 given)')):
            process.kill('moo')

    def test_invalid_poll(self):
        Popen = MockPopen()
        Popen.setCommand('bar')
        process = Popen('bar')
        with ShouldRaise(TypeError('poll() takes exactly 1 argument (2 given)')):
            process.poll('moo')
