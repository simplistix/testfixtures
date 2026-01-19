import os
from pathlib import Path
from tempfile import mkdtemp
from typing import Iterator, Sequence
from unittest import TestCase
from warnings import catch_warnings

import pytest

from testfixtures.mock import Mock, call

from testfixtures import (
    TempDirectory, TempDir, Replacer, ShouldRaise, compare, OutputCapture
)
from testfixtures.formats import JSON, Format, YAML
from testfixtures.rmtree import rmtree

some_bytes = '\xa3'.encode('utf-8')
some_text = '\xa3'


class TestTempDirectory(TestCase):

    def test_cleanup(self) -> None:
        d = TempDirectory()
        p = d.path
        assert p is not None
        assert os.path.exists(p) is True
        p = d.write('something', b'stuff')
        d.cleanup()
        assert os.path.exists(p) is False

    def test_cleanup_all(self) -> None:
        d1 = TempDirectory()
        d2 = TempDirectory()

        assert d1.path is not None
        assert os.path.exists(d1.path) is True
        p1 = d1.path
        assert d2.path is not None
        assert os.path.exists(d2.path) is True
        p2 = d2.path

        TempDirectory.cleanup_all()

        assert os.path.exists(p1) is False
        assert os.path.exists(p2) is False

    def test_with_statement(self) -> None:
        with TempDirectory() as d:
           p = d.path
           assert p is not None
           assert os.path.exists(p) is True
           d.write('something', b'stuff')
           assert os.listdir(p) == ['something']
           with open(os.path.join(p, 'something')) as f:
               assert f.read() == 'stuff'
        assert os.path.exists(p) is False

    def test_listdir_sort(self) -> None:  # pragma: no branch
        with TempDirectory() as d:
            d.write('ga', b'')
            d.write('foo1', b'')
            d.write('Foo2', b'')
            d.write('g.o', b'')
            with OutputCapture() as output:
                d.listdir()
        output.compare('Foo2\nfoo1\ng.o\nga')


