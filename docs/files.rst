Testing with files and directories
==================================

.. currentmodule:: testfixtures

Working with files and directories in tests can often require
excessive amounts of boilerplate code to make sure that the tests
happen in their own sandbox, files and directories contain what they
should or code processes test files correctly, and the sandbox is
cleared up at the end of the tests.

To help with this, testfixtures provides the :class:`TempDir` class that hides most of the
boilerplate code you would need to write.

.. note::
   :class:`TempDirectory` is still available for backward compatibility but is
   deprecated as of version 11. New code should use :class:`TempDir`, which returns
   :class:`~pathlib.Path` objects instead of strings.

Methods of use
--------------

Suppose you wanted to test the following function:

.. code-block:: python

  from pathlib import Path

  def foo2bar(dirpath: Path, filename: str) -> None:
      path = dirpath / filename
      data = path.read_bytes()
      data = data.replace(b'foo', b'bar')
      path.write_bytes(data)

There are two ways to use a :class:`TempDir`:

The context manager
~~~~~~~~~~~~~~~~~~~

A :class:`TempDir` can be used as a context manager:

>>> from testfixtures import TempDir
>>> with TempDir() as d:
...   test_txt = d.write('Downloads/test.txt', b'some foo thing')
...   foo2bar(d / 'Downloads', 'test.txt')
...   test_txt.read_bytes()
b'some bar thing'

Manual usage
~~~~~~~~~~~~

If you want to work with files or directories for the duration of a
doctest or in every test in a :class:`~unittest.TestCase`, then you
can use the :class:`TempDir` manually.

The instantiation is done in the set-up step of the :class:`~unittest.TestCase` or equivalent:

>>> from testfixtures import TempDir
>>> d = TempDir()

You can then use the temporary directory for your testing:

>>> d.write('test.txt', 'some foo thing')
PosixPath('...')
>>> foo2bar(d.path, 'test.txt')
>>> d.read('test.txt') == b'some bar thing'
True

Then, in the tear-down step of the :class:`~unittest.TestCase` or equivalent,
you should make sure the temporary directory is cleaned up:

>>> d.cleanup()

The :meth:`~testfixtures.TempDir.cleanup` method can also be added as an
:meth:`~unittest.TestCase.addCleanup` if that is easier or more compact in your test
suite.

If you have multiple :class:`TempDir` objects in use,
you can easily clean them all up:

>>> TempDir.cleanup_all()

.. invisible-code-block: python

   # Need to put re-create the docs-wide fixture now:
   sample_path = _tempdir.create()


Working with other interfaces
-----------------------------

If you're using a testing framework that already provides a temporary directory,
such as pytest's :ref:`tmp_path <tmp_path>` or :ref:`tmpdir <tmpdir>`, but wish to make use of
the :class:`TempDir` API for creating content or making assertions, then you can wrap the
existing object as follows:

>>> with TempDir(tmp_path) as d:
...     d.write('some/path.txt', 'some text')
...     d.compare(expected=('some/', 'some/path.txt'))
PosixPath('...')

When doing this, :class:`TempDir` will not remove the directory it is wrapping:

>>> tmp_path.exists()
True

Features of a temporary directory
---------------------------------

No matter which usage pattern you pick, you will always end up with a
:class:`TempDir` object. These have an array of
methods that let you perform common file and directory related tasks
without all the manual boiler plate. The following sections show you
how to perform the various tasks you're likely to bump into in the
course of testing.

.. create a tempdir for the examples:

  >>> tempdir = TempDir()

Computing paths
~~~~~~~~~~~~~~~

If you need to know the real path of the temporary directory, the
:class:`TempDir` object has a :attr:`~TempDir.path`
attribute:

>>> tempdir.path
PosixPath('...tmp...')

If you want to compute a path within the directory, you can traverse directly from it as if
it were a :class:`~pathlib.Path`:

>>> tempdir / 'some' / 'where'
PosixPath('.../some/where')

You can also explicitly ask for either a :class:`~pathlib.Path` or a string path:

