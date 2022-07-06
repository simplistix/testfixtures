from testfixtures import (
    Replacer,
    Replace,
    ShouldRaise,
    TempDirectory,
    replace,
    compare,
    not_there,
    )
from unittest import TestCase

import os

from testfixtures.tests import sample1
from testfixtures.tests import sample2
from ..compat import PY_310_PLUS

from warnings import catch_warnings


class TestReplace(TestCase):

    def test_function(self):

        def test_z():
            return 'replacement z'

        compare(sample1.z(), 'original z')

        @replace('testfixtures.tests.sample1.z', test_z)
        def test_something():
            compare(sample1.z(), 'replacement z')

        compare(sample1.z(), 'original z')

        test_something()

        compare(sample1.z(), 'original z')

    def test_class(self):

        OriginalX = sample1.X

        class ReplacementX(sample1.X):
            pass

        self.assertFalse(OriginalX is ReplacementX)
        self.assertTrue(isinstance(sample1.X(), OriginalX))

        @replace('testfixtures.tests.sample1.X', ReplacementX)
        def test_something():
            self.assertFalse(OriginalX is ReplacementX)
            self.assertTrue(isinstance(sample1.X(), ReplacementX))

        self.assertFalse(OriginalX is ReplacementX)
        self.assertTrue(isinstance(sample1.X(), OriginalX))

        test_something()

        self.assertFalse(OriginalX is ReplacementX)
        self.assertTrue(isinstance(sample1.X(), OriginalX))

    def test_method(self):

        def test_y(self):
            return self

        compare(sample1.X().y(), 'original y')

        @replace('testfixtures.tests.sample1.X.y', test_y)
        def test_something():
            self.assertTrue(isinstance(sample1.X().y(), sample1.X))

        compare(sample1.X().y(), 'original y')

        test_something()

        compare(sample1.X().y(), 'original y')

    def test_class_method(self):

        def rMethod(cls):
            return (cls, 1)

        compare(sample1.X().aMethod(), sample1.X)

        @replace('testfixtures.tests.sample1.X.aMethod', rMethod)
        def test_something(r):
            compare(r, rMethod)
            compare(sample1.X().aMethod(), (sample1.X, 1))

        compare(sample1.X().aMethod(), sample1.X)

        test_something()

        compare(sample1.X().aMethod(), sample1.X)

    def test_multiple_replace(self):

        def test_y(self):
            return 'test y'

        def test_z():
            return 'test z'

        compare(sample1.z(), 'original z')
        compare(sample1.X().y(), 'original y')

        @replace('testfixtures.tests.sample1.z', test_z)
        @replace('testfixtures.tests.sample1.X.y', test_y)
        def test_something(passed_test_y, passed_test_z):
            compare(test_z, passed_test_z)
            compare(test_y, passed_test_y)
            compare(sample1.z(), 'test z')
            compare(sample1.X().y(), 'test y')

        compare(sample1.z(), 'original z')
        compare(sample1.X().y(), 'original y')

        test_something()

        compare(sample1.z(), 'original z')
        compare(sample1.X().y(), 'original y')

    def test_gotcha(self):
        # Just because you replace an object in one context,
        # doesn't meant that it's replaced in all contexts!

        def test_z():
            return 'test z'

        compare(sample1.z(), 'original z')
        compare(sample2.z(), 'original z')

        @replace('testfixtures.tests.sample1.z', test_z)
        def test_something():
            compare(sample1.z(), 'test z')
            compare(sample2.z(), 'original z')

        compare(sample1.z(), 'original z')
        compare(sample2.z(), 'original z')

        test_something()

        compare(sample1.z(), 'original z')
        compare(sample2.z(), 'original z')

    def test_raises(self):

        def test_z():
            return 'replacement z'

        compare(sample1.z(), 'original z')

        @replace('testfixtures.tests.sample1.z', test_z)
        def test_something():
            compare(sample1.z(), 'replacement z')
            raise Exception()

        compare(sample1.z(), 'original z')

        with ShouldRaise():
            test_something()

        compare(sample1.z(), 'original z')

    def test_want_replacement(self):

        o = object()

        @replace('testfixtures.tests.sample1.z', o)
        def test_something(r):
            self.assertTrue(r is o)
            self.assertTrue(sample1.z is o)

        test_something()

    def test_not_there(self):

        o = object()

        @replace('testfixtures.tests.sample1.bad', o)
        def test_something(r):
            pass  # pragma: no cover

        with ShouldRaise(AttributeError("Original 'bad' not found")):
            test_something()

    def test_not_there_ok(self):

        o = object()

        @replace('testfixtures.tests.sample1.bad', o, strict=False)
        def test_something(r):
            self.assertTrue(r is o)
            self.assertTrue(sample1.bad is o)

        test_something()

    def test_replace_dict(self):

        from testfixtures.tests.sample1 import some_dict

        original = some_dict['key']
        replacement = object()

        @replace('testfixtures.tests.sample1.some_dict.key', replacement)
        def test_something(obj):
            self.assertTrue(obj is replacement)
            self.assertTrue(some_dict['key'] is replacement)

        test_something()

        self.assertTrue(some_dict['key'] is original)

    def test_replace_delattr(self):

        from testfixtures.tests import sample1

        @replace('testfixtures.tests.sample1.some_dict', not_there)
        def test_something(obj):
            self.assertFalse(hasattr(sample1, 'some_dict'))

        test_something()

        self.assertEqual(sample1.some_dict,
                         {'complex_key': [1, 2, 3], 'key': 'value'})

    def test_replace_delattr_not_there(self):

        @replace('testfixtures.tests.sample1.foo', not_there)
        def test_something(obj):
            pass  # pragma: no cover

        with ShouldRaise(AttributeError("Original 'foo' not found")):
            test_something()

    def test_replace_delattr_not_there_not_strict(self):

        from testfixtures.tests import sample1

        @replace('testfixtures.tests.sample1.foo',
                 not_there, strict=False)
        def test_something(obj):
            self.assertFalse(hasattr(sample1, 'foo'))

        test_something()

    def test_replace_delattr_not_there_restored(self):

        from testfixtures.tests import sample1

        @replace('testfixtures.tests.sample1.foo',
                 not_there, strict=False)
        def test_something(obj):
            sample1.foo = 'bar'

        test_something()
        self.assertFalse(hasattr(sample1, 'foo'))

    def test_replace_delattr_cant_remove(self):
        if PY_310_PLUS:
            message = "cannot set 'today' attribute of " \
                      "immutable type 'datetime.datetime'"
        else:
            message = "can't set attributes of " \
                      "built-in/extension type 'datetime.datetime'"
        with Replacer() as r:
            with ShouldRaise(TypeError(message)):
                r.replace('datetime.datetime.today', not_there)

    def test_replace_delattr_cant_remove_not_strict(self):
        if PY_310_PLUS:
            message = "cannot set 'today' attribute of " \
                      "immutable type 'datetime.datetime'"
        else:
            message = "can't set attributes of " \
                      "built-in/extension type 'datetime.datetime'"
        with Replacer() as r:
            with ShouldRaise(TypeError(message)):
                r.replace('datetime.datetime.today', not_there, strict=False)

    def test_replace_dict_remove_key(self):

        from testfixtures.tests.sample1 import some_dict

        @replace('testfixtures.tests.sample1.some_dict.key', not_there)
        def test_something(obj):
            self.assertFalse('key' in some_dict)

        test_something()

        self.assertEqual(sorted(some_dict.keys()), ['complex_key', 'key'])

    def test_replace_dict_remove_key_not_there(self):

        from testfixtures.tests.sample1 import some_dict

        @replace('testfixtures.tests.sample1.some_dict.badkey', not_there)
        def test_something(obj):
            self.assertFalse('badkey' in some_dict)  # pragma: no cover

        with ShouldRaise(AttributeError("Original 'badkey' not found")):
            test_something()

        self.assertEqual(sorted(some_dict.keys()), ['complex_key', 'key'])

    def test_replace_dict_remove_key_not_there_not_strict(self):

        from testfixtures.tests.sample1 import some_dict

        @replace('testfixtures.tests.sample1.some_dict.badkey',
                 not_there, strict=False)
        def test_something(obj):
            self.assertFalse('badkey' in some_dict)

        test_something()

        self.assertEqual(sorted(some_dict.keys()), ['complex_key', 'key'])

    def test_replace_dict_ensure_key_not_there_restored(self):

        from testfixtures.tests.sample1 import some_dict

        @replace('testfixtures.tests.sample1.some_dict.badkey',
                 not_there, strict=False)
        def test_something(obj):
            some_dict['badkey'] = 'some test value'

        test_something()

        self.assertEqual(sorted(some_dict.keys()), ['complex_key', 'key'])

    def test_replace_dict_not_there(self):

        from testfixtures.tests.sample1 import some_dict

        replacement = object()

        @replace('testfixtures.tests.sample1.some_dict.key2',
                 replacement,
                 strict=False)
        def test_something(obj):
            self.assertTrue(obj is replacement)
            self.assertTrue(some_dict['key2'] is replacement)

        test_something()

        self.assertEqual(sorted(some_dict.keys()), ['complex_key', 'key'])

    def test_replace_dict_not_there_empty_string(self):

        from testfixtures.tests.sample1 import some_dict

        @replace('testfixtures.tests.sample1.some_dict.key2', '', strict=False)
        def test_something():
            self.assertEqual(some_dict['key2'], '')

        test_something()

        self.assertEqual(sorted(some_dict.keys()), ['complex_key', 'key'])

    def test_replace_complex(self):

        from testfixtures.tests.sample1 import some_dict

        original = some_dict['complex_key'][1]
        replacement = object()

        @replace('testfixtures.tests.sample1.some_dict.complex_key.1',
                 replacement)
        def test_something(obj):
            self.assertTrue(obj is replacement)
            self.assertEqual(some_dict['complex_key'], [1, obj, 3])

        test_something()

        self.assertEqual(some_dict['complex_key'], [1, 2, 3])

        self.assertTrue(original is some_dict['complex_key'][1])

    def test_replacer_del(self):
        r = Replacer()
        r.replace('testfixtures.tests.sample1.left_behind',
                  object(), strict=False)
        with catch_warnings(record=True) as w:
            del r
            self.assertTrue(len(w), 1)
            compare(str(w[0].message),
                    "Replacer deleted without being restored, originals left:"
                    " {'testfixtures.tests.sample1.left_behind': <not_there>}")

    def test_multiple_replaces(self):
        orig = os.path.sep
        with Replacer() as r:
            r.replace('os.path.sep', '$')
            compare(os.path.sep, '$')
            r.replace('os.path.sep', '=')
            compare(os.path.sep, '=')
        compare(orig, os.path.sep)

    def test_sub_module_import(self):
        with TempDirectory() as dir:
            dir.write('module/__init__.py', b'')
            dir.write('module/submodule.py', b'def foo(): return "foo"')

            with Replacer() as r:
                r.replace('sys.path', [dir.path])

                def bar():
                    return "bar"
                # now test

                r.replace('module.submodule.foo', bar)

                from module.submodule import foo
                compare(foo(), "bar")

    def test_staticmethod(self):
        compare(sample1.X.bMethod(), 2)
        with Replacer() as r:
            r.replace('testfixtures.tests.sample1.X.bMethod', lambda: 1)
            compare(sample1.X.bMethod(), 1)
        compare(sample1.X.bMethod(), 2)

    def test_use_as_cleanup(self):
        def test_z():
            return 'replacement z'

        compare(sample1.z(), 'original z')
        replace = Replacer()
        compare(sample1.z(), 'original z')
        replace('testfixtures.tests.sample1.z', test_z)
        cleanup = replace.restore
        try:
            compare(sample1.z(), 'replacement z')
        finally:
            cleanup()
        compare(sample1.z(), 'original z')

    def test_replace_context_manager(self):
        def test_z():
            return 'replacement z'

        compare(sample1.z(), 'original z')

        with Replace('testfixtures.tests.sample1.z', test_z) as z:
            compare(z(), 'replacement z')
            compare(sample1.z(), 'replacement z')

        compare(sample1.z(), 'original z')

    def test_multiple_context_managers(self):

        def test_y(self):
            return 'test y'

        def test_z():
            return 'test z'

        compare(sample1.z(), 'original z')
        compare(sample1.X().y(), 'original y')

        with Replacer() as replace:
            z = replace('testfixtures.tests.sample1.z', test_z)
            y = replace('testfixtures.tests.sample1.X.y', test_y)
            compare(z(), 'test z')
            compare(y, sample1.X.y)
            compare(sample1.X().y(), 'test y')
            compare(sample1.z(), 'test z')
            compare(sample1.X().y(), 'test y')

        compare(sample1.z(), 'original z')
        compare(sample1.X().y(), 'original y')

    def test_context_manager_not_strict(self):
        def test_z():
            return 'replacement z'

        with Replace('testfixtures.tests.sample1.foo', test_z, strict=False):
            compare(sample1.foo(), 'replacement z')