class TempDirectoryTests(TestCase):

    def test_write_with_slash_at_start(self) -> None:
        with TempDirectory() as d:
            with ShouldRaise(ValueError(
                    'Attempt to read or write outside the temporary Directory'
                    )):
                d.write('/some/folder', 'stuff')

    def test_makedir_with_slash_at_start(self) -> None:
        with TempDirectory() as d:
            with ShouldRaise(ValueError(
                    'Attempt to read or write outside the temporary Directory'
                    )):
                d.makedir('/some/folder')

    def test_read_with_slash_at_start(self) -> None:
        with TempDirectory() as d:
            with ShouldRaise(ValueError(
                    'Attempt to read or write outside the temporary Directory'
                    )):
                d.read('/some/folder')

    def test_listdir_with_slash_at_start(self) -> None:
        with TempDirectory() as d:
            with ShouldRaise(ValueError(
                    'Attempt to read or write outside the temporary Directory'
                    )):
                d.listdir('/some/folder')

    def test_compare_with_slash_at_start(self) -> None:
        with TempDirectory() as d:
            with ShouldRaise(ValueError(
                    'Attempt to read or write outside the temporary Directory'
                    )):
                d.compare((), path='/some/folder')

    def test_read_with_slash_at_start_ok(self) -> None:
        with TempDirectory() as d:
            path = d.write('foo', b'bar')
            compare(d.read(path), b'bar')

    def test_dont_cleanup_with_path(self) -> None:
        d = mkdtemp()
        fp = os.path.join(d, 'test')
        with open(fp, 'w') as f:
            f.write('foo')
        try:
            td = TempDirectory(path=d)
            self.assertEqual(d, td.path)
            td.cleanup()
            # checks
            self.assertEqual(os.listdir(d), ['test'])
            with open(fp) as f:
                self.assertEqual(f.read(), 'foo')
        finally:
            rmtree(d)

    def test_dont_create_with_path(self) -> None:
        d = mkdtemp()
        rmtree(d)
        td = TempDirectory(path=d)
        self.assertEqual(d, td.path)
        self.assertFalse(os.path.exists(d))

    def test_delay_create(self) -> None:
        td = TempDirectory(create=False)
        assert td.path is None
        with ShouldRaise(RuntimeError('Instantiated with create=False and .create() not called')):
            td.as_path()
        td.create()
        assert td.path is not None
        td.cleanup()
        assert td.path is None

    def test_compare_sort_actual(self) -> None:
        with TempDirectory() as d:
            d.write('ga', b'')
            d.write('foo1', b'')
            d.write('Foo2', b'')
            d.write('g.o', b'')
            d.compare(['Foo2', 'foo1', 'g.o', 'ga'])

    def test_compare_sort_expected(self) -> None:
        with TempDirectory() as d:
            d.write('ga', b'')
            d.write('foo1', b'')
            d.write('Foo2', b'')
            d.write('g.o', b'')
            d.compare(['Foo2', 'ga', 'foo1', 'g.o'])

    def test_compare_path_tuple(self) -> None:
        with TempDirectory() as d:
            d.write('a/b/c', b'')
            d.compare(path=('a', 'b'),
                      expected=['c'])

    def test_recursive_ignore(self) -> None:
        with TempDirectory(ignore=['.svn']) as d:
            d.write('.svn/rubbish', b'')
            d.write('a/.svn/rubbish', b'')
            d.write('a/b/.svn', b'')
            d.write('a/b/c', b'')
            d.write('a/d/.svn/rubbish', b'')
            d.compare([
                'a/',
                'a/b/',
                'a/b/c',
                'a/d/',
                ])

    def test_files_only(self) -> None:
        with TempDirectory() as d:
            d.write('a/b/c', b'')
            d.compare(['a/b/c'], files_only=True)

    def test_path(self) -> None:
        with TempDirectory() as d:
            expected1 = d.makedir('foo')
            expected2 = d.write('baz/bob', b'')
            expected3 = d.as_string('a/b/c')

            actual1 = d.as_string('foo')
            actual2 = d.as_string('baz/bob')
            actual3 = d.as_string(('a', 'b', 'c'))

        self.assertEqual(expected1, actual1)
        self.assertEqual(expected2, actual2)
        self.assertEqual(expected3, actual3)

    def test_getpath(self) -> None:
        with TempDirectory() as d:
            expected1 = d.getpath()
            expected2 = d.getpath('foo')

            actual1 = d.as_string()
            actual2 = d.as_string('foo')

        compare(expected1, actual=actual1)
        compare(expected2, actual=actual2)

    def test_atexit(self) -> None:
        m = Mock()
        with Replacer() as r:
            # make sure the marker is false, other tests will
            # probably have set it
            r.replace('testfixtures.TempDirectory.atexit_setup', False)
            r.replace('atexit.register', m.register)

            d = TempDirectory()

            expected = [call.register(d.atexit)]

            compare(expected, m.mock_calls)

            with catch_warnings(record=True) as w:
                d.atexit()
                self.assertTrue(len(w), 1)
                assert d.path is not None
                compare(str(w[0].message), (  # pragma: no branch
                    "TempDirectory instances not cleaned up by shutdown:\n" +
                    d.path
                    ))

            d.cleanup()

            compare(TempDirectory.instances, expected=set())

            # check re-running has no ill effects
            d.atexit()

    def test_read_decode(self) -> None:
        with TempDirectory() as d:
            assert d.path is not None
            with open(os.path.join(d.path, 'test.file'), 'wb') as f:
                f.write(b'\xc2\xa3')
            compare(d.read('test.file', 'utf8'), some_text)

    def test_read_no_decode(self) -> None:
        with TempDirectory() as d:
            assert d.path is not None
            with open(os.path.join(d.path, 'test.file'), 'wb') as f:
                f.write(b'\xc2\xa3')
            compare(d.read('test.file'), b'\xc2\xa3')

    def test_write_bytes(self) -> None:
        with TempDirectory() as d:
            d.write('test.file', b'\xc2\xa3')
            assert d.path is not None
            with open(os.path.join(d.path, 'test.file'), 'rb') as f:
                compare(f.read(), b'\xc2\xa3')

    def test_write_unicode(self) -> None:
        with TempDirectory() as d:
            d.write('test.file', some_text, 'utf8')
            assert d.path is not None
            with open(os.path.join(d.path, 'test.file'), 'rb') as f:
                compare(f.read(), b'\xc2\xa3')

    def test_write_unicode_default_encoding(self) -> None:
        with TempDirectory() as d:
            d.write('test.file', u'\xa3')
            compare((d / 'test.file').read_text(), expected=u'\xa3')

    def test_just_empty_non_recursive(self) -> None:
        with TempDirectory() as d:
            d.makedir('foo/bar')
            d.makedir('foo/baz')
            d.compare(path='foo',
                      expected=['bar', 'baz'],
                      recursive=False)

    def test_just_empty_dirs(self) -> None:
        with TempDirectory() as d:
            d.makedir('foo/bar')
            d.makedir('foo/baz')
            d.compare(['foo/', 'foo/bar/', 'foo/baz/'])

    def test_symlink(self) -> None:
        with TempDirectory() as d:
            d.write('foo/bar.txt', b'x')
            os.symlink(d.as_string('foo'), d.as_string('baz'))
            d.compare(['baz/', 'foo/', 'foo/bar.txt'])

    def test_follow_symlinks(self) -> None:
        with TempDirectory() as d:
            d.write('foo/bar.txt', b'x')
            os.symlink(d.as_string('foo'), d.as_string('baz'))
            d.compare(['baz/', 'baz/bar.txt', 'foo/', 'foo/bar.txt'],
                      followlinks=True)

    def test_trailing_slash(self) -> None:
        with TempDirectory() as d:
            d.write('source/foo/bar.txt', b'x')
            d.compare(path='source/', expected=['foo/', 'foo/bar.txt'])

    def test_default_encoding(self) -> None:
        encoded = b'\xc2\xa3'
        decoded = encoded.decode('utf-8')
        with TempDirectory(encoding='utf-8') as d:
            d.write('test.txt', decoded)
            compare(d.read('test.txt'), expected=decoded)

    def test_override_default_encoding(self) -> None:
        encoded = b'\xc2\xa3'
        decoded = encoded.decode('utf-8')
        with TempDirectory(encoding='ascii') as d:
            d.write('test.txt', decoded, encoding='utf-8')
            compare(d.read('test.txt', encoding='utf-8'), expected=decoded)

    def test_attempt_to_encode_bytes(self) -> None:
        with TempDirectory() as d:
            with ShouldRaise(TypeError("Cannot specify encoding when data is bytes")):
                d.write('test.txt', b'\xc2\xa3', encoding='utf-8')  # type: ignore[call-overload]

    def test_as_path_minimal(self) -> None:
        with TempDirectory(encoding='ascii') as d:
            assert d.path is not None
            compare(d.as_path(), expected=Path(d.path), strict=True)

    def test_as_path_relative_string(self) -> None:
        with TempDirectory(encoding='ascii') as d:
            assert d.path is not None
            compare(d.as_path('foo/bar'), expected=Path(d.path) / 'foo' / 'bar', strict=True)

    def test_as_path_relative_sequence(self) -> None:
        with TempDirectory(encoding='ascii') as d:
            assert d.path is not None
            compare(d.as_path(('foo', 'bar')), expected=Path(d.path) / 'foo' / 'bar', strict=True)

    def test_traverse(self) -> None:
        with TempDirectory(encoding='ascii') as d:
            assert d.path is not None
            compare((d / 'foo' / 'bar'), expected=Path(d.path) / 'foo' / 'bar', strict=True)

    def test_cwd_context_manager(self) -> None:
        original = os.getcwd()
        try:
            # need to resolve links thanks to /tmp location on macos!
            with TempDirectory(cwd=True) as d:
                assert d.path is not None
                compare(Path(os.getcwd()).resolve(), expected=Path(d.path).resolve())
            compare(Path(os.getcwd()).resolve(), expected=Path(original).resolve())
        finally:
            os.chdir(original)

    def test_write_read_roundtrip(self):
        with TempDirectory(cwd=True) as d:
            path = d.write('file', 'stuff')
            result = d.read(path)
        compare(result, expected=b'stuff')

    def test_write_path(self):
        with TempDirectory(cwd=True) as d:
            path = d.write(d / 'file', 'stuff')
            compare(Path(path).read_text(), expected='stuff')