>>> tempdir.as_path('foo')
PosixPath('.../foo')
>>> tempdir.as_string('bar')
'.../bar'

If you want to compute a deeper path, you can pass either a
tuple or a forward slash-separated path to any of the methods:

>>> import os
>>> tempdir.as_string(('foo', 'baz')).rsplit(os.sep, 2)[-2:]
['foo', 'baz']
>>> tempdir.as_string('foo/baz').rsplit(os.sep, 2)[-2:]
['foo', 'baz']

.. note:: 

  If passing a string containing path separators, a forward
  slash should be used as the separator regardless of the underlying
  platform separator.

Writing files
~~~~~~~~~~~~~

To write to a file in the root of the temporary directory, you pass
the name of the file and the content you want to write:

>>> tempdir.write('myfile.txt', 'some text')
PosixPath(...)
>>> print((tempdir / 'myfile.txt').read_text())
some text

The absolute path of the newly written file is returned:

>>> path = tempdir.write('anotherfile.txt', 'some more text')
>>> print(path.read_text())
some more text

You can also write files into a sub-directory of the temporary
directory as follows; if any intermediate directories do not exist, they will be created:

>>> path = tempdir.write(('some', 'folder', 'afile.txt'), 'the text')
>>> print(path.read_text())
the text

You can also specify the path to write to as a forward-slash separated
string:

>>> path = tempdir.write('some/folder/bfile.txt', 'the text')
>>> print(path.read_text())
the text

.. note::

   Forward slashes should be used regardless of the file system or
   operating system in use.

For structured data like JSON, YAML, or TOML, the :meth:`~TempDir.dump` method
provides automatic serialization based on file extension:

>>> tempdir.dump('config.json', {'host': 'localhost', 'port': 8080})
PosixPath('...')
>>> print(tempdir.read_text('config.json'))
{"host": "localhost", "port": 8080}

.. invisible-code-block: python

  try:
      import yaml
      import tomlkit
  except ImportError:
      missing_format_deps = True
  else:
      missing_format_deps = False

.. skip: start if(missing_format_deps, reason="yaml or tomlkit not installed")

>>> tempdir.dump('settings.yaml', {'debug': True, 'level': 'info'})
PosixPath('...')
>>> print(tempdir.read_text('settings.yaml'))
debug: true
level: info
<BLANKLINE>

.. skip: end

You can also clone existing static files and directories using :meth:`~TempDir.clone`:

.. invisible-code-block: python

   sample_path = _tempdir.write("sample.txt", "Sample Content")

>>> sample_path
'.../sample.txt'
>>> tempdir.clone(sample_path)
PosixPath('...')
>>> (tempdir / 'sample.txt').read_text()
'Sample Content'

Creating directories
~~~~~~~~~~~~~~~~~~~~

If you just want to create a sub-directory in the temporary directory
you can do so as follows: 

.. new tempdir:

  >>> tempdir = TempDir()

>>> tempdir.makedir('output')
PosixPath('...')
>>> (tempdir / 'output').is_dir()
True

As with file creation, the absolute path of the sub-directory that has
just been created is returned:

>>> path = tempdir.makedir('more_output')
>>> Path(path).is_dir()
True

Finally, you can create a nested sub-directory even if the intervening
parent directories do not exist:

>>> (tempdir / 'some').exists()
False
>>> path = tempdir.makedir(('some', 'sub', 'dir'))
>>> Path(path).exists()
True

You can also specify the path of the directories to create as a forward-slash separated
string:

>>> (tempdir / 'another').exists()
False
>>> path = tempdir.makedir('another/sub/dir')
>>> Path(path).exists()
True

.. note:: 

   Forward slashes should be used regardless of the file system or
   operating system in use.

Checking the contents of files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once a file has been written into the temporary directory, you will
often want to check its contents. This is done with the
:meth:`TempDir.read` method.

Suppose the code you are testing creates some files:

.. new tempdir:

  >>> tempdir = TempDir()

