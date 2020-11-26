"""
Tools for helping to test Twisted applications.
"""
from __future__ import absolute_import

from pprint import pformat

from . import compare
from twisted.logger import globalLogPublisher, formatEvent, LogLevel


class LogCapture(object):
    """
    A helper for capturing stuff logged using Twisted's loggers.

    :param fields:
      A sequence of field names that :meth:`~LogCapture.check` will use to build
      "actual" events to compare against the expected events passed in.
      If items are strings, they will be treated as keys info the Twisted logging event.
      If they are callable, they will be called with the event as their only parameter.
      If only one field is specified, "actual" events will just be that one field;
      otherwise they will be a tuple of the specified fields.
    """

    def __init__(self, fields=('log_level', formatEvent,)):
        #: The list of events captured.
        self.events = []
        self.fields = fields

    def __call__(self, event):
        self.events.append(event)

    def install(self):
        "Start capturing."
        self.original_observers = globalLogPublisher._observers
        globalLogPublisher._observers = [self]

    def uninstall(self):
        "Stop capturing."
        globalLogPublisher._observers = self.original_observers

    def check(self, *expected, **kw):
        """
        Check captured events against those supplied. Please see the ``fields`` parameter
        to the constructor to see how "actual" events are built.

        :param order_matters:
          This defaults to ``True``. If ``False``, the order of expected logging versus
          actual logging will be ignored.
        """
        order_matters = kw.pop('order_matters', True)
        assert not kw, 'order_matters is the only keyword parameter'
        actual = []
        for event in self.events:
            actual_event = tuple(field(event) if callable(field) else event.get(field)
                            for field in self.fields)
            if len(actual_event) == 1:
                actual_event = actual_event[0]
            actual.append(actual_event)
        if order_matters:
            compare(expected=expected, actual=actual)
        else:
            expected = list(expected)
            matched = []
            unmatched = []
            for entry in actual:
                try:
                    index = expected.index(entry)
                except ValueError:
                    unmatched.append(entry)
                else:
                    matched.append(expected.pop(index))
            if expected:
                raise AssertionError((
                    'entries not as expected:\n\n'
                    'expected and found:\n%s\n\n'
                    'expected but not found:\n%s\n\n'
                    'other entries:\n%s'
                ) % (pformat(matched), pformat(expected), pformat(unmatched)))

    def check_failure_text(self, expected, index=-1, attribute='value'):
        """
        Check the string representation of an attribute of a logged :class:`Failure` is as expected.

        :param expected: The expected string representation.
        :param index: The index into :attr:`events` where the failure should have been logged.
        :param attribute: The attribute of the failure of which to find the string representation.
        """
        compare(expected, actual=str(getattr(self.events[index]['log_failure'], attribute)))

    def raise_logged_failure(self, start_index=0):
        """
        A debugging tool that raises the first failure encountered in captured logging.

        :param start_index: The index into :attr:`events` from where to start looking for failures.
        """
        for event in self.events[start_index:]:
            failure = event.get('log_failure')
            if failure:
                raise failure

    @classmethod
    def make(cls, testcase, **kw):
        """
        Instantiate, install and add a cleanup for a :class:`LogCapture`.

        :param testcase: This must be an instance of :class:`twisted.trial.unittest.TestCase`.
        :param kw: Any other parameters are passed directly to the :class:`LogCapture` constructor.
        :return: The :class:`LogCapture` instantiated by this method.
        """
        capture = cls(**kw)
        capture.install()
        testcase.addCleanup(capture.uninstall)
        return capture


#: Short reference to Twisted's ``LogLevel.debug``
DEBUG = LogLevel.debug
#: Short reference to Twisted's ``LogLevel.info``
INFO = LogLevel.info
#: Short reference to Twisted's ``LogLevel.warn``
WARN = LogLevel.warn
#: Short reference to Twisted's ``LogLevel.error``
ERROR = LogLevel.error
#: Short reference to Twisted's ``LogLevel.critical``
CRITICAL = LogLevel.critical