def test_wrap_path(tmp_path: Path) -> None:
    with TempDirectory(tmp_path) as d:
        assert d.path == str(tmp_path)
    assert tmp_path.exists()


class TestTempDir:

    @pytest.fixture()
    def tempdir(self) -> Iterator[TempDir]:
        with TempDir() as d:
            yield d

    def test_makedir(self, tempdir: TempDir) -> None:
        path = tempdir.makedir('foo')
        assert isinstance(path, Path)

    def test_write(self, tempdir: TempDir) -> None:
        path = tempdir.write('foo', '')
        assert isinstance(path, Path)

    def test_path(self, tempdir: TempDir) -> None:
        assert isinstance(tempdir.path, Path)
        assert tempdir.path.exists()

    def test_attempt_to_encode_bytes(self, tempdir: TempDir) -> None:
        with ShouldRaise(TypeError("Cannot specify encoding when data is bytes")):
            tempdir.write('test.txt', b'\xc2\xa3', encoding='utf-8')  # type: ignore[call-overload]

    def test_write_read_roundtrip(self, tempdir: TempDir):
        path = tempdir.write('file', 'stuff')
        result = tempdir.read(path)
        compare(result, expected=b'stuff')

    def test_write_path(self, tempdir: TempDir):
        path = tempdir.write(tempdir / 'file', 'stuff')
        compare(path.read_text(), expected='stuff')