.. code-block:: python

 def spew(root):
      (root / 'root.txt').write_bytes(b'root output')
      (root / 'subdir').mkdir()
      (root / 'subdir' / 'file.txt').write_bytes(b'subdir output')
      (root / 'subdir' / 'logs').mkdir()

We can test this function by passing it the temporary directory's path
and then using the :meth:`TempDir.read` method to
check the files were created with the correct content:

>>> spew(tempdir.as_path())
>>> tempdir.read_text('root.txt')
'root output'
>>> tempdir.read_text('subdir/file.txt')
'subdir output'

The second part of the above test shows how to use the
:meth:`TempDir.read` method to check the contents
of files that are in sub-directories of the temporary directory. This
can also be done by specifying the path relative to the root of 
the temporary directory as a forward-slash separated string:

>>> tempdir.read_text('subdir/file.txt')
'subdir output'

.. note:: 

  Forward slashes should be used regardless of the file system or
  operating system in use.

Checking the contents of directories
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It's good practice to test that your code is only writing files you expect it
to and to check they are being written to the path you expect.
:meth:`TempDir.compare` is the method to use to do this.

As an example, we could check that the ``spew()`` function above created no
extraneous files as follows:

>>> tempdir.compare([
...     'root.txt',
...     'subdir/',
...     'subdir/file.txt',
...     'subdir/logs/',
... ])

If we only wanted to check the sub-directory, we would specify the path to
start from, relative to the root of the temporary directory:

>>> tempdir.compare([
...     'file.txt',
...     'logs/',
... ], path='subdir')

If, like git, we only cared about files, we could do the comparison as follows:

>>> tempdir.compare([
...     'root.txt',
...     'subdir/file.txt',
... ], files_only=True)

And finally, if we only cared about files at a particular level, we could
turn off the recursive comparison as follows:

>>> tempdir.compare([
...     'root.txt',
...     'subdir',
... ], recursive=False)

The :meth:`~testfixtures.TempDir.compare` method can also be used to
check whether a directory contains nothing, for example:

>>> tempdir.compare(path=('subdir', 'logs'), expected=())

The above can also be done by specifying the sub-directory to be
checked as a forward-slash separated path:

>>> tempdir.compare(path='subdir/logs', expected=())

If the actual directory contents do not match the expected contents passed in,
an :class:`AssertionError` is raised, which will show up as a
unit test failure:

>>> tempdir.compare(['subdir'], recursive=False)
Traceback (most recent call last):
...
AssertionError: sequence not as expected:
<BLANKLINE>
same:
()
<BLANKLINE>
expected:
('subdir',)
<BLANKLINE>
actual:
('root.txt', 'subdir')

In some circumstances, you may want to ignore certain files or
sub-directories when checking contents. To make this easy, the
:class:`~testfixtures.TempDir` constructor takes an optional
`ignore` parameter which, if provided, should contain a sequence of
regular expressions. If any of the regular expressions return a match
when used to search through the results of any of the methods
covered in this section, that result will be ignored.

For example, suppose we are testing some revision control code, but
don't really care about the revision control system's metadata
directories, which may or may not be present:

.. code-block:: python

  from random import choice

  def git_ish(dirpath, filename):
      root = Path(dirpath)
      if choice((True, False)):
          (root / '.git').mkdir()
      (root / filename).write_bytes(b'something')

To test this, we can use any of the previously described methods.

When used manually or as a context manager, this would be as follows:

>>> with TempDir(ignore=['.git']) as d:
...    git_ish(d.path, 'test.txt')
...    d.compare(['test.txt'])

.. set things up again:

  >>> tempdir = TempDir()
  >>> spew(tempdir.as_path())

If you are working with doctests, the
:meth:`~testfixtures.TempDir.listdir` method can be used instead:

>>> tempdir.listdir()
root.txt
subdir
>>> tempdir.listdir('subdir')
file.txt
logs
>>> tempdir.listdir(('subdir', 'logs'))
No files or directories found.

