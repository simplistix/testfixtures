from __future__ import with_statement
# Copyright (c) 2008 Simplistix Ltd
# See license.txt for license details.

import os

from doctest import DocTestSuite,ELLIPSIS
from testfixtures import TempDirectory
from unittest import TestSuite

from logging import getLogger

class DemoTempDirectory:

    def test_simple(self):
        """
        >>> os.path.exists(temp_dir.path)
        True

        You can manually create files in the directory:
        
        >>> f = open(os.path.join(temp_dir.path,'something'),'wb')
        >>> f.write('stuff')
        >>> f.close()

        TempDirectory also provides a handy method for doing so:
        
        >>> temp_dir.write('.svn','stuff')
        
        There's a handy method for listing the contents of the
        directory:
        
        >>> temp_dir.listdir()
        .svn
        something

        Likewise, you can read from files in the directory:
        
        >>> open(os.path.join(temp_dir.path,'.svn'),'rb').read()
        'stuff'

        Or, you can use the handy method:

        >>> temp_dir.read('something')
        'stuff'
        """
        
    def test_subpaths(self):
        """
        You can work with files and directories below the root temp
        dir with following methods:

        >>> temp_dir.makedir('test')
        >>> temp_dir.listdir()
        test
        >>> os.path.isdir(os.path.join(temp_dir.path,'test'))
        True

        You can also make directory structures easily:
        
        >>> temp_dir.makedir(('another','test'))
        >>> temp_dir.listdir()
        another
        test

        `listdir` can also be asked to list subdirectories:
        
        >>> temp_dir.listdir('another')
        test
        >>> temp_dir.listdir(('another','test'))

        `makedir` will also return the created path if requested:
        
        >>> temp_dir.makedir('foo',path=True)
        '...foo'
        
        `write` handles subpaths:

        >>> temp_dir.write(('another','file.txt'),'data')
        >>> open(os.path.join(temp_dir.path,'another','file.txt'),'rb').read()
        'data'

        You can also write directly into a subdirectory that doesn't
        exist:

        >>> temp_dir.write(('new','file'),'bar')
        >>> temp_dir.read(('new','file'))
        'bar'

        `read` handles subpaths:

        >>> temp_dir.read(('another','file.txt'))
        'data'
        """

    def test_return_path(self):
        """
        If you want the path created when you use `write`, you
        can do:
        
        >>> temp_dir.write('filename','data',path=True)
        '...filename'
        """

    def test_ignore(self):
        """
        TempDirectories can also be set up to ignore certain files:
        
        >>> d = TempDirectory(ignore=('.svn',))
        >>> d.write('.svn','stuff')
        >>> temp_dir.listdir()
        """
        
class TestTempDirectory:

    def test_cleanup(self):
        """
        >>> d = TempDirectory()
        >>> p = d.path
        >>> os.path.exists(p)
        True
        >>> d.write('something','stuff')
        >>> d.cleanup()
        >>> os.path.exists(p)
        False
        """

    def test_cleanup_all(self):
        """
        If you create several TempDirecories during a doctest,
        or if exceptions occur while running them,
        it can create clutter on disk.
        For this reason, it's recommended to use the classmethod
        TempDirectory.cleanup_all() as a tearDown function
        to remove them all:

        >>> d1 = TempDirectory()
        >>> d2 = TempDirectory()

        Some sanity checks:

        >>> os.path.exists(d1.path)
        True
        >>> os.path.exists(d2.path)
        True

        Now we show the function in action:

        >>> TempDirectory.cleanup_all()

        >>> os.path.exists(d1.path)
        False
        >>> os.path.exists(d2.path)
        False
        """

    def test_with_statement(self):
        """
        >>> with TempDirectory() as d:
        ...    p = d.path
        ...    print os.path.exists(p)
        ...    d.write('something','stuff')
        True
        >>> os.path.exists(p)
        False
        """

# using a set up and teardown function
# gets rid of the need for the imports in
# doc tests

def setUp(test):
    test.globs['temp_dir']=TempDirectory()

def tearDown(test):
    TempDirectory.cleanup_all()
    
def test_suite():
    return TestSuite((
        DocTestSuite(setUp=setUp,tearDown=tearDown,
                     optionflags=ELLIPSIS),
        ))
