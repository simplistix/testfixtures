from testfixtures.mock import Mock, call

from .test_compare import CompareHelper

class TestCall(CompareHelper):

    def test_non_root_call_not_equal(self):
        self.check_raises(
            call.foo().bar(),
            call.baz().bar(),
            'mock.call not as expected:\n'
            '\n'
            "While comparing  function name: 'foo().bar' != 'baz().bar'"
        )

    def test_non_root_attr_not_equal(self):
        self.check_raises(
            call.foo.bar(),
            call.baz.bar(),
            'mock.call not as expected:\n'
            '\n'
            "While comparing  function name: 'foo.bar' != 'baz.bar'"
        )

    def test_non_root_params_not_equal(self):
        self.check_raises(
            call.foo(x=1).bar(),
            call.foo(x=2).bar(),
            'mock.call not as expected:'
        )

class TestMock(CompareHelper):

    def test_non_root_call_not_equal(self):
        m = Mock()
        m.foo().bar()
        self.check_raises(
            m.mock_calls[-1],
            call.baz().bar(),
            'mock.call not as expected:\n'
            '\n'
            "While comparing  function name: 'foo().bar' != 'baz().bar'"
        )

    def test_non_root_attr_not_equal(self):
        m = Mock()
        m.foo.bar()
        self.check_raises(
            m.mock_calls[-1],
            call.baz.bar(),
            'mock.call not as expected:\n'
            '\n'
            "While comparing  function name: 'foo.bar' != 'baz.bar'"
        )