The above example also shows how to check the contents of sub-directories of
the temporary directory and also shows what is printed when a
directory contains nothing. The
:meth:`~testfixtures.TempDir.listdir` method can also take a
path separated by forward slashes, which can make doctests a little
more readable. The above test could be written as follows:

>>> tempdir.listdir('subdir/logs')
No files or directories found.

However, if you have a nested folder structure, such as that created by
our ``spew()`` function, it can be easier to just inspect the whole
tree of files and folders created. You can do this by using the
`recursive` parameter to :meth:`~testfixtures.TempDir.listdir`:

>>> tempdir.listdir(recursive=True)
root.txt
subdir/
subdir/file.txt
subdir/logs/

Bytes versus Strings
~~~~~~~~~~~~~~~~~~~~

.. new tempdir:

  >>> tempdir = TempDir()

You'll notice that all of the examples so far have only used bytes.
To work with strings, :class:`TempDir` provides explicit parameters
for providing the character set to use for decoding and encoding.
Using these as example, which all contain the British Pound symbol:

.. code-block:: python

   some_bytes = '\xa3'.encode('utf-8')
   some_text = '\xa3'

When writing, you can either write bytes directly, as we
have been in the examples so far:

>>> path = tempdir.write('currencies.txt', some_bytes)
>>> Path(path).read_bytes()
b'\xc2\xa3'

Or, you can write text, in which case your system default encoding, usually ``utf-8``,
will be used when writing the data to the file:

>>> path = tempdir.write('currencies.txt', some_text)
>>> Path(path).read_bytes()
b'\xc2\xa3'

Alternatively, you can specify an explicit encoding to use when writing the data to the file:

>>> latin_path = tempdir.write('latin-currencies.txt', some_text, encoding='latin1')
>>> Path(latin_path).read_bytes()
b'\xa3'

The same is true when reading files. You can either read bytes:

>>> tempdir.read('currencies.txt') == some_bytes
True

Or, you can read text, but must specify an encoding that will be used
to decode the data in the file:

>>> tempdir.read('currencies.txt', encoding='utf-8') == some_text
True

If you're always using a common character encoding, you can instead
specify it to the constructor:

>>> tempdir = TempDir(encoding='utf-8')
>>> tempdir.write('more-currencies.txt', some_text)
PosixPath('...')

>>> Path(path).read_bytes().decode('utf-8') == some_text
True

>>> tempdir.read('more-currencies.txt') == some_text
True

Serialization Formats
~~~~~~~~~~~~~~~~~~~~~

.. skip: start if(missing_format_deps, reason="yaml or tomlkit not installed")

.. new tempdir:

  >>> tempdir = TempDir()

:class:`TempDir` also supports working with common serialization formats
like JSON, YAML, and TOML through the :meth:`~TempDir.parse` and
:meth:`~TempDir.dump` methods, which auto-detect the format from the file
extension:

>>> config = {'database': {'host': 'localhost', 'port': 5432}, 'debug': True}
>>> tempdir.dump('config.json', config)
PosixPath('...')
>>> print(_.read_text())
{"database": {"host": "localhost", "port": 5432}, "debug": true}
>>> tempdir.parse('config.json')
{'database': {'host': 'localhost', 'port': 5432}, 'debug': True}

If you need to test a situation where the format cannot be inferred from the filename,
then it can be explicitly specified:

>>> from testfixtures.formats import YAML
>>> tempdir.dump('config', config, format=YAML)
PosixPath('...')
>>> print(_.read_text())
database:
  host: localhost
  port: 5432
debug: true
<BLANKLINE>
>>> tempdir.parse('config', format=YAML)
{'database': {'host': 'localhost', 'port': 5432}, 'debug': True}

A format can also be specified to :meth:`~TempDir.write` and :meth:`~TempDir.read`.
When both ``encoding`` and ``format`` are provided, the ``format`` parameter handles the
serialization between objects and strings while the ``encoding`` parameter controls how the
serialized strings are converted to and from bytes.

