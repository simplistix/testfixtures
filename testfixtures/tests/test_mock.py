from testfixtures.mock import Mock, call

from .test_compare import CompareHelper

class TestCall(CompareHelper):

    def test_non_root_call_not_equal(self):
        self.check_raises(
            call.foo().bar(),
            call.baz().bar(),
            '\n'
            "'call.foo().bar()'\n"
            '!=\n'
            "'call.baz().bar()'"
        )

    def test_non_root_attr_not_equal(self):
        self.check_raises(
            call.foo.bar(),
            call.baz.bar(),
            '\n'
            "'call.foo.bar()'\n"
            '!=\n'
            "'call.baz.bar()'"
        )

    def test_non_root_params_not_equal(self):
        self.check_raises(
            call.foo(x=1).bar(),
            call.foo(x=2).bar(),
            '\n'
            "'call.foo(x=1)'\n"
            '!=\n'
            "'call.foo(x=2)'"
        )

class TestMock(CompareHelper):

    def test_non_root_call_not_equal(self):
        m = Mock()
        m.foo().bar()
        self.check_raises(
            m.mock_calls[-1],
            call.baz().bar(),
            '\n'
            "'call.foo().bar()'\n"
            '!=\n'
            "'call.baz().bar()'"
        )

    def test_non_root_attr_not_equal(self):
        m = Mock()
        m.foo.bar()
        self.check_raises(
            m.mock_calls[-1],
            call.baz.bar(),
            '\n'
            "'call.foo.bar()'\n"
            '!=\n'
            "'call.baz.bar()'"
        )