@pytest.mark.parametrize('class_', [TempDir, TempDirectory])
class TestFormats:

    def test_write_format(self, class_: type[TempDir | TempDirectory]) -> None:
        with class_() as d:
            data = {'key': 'value', 'number': 42}
            d.write('config.json', data, format=JSON)
            with open(os.path.join(d.path, 'config.json'), 'rb') as f:
                compare(f.read(), b'{"key": "value", "number": 42}')

    def test_read_format(self, class_: type[TempDir | TempDirectory]):
        with class_() as d:
            with open(os.path.join(d.path, 'config.json'), 'wb') as f:
                f.write(b'{"key": "value", "number": 42}')
            result = d.read('config.json', format=JSON)
            compare(result, expected={'key': 'value', 'number': 42})

    def test_roundtrip_format(self, class_: type[TempDir | TempDirectory]):
        with class_() as d:
            original = {'nested': {'data': [1, 2, 3]}, 'flag': True}
            d.write('data.json', original, format=JSON)
            result = d.read('data.json', format=JSON)
            compare(result, expected=original)

    def test_write_format_with_encoding(self, class_: type[TempDir | TempDirectory]):
        with class_() as d:
            # Test that latin-1 encoding is used with ASCII-safe JSON
            # JSON module escapes non-ASCII as \uXXXX by default
            data = {'message': 'test'}
            d.write('config.json', data, encoding='latin-1', format=JSON)
            with open(os.path.join(d.path, 'config.json'), 'rb') as f:
                # JSON string encoded as latin-1 (ASCII compatible)
                content = f.read()
                compare(content, expected=b'{"message": "test"}')

    def test_read_format_with_encoding(self, class_: type[TempDir | TempDirectory]):
        with class_() as d:
            # Write latin-1 encoded JSON with non-ASCII character
            # £ is 0xa3 in latin-1
            with open(os.path.join(d.path, 'config.json'), 'wb') as f:
                f.write(b'{"message": "\xa3100"}')
            result = d.read('config.json', encoding='latin-1', format=JSON)
            compare(result, expected={'message': '£100'})

    def test_roundtrip_format_with_encoding(self, class_: type[TempDir | TempDirectory]):
        with class_() as d:
            # Roundtrip with latin-1 encoding
            # Use ASCII-safe data since JSON escapes non-ASCII by default
            original = {'name': 'test', 'value': 123}
            d.write('data.json', original, encoding='latin-1', format=JSON)
            result = d.read('data.json', encoding='latin-1', format=JSON)
            compare(result, expected=original)

    def test_format_with_default_encoding(self, class_: type[TempDir | TempDirectory]):
        with class_(encoding='utf-8') as d:
            data = {'test': 'data'}
            d.write('config.json', data, format=JSON)
            result = d.read('config.json', format=JSON)
            compare(result, expected=data)

    def test_write_no_format_but_data_provided(self, class_: type[TempDir | TempDirectory]):
        with class_() as d:
            with ShouldRaise(TypeError("memoryview: a bytes-like object is required, not 'dict'")):
                d.write('config.json', {'test': 'data'})  # type: ignore[call-overload]


