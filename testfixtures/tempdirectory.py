import atexit
import os
import warnings
from pathlib import Path
from re import compile
from tempfile import mkdtemp
from types import TracebackType
from typing import Sequence, Callable, TypeAlias, Self

from testfixtures.comparison import compare
from testfixtures.utils import wrap
from .rmtree import rmtree

PathStrings: TypeAlias = str | Sequence[str]


class TempDirectory:
    """
    A class representing a temporary directory on disk.

    :param ignore: A sequence of strings containing regular expression
                   patterns that match filenames that should be
                   ignored by the :class:`TempDirectory` listing and
                   checking methods.

    :param create: If `True`, the temporary directory will be created
                   as part of class instantiation.

    :param path: If passed, this should be a string containing an
                 absolute path to use as the temporary directory. When
                 passed, :class:`TempDirectory` will not create a new
                 directory to use.

    :param encoding: A default encoding to use for :meth:`read` and
                     :meth:`write` operations when the ``encoding`` parameter
                     is not passed to those methods.

    :param cwd: If ``True``, set the current working directory to be that of the temporary directory
                when used as a decorator or context manager.
    """

    instances = set['TempDirectory']()
    atexit_setup = False

    #: The absolute path of the :class:`TempDirectory` on disk
    path = None

    def __init__(
            self,
            path: str | Path | None = None,
            *,
            ignore: Sequence[str] = (),
            create: bool | None = None,
            encoding: str | None = None,
            cwd: bool = False,
    ):
        self.ignore = []
        for regex in ignore:
            self.ignore.append(compile(regex))
        self.path = str(path) if path else None
        self.encoding = encoding
        self.cwd = cwd
        self.original_cwd: str | None = None
        self.dont_remove = bool(path)
        if create or (path is None and create is None):
            self.create()

    @classmethod
    def atexit(cls) -> None:
        if cls.instances:
            warnings.warn(
                'TempDirectory instances not cleaned up by shutdown:\n'
                '%s' % ('\n'.join(i.path for i in cls.instances if i.path))
                )

    def create(self) -> 'TempDirectory':
        """
        Create a temporary directory for this instance to use if one
        has not already been created.
        """
        if self.path:
            return self
        self.path = mkdtemp()
        self.instances.add(self)
        if not self.__class__.atexit_setup:
            atexit.register(self.atexit)
            self.__class__.atexit_setup = True
        if self.cwd:
            self.original_cwd = os.getcwd()
            os.chdir(self.path)
        return self

    def cleanup(self) -> None:
        """
        Delete the temporary directory and anything in it.
        This :class:`TempDirectory` cannot be used again unless
        :meth:`create` is called.
        """
        if self.cwd and self.original_cwd:
            os.chdir(self.original_cwd)
            self.original_cwd = None
        if self.path and os.path.exists(self.path) and not self.dont_remove:
            rmtree(self.path)
            del self.path
        if self in self.instances:
            self.instances.remove(self)

    @classmethod
    def cleanup_all(cls) -> None:
        """
        Delete all temporary directories associated with all
        :class:`TempDirectory` objects.
        """
        for i in tuple(cls.instances):
            i.cleanup()

    def actual(
            self,
            path: PathStrings | None = None,
            recursive: bool = False,
            files_only: bool = False,
            followlinks: bool = False,
    ) -> list[str]:
        path = self._join(path)

        result: list[str] = []
        if recursive:
            for dirpath, dirnames, filenames in os.walk(path, followlinks=followlinks):
                dirpath = '/'.join(dirpath[len(path)+1:].split(os.sep))
                if dirpath:
                    dirpath += '/'

                for dirname in dirnames:
                    if not files_only:
                        result.append(dirpath+dirname+'/')

                for name in sorted(filenames):
                    result.append(dirpath+name)
        else:
            for n in os.listdir(path):
                result.append(n)

        filtered = []
        for result_path in sorted(result):
            ignore = False
            for regex in self.ignore:
                if regex.search(result_path):
                    ignore = True
                    break
            if ignore:
                continue
            filtered.append(result_path)
        return filtered

    def listdir(self, path: PathStrings | None = None, recursive: bool = False) -> None:
        """
        Print the contents of the specified directory.

        :param path: The path to list, which can be:

                     * `None`, indicating the root of the temporary
                       directory should be listed.

                     * A tuple of strings, indicating that the
                       elements of the tuple should be used as directory
                       names to traverse from the root of the
                       temporary directory to find the directory to be
                       listed.

                     * A forward-slash separated string, indicating
                       the directory or subdirectory that should be
                       traversed to from the temporary directory and
                       listed.

        :param recursive: If `True`, the directory specified will have
                          its subdirectories recursively listed too.
        """
        actual = self.actual(path, recursive)
        if not actual:
            print('No files or directories found.')
        for n in actual:
            print(n)

    def compare(
            self,
            expected: Sequence[str],
            path: PathStrings | None = None,
            files_only: bool = False,
            recursive: bool = True,
            followlinks: bool = False,
    ) -> None:
        """
        Compare the expected contents with the actual contents of the temporary
        directory. An :class:`AssertionError` will be raised if they are not the
        same.

        :param expected: A sequence of strings containing the paths
                         expected in the directory. These paths should
                         be forward-slash separated and relative to
                         the root of the temporary directory.

        :param path: The path to use as the root for the comparison,
                     relative to the root of the temporary directory.
                     This can either be:

                     * A tuple of strings, making up the relative path.

                     * A forward-slash separated string.

                     If it is not provided, the root of the temporary
                     directory will be used.

        :param files_only: If specified, directories will be excluded from
                           the list of actual paths used in the comparison.

        :param recursive: If ``False``, only the direct contents of
                          the directory specified by ``path`` will be included
                          in the actual contents used for comparison.

        :param followlinks: If ``True``, symlinks and hard links
                            will be followed when recursively building up
                            the actual list of directory contents.
        """

        __tracebackhide__ = True
    
        compare(expected=sorted(expected),
                actual=tuple(self.actual(
                    path, recursive, files_only, followlinks
                )),
                recursive=False)

    def _join(self, parts: str | Sequence[str] | None) -> str:
        if self.path is None:
            raise RuntimeError('Instantiated with create=False and .create() not called')
        # make things platform independent
        if parts is None:
            return self.path
        if isinstance(parts, str):
            parts = parts.split('/')
        relative = os.sep.join(parts).rstrip(os.sep)
        if relative.startswith(os.sep):
            if relative.startswith(self.path):
                return relative
            raise ValueError(
                'Attempt to read or write outside the temporary Directory'
                )
        return os.path.join(self.path, relative)

    def makedir(self, dirpath: PathStrings) -> str:
        """
        Make an empty directory at the specified path within the
        temporary directory. Any intermediate subdirectories that do
        not exist will also be created.

        :param dirpath: The directory to create, which can be:

                        * A tuple of strings.

                        * A forward-slash separated string.

        :returns: The absolute path of the created directory.
        """
        thepath = self._join(dirpath)
        os.makedirs(thepath)
        return thepath

    def write(self, filepath: PathStrings, data: str | bytes, encoding: str | None = None) -> str:
        """
        Write the supplied data to a file at the specified path within
        the temporary directory. Any subdirectories specified that do
        not exist will also be created.

        The file will always be written in binary mode. The data supplied must
        either be bytes or an encoding must be supplied to convert the string
        into bytes.

        :param filepath: The path to the file to create, which can be:

                         * A tuple of strings.

                         * A forward-slash separated string.

        :param data:

          :class:`bytes` containing the data to be written, or a :class:`str`
          if ``encoding`` has been supplied.

        :param encoding: The encoding to be used if data is not bytes. Should
                         not be passed if data is already bytes.

        :returns: The absolute path of the file written.
        """
        filepath_parts = filepath.split('/') if isinstance(filepath, str) else filepath
        if len(filepath_parts) > 1:
            dirpath = self._join(filepath_parts[:-1])
            if not os.path.exists(dirpath):
                os.makedirs(dirpath)
        thepath = self._join(filepath_parts)
        encoding = encoding or self.encoding
        if encoding is not None:
            if isinstance(data, bytes):
                raise TypeError('Cannot specify encoding when data is bytes')
            data = data.encode(encoding)
        elif isinstance(data, str):
            data = data.encode()
        with open(thepath, 'wb') as f:
            f.write(data)
        return thepath

    def as_string(self, path: str | Sequence[str] | None = None) -> str:
        """
        Return the full path on disk that corresponds to the path
        relative to the temporary directory that is passed in.

        :param path: The path to the file to create, which can be:

                     * A tuple of strings.

                     * A forward-slash separated string.

        :returns: A string containing the absolute path.

        """
        return self._join(path)

    #: .. deprecated:: 7
    #:
    #:   Use :meth:`as_string` instead.
    getpath = as_string

    def as_path(self, path: PathStrings | None = None) -> Path:
        """
        Return the :class:`~pathlib.Path` that corresponds to the path
        relative to the temporary directory that is passed in.

        :param path: The path to the file to create, which can be:

                     * A tuple of strings.

                     * A forward-slash separated string.
        """
        return Path(self._join(path))

    def __truediv__(self, other: str) -> Path:
        return self.as_path() / other

    def read(self, filepath: PathStrings, encoding: str | None = None) -> str | bytes:
        """
        Reads the file at the specified path within the temporary
        directory.

        The file is always read in binary mode. Bytes will be returned unless
        an encoding is supplied, in which case a unicode string of the decoded
        data will be returned.

        :param filepath: The path to the file to read, which can be:

                         * A tuple of strings.

                         * A forward-slash separated string.

        :param encoding: The encoding used to decode the data in the file.

        :returns:

          The contents of the file as a :class:`str` or :class:`bytes`, if ``encoding``
          is not specified.
        """
        with open(self._join(filepath), 'rb') as f:
            data = f.read()
        encoding = encoding or self.encoding
        if encoding is not None:
            return data.decode(encoding)
        return data

    def __enter__(self) -> Self:
        return self

    def __exit__(
            self,
            exc_type: type[BaseException] | None,
            value: BaseException | None,
            traceback: TracebackType | None,
    ) -> None:
        self.cleanup()


def tempdir(
        path: str | Path | None = None,
        *,
        ignore: Sequence[str] = (),
        encoding: str | None = None,
        cwd: bool = False,
) -> Callable[[Callable], Callable]:
    """
    A decorator for making a :class:`TempDirectory` available for the
    duration of a test function.

    All arguments and parameters are passed through to the
    :class:`TempDirectory` constructor.
    """
    l = TempDirectory(path, ignore=ignore, encoding=encoding, cwd=cwd, create=False)
    return wrap(l.create, l.cleanup)
