# Copyright (c) 2008-2011 Simplistix Ltd
# See license.txt for license details.

import sys

from cStringIO import StringIO
from testfixtures.comparison import compare

class OutputCapture:
    """
    A context manager for capturing output to the
    :attr:`sys.stdout` and :attr:`sys.stderr` streams.
    """

    original_stdout = None
    original_stderr = None
    
    def __enter__(self):
        self.output = StringIO()
        self.enable()
        return self

    def __exit__(self,*args):
        self.disable()
        
    def disable(self):
        "Disable the output capture if it is enabled."
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        
    def enable(self):
        "Enable the output capture if it is disabled."
        if self.original_stdout is None:
            self.original_stdout = sys.stdout
            self.original_stderr = sys.stderr
        sys.stdout = sys.stderr = self.output
        
    @property
    def captured(self):
        "A property containing any output that has been captured so far."
        return self.output.getvalue()
    
    def compare(self,expected):
        """
        Compare the captured output to that expected. If the output is
        not the same, an :class:`AssertionError` will be raised.

        :param expected: A string containing the expected output.
        """
        compare(expected.strip(),self.captured.strip())