@pytest.mark.parametrize('class_', [TempDir, TempDirectory])
class TestReadText:

    def test_basic_text_reading(self, class_: type[TempDir | TempDirectory]):
        with class_() as d:
            d.write('file.txt', 'hello world', encoding='utf-8')
            result = d.read_text('file.txt', encoding='utf-8')
            compare(result, expected='hello world')

    def test_instance_default_encoding(self, class_: type[TempDir | TempDirectory]):
        with class_(encoding='utf-8') as d:
            d.write('file.txt', 'test content', encoding='utf-8')
            result = d.read_text('file.txt')
            compare(result, expected='test content')

    def test_explicit_encoding_overrides_instance(self, class_: type[TempDir | TempDirectory]):
        with class_(encoding='latin-1') as d:
            d.write('file.txt', 'café', encoding='utf-8')
            result = d.read_text('file.txt', encoding='utf-8')
            compare(result, expected='café')

    def test_errors_parameter(self, class_: type[TempDir | TempDirectory]):
        with class_() as d:
            d.write('file.txt', b'\xff\xfe')
            result = d.read_text('file.txt', encoding='utf-8', errors='ignore')
            assert isinstance(result, str)

    def test_newline_parameter(self, class_: type[TempDir | TempDirectory]):
        with class_() as d:
            d.write('file.txt', 'line1\r\nline2\r\n', encoding='utf-8')
            result = d.read_text('file.txt', encoding='utf-8', newline='')
            compare(result, expected='line1\r\nline2\r\n')

    def test_type_annotation(self, class_: type[TempDir | TempDirectory]):
        with class_() as d:
            d.write('file.txt', 'text', encoding='utf-8')
            result: str = d.read_text('file.txt')
            assert isinstance(result, str)


@pytest.mark.parametrize('class_', [TempDir, TempDirectory])
class TestReadBytes:

    def test_basic_bytes_reading(self, class_: type[TempDir | TempDirectory]):
        with class_() as d:
            d.write('file.bin', b'\x00\x01\x02\x03')
            result = d.read_bytes('file.bin')
            compare(result, expected=b'\x00\x01\x02\x03')

    def test_binary_data(self, class_: type[TempDir | TempDirectory]):
        with class_() as d:
            binary_data = bytes(range(256))
            d.write('file.bin', binary_data)
            result = d.read_bytes('file.bin')
            compare(result, expected=binary_data)

    def test_type_annotation(self, class_: type[TempDir | TempDirectory]):
        with class_() as d:
            d.write('file.bin', b'data')
            result: bytes = d.read_bytes('file.bin')
            assert isinstance(result, bytes)