When writing, the format first renders the object to a string, then that string
is encoded with the specified encoding:

>>> from testfixtures.formats import TOML
>>> data = {'gbp': '£'}
>>> path = tempdir.write('data.toml', data, format=TOML, encoding='latin-1')
>>> path.read_bytes()
b'gbp = "\xa3"\n'

When reading, bytes are first decoded with the specified encoding, then parsed
by the format:

>>> loaded = tempdir.read('data.toml', format=TOML, encoding='latin-1')
>>> loaded
{'gbp': '£'}

Built-in formats
^^^^^^^^^^^^^^^^

Three built-in format handlers are provided:

**JSON** - Always available, uses the standard library :mod:`json` module:

>>> tempdir.dump('data.json', [1, 2, {'key': 'value'}])
PosixPath('...')
>>> print(_.read_text())
[1, 2, {"key": "value"}]
>>> tempdir.parse('data.json')
[1, 2, {'key': 'value'}]

**YAML** - Available when PyYAML is importable.

.. note::

   To use the YAML format, install with the ``testfixtures[yaml]`` extra.

>>> tempdir.dump('config.yaml', {'app': {'name': 'test'}})
PosixPath('...')
>>> print(_.read_text())
app:
  name: test
<BLANKLINE>
>>> tempdir.parse('config.yaml')
{'app': {'name': 'test'}}

**TOML** - Reads uses the standard library :mod:`tomllib`
module (Python 3.11+) or ``tomlkit`` if available. Writing requires ``tomlkit``.

.. note::

   To use TOML format for writing, install with the ``testfixtures[toml]`` extra.

>>> tempdir.dump('config.toml', {'tool': {'name': 'example'}})
PosixPath('...')
>>> print(_.read_text())
[tool]
name = "example"
<BLANKLINE>
>>> tempdir.parse('config.toml')
{'tool': {'name': 'example'}}

.. skip: end

Implementing custom formats
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can add support for additional formats by implementing the
:class:`~testfixtures.formats.Format` protocol. The protocol requires two methods:

- ``parse(data: str) -> Any`` - Deserialize a string into a Python object
- ``render(obj: Any) -> str`` - Serialize a Python object into a string

For example, here's a simple CSV format handler:

.. code-block:: python

    import csv
    from io import StringIO
    from testfixtures.formats import Format

    class CSVFormat:
        def parse(self, data: str) -> list[list[str]]:
            reader = csv.reader(StringIO(data))
            return list(reader)

        def render(self, obj: list[list[str]]) -> str:
            output = StringIO()
            writer = csv.writer(output)
            writer.writerows(obj)
            return output.getvalue()

Here's how it could be used

>>> with TempDir() as d:
...     path = d.dump('data.csv', [['name', 'age'], ['Alice', '30']], format=CSVFormat())
...     print(path.read_text())
...     rows = d.parse('data.csv', format=CSVFormat())
name,age
Alice,30
<BLANKLINE>
>>> rows
[['name', 'age'], ['Alice', '30']]

Working with an existing sandbox
--------------------------------

Some testing infrastructure already provides a sandbox temporary
directory, however that infrastructure might not provide the same
level of functionality that :class:`~testfixtures.TempDir`
provides.

For this reason, it is possible to wrap an existing directory such as
the following with a :class:`~testfixtures.TempDir`:

>>> from tempfile import mkdtemp
>>> thedir = mkdtemp()

When working with the context manager, this is done as follows:

>>> with TempDir(path=thedir) as d:
...   d.write('file', b'data')
...   d.makedir('directory')
...   sorted(os.listdir(thedir))
PosixPath('...')
PosixPath('...')
['directory', 'file']

.. check thedir still exists and reset

  >>> from shutil import rmtree
  >>> os.path.exists(thedir)
  True
  >>> rmtree(thedir)
  >>> thedir = mkdtemp()

It is important to note that if an existing directory is used, it will
not be deleted by the context manager. You
will need to make sure that the directory is cleaned up as required.

