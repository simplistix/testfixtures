# Copyright (c) 2008-2011 Simplistix Ltd
# See license.txt for license details.

import atexit
import os
import warnings

from re import compile
from shutil import rmtree
from tempfile import mkdtemp
from testfixtures.comparison import compare
from testfixtures.utils import wrap


class TempDirectory:
    """
    A class representing a temporary directory on disk.

    :param ignore: A sequence of strings containing regular expression
                   patterns that match filenames that should be
                   ignored by the :class:`TempDirectory` listing and
                   checking methods.

    :param create: If `True`, the temporary directory will be created
                   as part of class instantiation.

    :param path: If passed, this should be a string containing a
                 physical path to use as the temporary directory. When
                 passed, :class:`TempDirectory` will not create a new
                 directory to use.
    """
    
    instances = set()
    atexit_setup = False
    
    #: The physical path of the :class:`TempDirectory` on disk
    path = None
    
    def __init__(self,ignore=(),create=True,path=None):
        self.ignore = []
        for regex in ignore:
            self.ignore.append(compile(regex))
        self.path = path
        self.dont_remove = bool(path)
        if create:
            self.create()

    @classmethod
    def atexit(cls):
        if cls.instances:
            warnings.warn(
                'TempDirectory instances not cleaned up by shutdown:\n'
                '%s' % ('\n'.join(i.path for i in cls.instances))
                )
        
    def create(self):
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
        return self

    def cleanup(self):
        """
        Delete the temporary directory and anything in it.
        This :class:`TempDirectory` cannot be used again unless
        :meth:`create` is called.
        """
        if self.path and os.path.exists(self.path) and not self.dont_remove:
            rmtree(self.path)
            del self.path
        if self in self.instances:
            self.instances.remove(self)

    @classmethod
    def cleanup_all(cls):
        """
        Delete all temporary directories associated with all
        :class:`TempDirectory` objects.
        """
        for i in tuple(cls.instances):
            i.cleanup()

    def actual(self,path=None,recursive=False):
        if path:
            path = self._join(path)
        else:
            path = self.path
        result = []
        if recursive:
            for dirpath,dirnames,filenames in os.walk(path):
                dirpath = '/'.join(dirpath[len(path)+1:].split(os.sep))
                if dirpath:
                    dirpath += '/'
                    result.append(dirpath)
                for name in sorted(filenames):
                    result.append(dirpath+name)
        else:
            for n in os.listdir(path):
                result.append(n)
        filtered = []
        for path in sorted(result):
            ignore = False
            for regex in self.ignore:
                if regex.search(path):
                    ignore = True
                    break
            if ignore:
                continue
            filtered.append(path)
        return filtered
    
    def listdir(self,path=None,recursive=False):
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
        actual = self.actual(path,recursive)
        if not actual:
            print 'No files or directories found.'
        for n in actual:
            print n

    def check(self,*expected):
        """
        Compare the contents of the temporary directory with the
        expected contents supplied.

        This method only checks the root of the temporary directory.

        :param expected: A sequence of strings containing the names
                         expected in the directory.
        """
        compare(expected,tuple(self.actual()))

    def check_dir(self,dir,*expected):
        """
        Compare the contents of the specified subdirectory of the
        temporary directory with the expected contents supplied.

        This method will only check the contents of the subdirectory
        specified and will not recursively check subdirectories.
        
        :param dir: The subdirectory to check, which can be:

                     * A tuple of strings, indicating that the
                       elements of the tuple should be used as directory
                       names to traverse from the root of the
                       temporary directory to find the directory to be
                       checked.

                     * A forward-slash separated string, indicating
                       the directory or subdirectory that should be
                       traversed to from the temporary directory and
                       checked.

        :param expected: A sequence of strings containing the names
                         expected in the directory.
        """
        compare(expected,tuple(self.actual(dir)))

    def check_all(self,dir,*expected):
        """
        Recursively compare the contents of the specified directory
        with the expected contents supplied.

        :param dir: The directory to check, which can be:

                     * A tuple of strings, indicating that the
                       elements of the tuple should be used as directory
                       names to traverse from the root of the
                       temporary directory to find the directory to be
                       checked.

                     * A forward-slash separated string, indicating
                       the directory or subdirectory that should be
                       traversed to from the temporary directory and
                       checked.

                     * An empty string, indicating that the whole
                       temporary directory should be checked.

        :param expected: A sequence of strings containing the paths
                         expected in the directory. These paths should
                         be forward-slash separated and relative to
                         the root of the temporary directory.
        """
        compare(expected,tuple(self.actual(dir,recursive=True)))

    def _join(self,name):
        if isinstance(name,basestring):
            name = name.split('/')
        if not name[0]:
            raise ValueError(
                'Attempt to read or write outside the temporary Directory'
                )
        return os.path.join(self.path,*name)
        
    def makedir(self,dirpath,
                # for backwards compatibility
                path=True):
        """
        Make an empty directory at the specified path within the
        temporary directory. Any intermediate subdirectories that do
        not exist will also be created.

        :param dirpath: The directory to create, which can be:
        
                        * A tuple of strings. 

                        * A forward-slash separated string.

        :returns: The full path of the created directory.
        """
        thepath = self._join(dirpath)
        os.makedirs(thepath)
        return thepath
    
    def write(self,filepath,data,
              # for backwards compatibility
              path=True):
        """
        Write the supplied data to a file at the specified path within
        the temporary directory. Any subdirectories specified that do
        not exist will also be created.

        The file will always be written in binary mode.
        
        :param filepath: The path to the file to create, which can be:
        
                         * A tuple of strings. 

                         * A forward-slash separated string.

        :param data: A string containing the data to be written.
        
        :returns: The full path of the file written.
        """
        if isinstance(filepath,basestring):
            filepath = filepath.split('/')
        if len(filepath)>1:
            dirpath = self._join(filepath[:-1])
            if not os.path.exists(dirpath):
                os.makedirs(dirpath)
        thepath = self._join(filepath)
        f = open(thepath,'wb')
        f.write(data)
        f.close()
        return thepath

    def getpath(self,path):
        """
        Return the full path on disk that corresponds to the path
        relative to the temporary directory that is passed in.

        :param path: The path to the file to create, which can be:
        
                     * A tuple of strings. 

                     * A forward-slash separated string.

        :returns: A string containing the full path.
        """
        return self._join(path)
    
    def read(self, filepath, mode='rb'):
        """
        Reading the file at the specified path within the temporary
        directory.

        The file is always read in binary mode.

        :param filepath: The path to the file to read, which can be:
        
                         * A tuple of strings. 

                         * A forward-slash separated string.

        :param mode: The mode used to open the file. Set to ``r`` if
                     you're reading and text file and not concerned
                     about line endings. Leave the default in other
                     cases.

        :returns: A string containing the data read.
        """
        f = open(self._join(filepath), mode)
        data = f.read()
        f.close()
        return data

    def __enter__(self):
        return self
    
    def __exit__(self,type,value,traceback):
        self.cleanup()

def tempdir(*args,**kw):
    """
    A decorator for making a :class:`TempDirectory` available for the
    duration of a test function.

    All arguments and parameters are passed through to the
    :class:`TempDirectory` constructor.
    """
    kw['create']=False
    l = TempDirectory(*args,**kw)
    return wrap(l.create,l.cleanup)