@pytest.mark.parametrize('class_', [TempDir, TempDirectory])
class TestParseDump:

    def test_dump_return_type(self, class_: type[TempDir | TempDirectory]):
        with class_() as d:
            data = {'key': 'value'}
            path = d.dump('config.json', data)
            if class_ is TempDir:
                assert isinstance(path, Path)
            else:
                assert isinstance(path, str)

    def test_dump_json(self, class_: type[TempDir | TempDirectory]):
        with class_() as d:
            data = {'key': 'value', 'number': 42}
            path = d.dump('config.json', data)
            with open(path, 'rb') as f:
                compare(f.read(), b'{"key": "value", "number": 42}')

    def test_parse_json(self, class_: type[TempDir | TempDirectory]):
        with class_() as d:
            d.write('config.json', b'{"key": "value", "number": 42}')
            result = d.parse('config.json')
            compare(result, expected={'key': 'value', 'number': 42})

    def test_roundtrip_json(self, class_: type[TempDir | TempDirectory]):
        with class_() as d:
            original = {'nested': {'data': [1, 2, 3]}, 'flag': True}
            d.dump('data.json', original)
            result = d.parse('data.json')
            compare(result, expected=original)

    def test_dump_yaml(self, class_: type[TempDir | TempDirectory]):
        pytest.importorskip('yaml')
        with class_() as d:
            data = {'app': {'name': 'test'}}
            path = d.dump('config.yaml', data)
            with open(path, 'rb') as f:
                content = f.read()
                assert b'app:' in content
                assert b'name: test' in content

    def test_parse_yaml(self, class_: type[TempDir | TempDirectory]):
        pytest.importorskip('yaml')
        with class_() as d:
            d.write('config.yaml', b'app:\n  name: test\n')
            result = d.parse('config.yaml')
            compare(result, expected={'app': {'name': 'test'}})

    def test_dump_toml(self, class_: type[TempDir | TempDirectory]):
        with class_() as d:
            # TOML reading works with stdlib tomllib, no import needed
            data = {'key': 'value', 'num': 42}
            # But writing requires tomlkit
            pytest.importorskip('tomlkit')
            path = d.dump('config.toml', data)
            with open(path, 'rb') as f:
                content = f.read()
                assert b'key = "value"' in content
                assert b'num = 42' in content

    def test_parse_toml(self, class_: type[TempDir | TempDirectory]):
        with class_() as d:
            d.write('config.toml', b'key = "value"\nnum = 42\n')
            result = d.parse('config.toml')
            compare(result, expected={'key': 'value', 'num': 42})

    def test_case_insensitive(self, class_: type[TempDir | TempDirectory]):
        with class_() as d:
            data = {'test': 'data'}
            path = d.dump('config.JSON', data)
            result = d.parse(path)
            compare(result, expected=data)

    def test_yml_extension(self, class_: type[TempDir | TempDirectory]):
        pytest.importorskip('yaml')
        with class_() as d:
            data = {'test': 'data'}
            path = d.dump('config.yml', data)
            result = d.parse(path)
            compare(result, expected=data)

    def test_unknown_extension(self, class_: type[TempDir | TempDirectory]):
        with class_() as d:
            with ShouldRaise(ValueError(
                "No format registered for extension '.txt'. "
                "Supported extensions: ['.json', '.toml', '.yaml', '.yml']"
            )):
                d.parse('data.txt')

    def test_no_extension(self, class_: type[TempDir | TempDirectory]):
        with class_() as d:
            with ShouldRaise(ValueError(
                "No format registered for extension ''. "
                "Supported extensions: ['.json', '.toml', '.yaml', '.yml']"
            )):
                d.parse('filename')

    def test_multiple_dots_json(self, class_: type[TempDir | TempDirectory]):
        with class_() as d:
            data = {'backup': 'config'}
            d.dump('backup.config.json', data)
            result = d.parse('backup.config.json')
            compare(result, expected=data)

    def test_multiple_dots_toml(self, class_: type[TempDir | TempDirectory]):
        pytest.importorskip('tomlkit')
        with class_() as d:
            data = {'backup': 'config'}
            d.dump('backup.config.toml', data)
            result = d.parse('backup.config.toml')
            compare(result, expected=data)

    def test_custom_formats(self, class_: type[TempDir | TempDirectory]):
        with class_(formats=[JSON]) as d:
            data = {'test': 'data'}
            d.dump('config.json', data)
            result = d.parse('config.json')
            compare(result, expected=data)

    def test_duplicate_suffix(self, class_: type[TempDir | TempDirectory]):
        class CustomFormat:
            suffixes: Sequence[str] = ('.json',)
            def parse(self, data: str):
                return {'custom': data}
            def render(self, obj):
                return str(obj)

        custom_fmt = CustomFormat()
        with ShouldRaise(ValueError("Multiple formats registered for extension '.json'")):
            class_(formats=[JSON, custom_fmt])

    def test_parse_with_instance_encoding(self, class_: type[TempDir | TempDirectory]):
        with class_(encoding='utf-8') as d:
            data = {'message': 'test'}
            d.dump('config.json', data)
            result = d.parse('config.json')
            compare(result, expected=data)

    def test_dump_with_instance_encoding(self, class_: type[TempDir | TempDirectory]):
        with class_(encoding='utf-8') as d:
            data = {'message': 'test'}
            path = d.dump('config.json', data)
            with open(path, 'rb') as f:
                content = f.read()
                # Verify it's properly encoded as UTF-8
                assert b'{"message": "test"}' in content

    def test_parse_no_extension_with_format(self, class_: type[TempDir | TempDirectory]):
        with class_() as d:
            d.write('config', b'{"key": "value"}')
            result = d.parse('config', format=JSON)
            compare(result, expected={'key': 'value'})

    def test_dump_no_extension_with_format(self, class_: type[TempDir | TempDirectory]):
        with class_() as d:
            data = {'key': 'value'}
            path = d.dump('config', data, format=JSON)
            with open(path, 'rb') as f:
                compare(f.read(), expected=b'{"key": "value"}')

    def test_roundtrip_no_extension(self, class_: type[TempDir | TempDirectory]):
        with class_() as d:
            original = {'nested': {'data': [1, 2, 3]}, 'flag': True}
            d.dump('config', original, format=JSON)
            result = d.parse('config', format=JSON)
            compare(result, expected=original)

    def test_parse_format_overrides_extension(self, class_: type[TempDir | TempDirectory]):
        pytest.importorskip('yaml')
        with class_() as d:
            d.write('data.json', b'key: value\n')
            result = d.parse('data.json', format=YAML)
            compare(result, expected={'key': 'value'})

    def test_dump_format_overrides_extension(self, class_: type[TempDir | TempDirectory]):
        pytest.importorskip('yaml')
        with class_() as d:
            data = {'key': 'value'}
            path = d.dump('data.json', data, format=YAML)
            with open(path, 'rb') as f:
                content = f.read()
                assert b'key: value' in content
