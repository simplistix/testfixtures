"""
A mock for Popen that records what was called and when and behaves as it's instructed

Example usage:

.. code-block:: python

    # test setup
    Popen = MockPopen()
    Popen.setCommand('svn ls -R foo', stdout='ff', stderr='ee', returncode=0)
    self.r.replace('blah', Popen)

    # code under test
    def my_func():
        process = Popen('a command', stdout=PIPE, stderr=PIPE, shell=True)
        out, err = process.communicate()
        if process.returncode:
            raise RuntimeError('something bad happened')
        return out

    # testing of results
    compare(my_func(), 'ff')
    # testing calls were in the right order and with the correct params:
    compare([
         call.Popen('svn ls -R foo', shell=True, stderr=-1, stdout=-1)
         call.Popen_instance.communicate()
         ], Popen.mock.method_calls)

.. note:: Accessing ``.stdin`` isn't current supported by this mock.

For more detailed examples, see ``tests/test_popen.py``
"""
from mock import Mock
from subprocess import Popen as Popen
from tempfile import TemporaryFile

class MockPopen(object):

    def __init__(self):
        self.commands = {}
        self.mock = mock = Mock()
        self.mock.Popen.side_effect = self.Popen
        mock.Popen_instance = Mock(spec=Popen)
        inst = mock.Popen.return_value =  mock.Popen_instance 
        inst.communicate.side_effect = self.communicate
        inst.wait.side_effect = self.wait
        inst.send_signal.side_effect = self.send_signal
        inst.terminate.side_effect = self.terminate
        inst.kill.side_effect = self.kill
        inst.poll.side_effect = self.poll
        
    def setCommand(self, command, stdout='', stderr='', returncode=0, pid=1234,
                   poll_count=3):
        self.commands[command] = (stdout, stderr, returncode, pid, poll_count)

    def __call__(self, *args, **kw):
        return self.mock.Popen(*args, **kw)

    def Popen(self, args, bufsize=0, executable=None,
               stdin=None, stdout=None, stderr=None,
               preexec_fn=None, close_fds=False, shell=False, cwd=None,
               env=None, universal_newlines=False,
               startupinfo=None, creationflags=0):

        if isinstance(args, basestring):
            cmd = args
        else:
            cmd = ' '.join(args)

        if cmd not in self.commands:
            raise KeyError('Nothing specified for command %r' % cmd)
        
        self.stdout, self.stderr, self.returncode, pid, poll = self.commands[cmd]
        self.poll_count = poll
        for name in 'stdout', 'stderr':
            f = TemporaryFile()
            f.write(getattr(self, name))
            f.flush()
            f.seek(0)
            setattr(self.mock.Popen_instance, name, f)
            
        self.mock.Popen_instance.pid = pid
        self.mock.Popen_instance.returncode = None
        
        return self.mock.Popen_instance

    def wait(self):
        self.mock.Popen_instance.returncode = self.returncode
        return self.returncode

    def communicate(self, input=None):
        self.wait()
        return self.stdout, self.stderr

    def poll(self):
        while self.poll_count and self.mock.Popen_instance.returncode is None:
            self.poll_count -= 1
            return None
        # This call to wait() is NOT how poll() behaves in reality.
        # poll() NEVER sets the returncode.
        # The returncode is *only* ever set by process completion.
        # The following is an artifact of the fixture's implementation.
        return self.wait()

    # These are here to check parameter types
    def send_signal(self, signal):
        pass
    def terminate(self):
        pass
    def kill(self):
        pass