.. check the above statement is true:

  >>> os.path.exists(thedir)
  True

.. better clean it up:

 >>> rmtree(thedir)


Changing the current working directory
--------------------------------------

While it's generally not a good idea to have software that relies on the current working
directory, there's still plenty of occasions where it ends up mattering during testing.

If you'd like the current working directory to be set to the temporary directory for the
duration of a managed context, you can do it like this:

>>> import os
>>> with TempDir(cwd=True) as d:
...     os.getcwd() == str(d.as_path().resolve())
True

It's better practice to only change the current working directory for the smallest
context possible, and in this case it's better to use the :func:`~contextlib.chdir` context manager
from the standard library, available on Python 3.11 or newer.

.. _sybil:

Using with Sybil
-----------------

`Sybil`__ is a tool for testing the examples found in
documentation. It works by applying a set of specialised
parsers to the documentation and testing or otherwise using the examples
returned by those parsers.

__ https://sybil.readthedocs.io

The key differences between testing with Sybil and traditional
doctests are that it is possible to plug in different types of parser,
not just the "python console session" one, and so it is possible to
test different types of examples. Testfixtures provides one these
parsers to aid working with
:class:`~testfixtures.TempDir` objects. This parser makes use of
`topic`__ directives with specific classes set to perform
different actions. 

__ https://docutils.sourceforge.io/docs/ref/rst/directives.html#topic

The following sections describe how to use this parser to help with
writing temporary files and checking their contents.

.. note::

   To ensure you are using a compatible version of Sybil, install with the
   ``testfixtures[sybil]`` extra.

Setting up
~~~~~~~~~~

To use the Sybil parser, you need to make sure a
:class:`TempDir` instance is available under a particular name
in the sybil test namespace. This name is then passed to the parser's
constructor and the parser is passed to the
:class:`~sybil.Sybil` constructor.

The following example shows how to use Sybil's `pytest`__ integration to
execute all of the examples below. These require not only the
Testfixtures parser but also the Sybil parsers that give more
traditional doctest behaviour, invisible code blocks
that are useful for setting things up and checking examples without
breaking up the flow of the documentation, and capturing of examples
from the documentation to use for use in other forms of testing: 

__ https://docs.pytest.org/en/latest/

.. literalinclude:: ../conftest.py

Writing files
~~~~~~~~~~~~~

To write a file, a `topic`__ with a class of
``write-file`` is included in the documentation. The following example
is a complete reStructuredText file that shows how to write a file
that is then used by a later example:

__ https://docutils.sourceforge.io/docs/ref/rst/directives.html#topic

.. literalinclude:: ../tests/configparser-read.txt
   :language: rest

Checking the contents of files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To check the contents of a file, a `topic`__ with a class of
``read-file`` containing the expected content is included in the documentation.
The following example is a complete reStructuredText file that shows how to check
the values written by the code being documented while also using this check as
part of the documentation:

__ https://docutils.sourceforge.io/docs/ref/rst/directives.html#topic

.. literalinclude:: ../tests/configparser-write.txt
   :language: rest

Checking the contents of directories
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

While :class:`~testfixtures.sybil.FileParser` itself does not offer any
facility for checking the contents of directories, Sybil's
:class:`~sybil.parsers.rest.CaptureParser`
can be used in conjunction with the existing features of a
:class:`TempDir` to illustrate the contents expected
in a directory seamlessly within the documentation.

Here's a complete reStructuredText document that illustrates this
technique: 

.. literalinclude:: ../tests/directory-contents.txt
   :language: rest

A note on line endings
~~~~~~~~~~~~~~~~~~~~~~

As currently implemented, the parser provided by testfixtures always
writes content with ``'\n'`` line separators and, when read, will always
have its line endings normalised to ``'\n'``.
If you hit any limitations caused by this, please raise an issue in the tracker on GitHub.

.. clean up:
 >>> tempdir.cleanup_all()
 >>> _tempdir.create()
 <testfixtures...
