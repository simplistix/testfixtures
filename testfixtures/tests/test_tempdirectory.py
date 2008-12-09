# Copyright (c) 2008 Simplistix Ltd
# See license.txt for license details.

import os

from doctest import DocTestSuite
from testfixtures import TempDirectory
from unittest import TestSuite

from logging import getLogger

class DemoTempDirectory:

    def test_simple(self):
        """
        >>> os.path.exists(temp_dir.path)
        True
        >>> f = open(os.path.join(temp_dir.path,'something'),'wb')
        >>> f.write('stuff')
        >>> f.close()
        >>> f = open(os.path.join(temp_dir.path,'.svn'),'wb')
        >>> f.write('stuff')
        >>> f.close()
        >>> temp_dir.listdir()
        .svn
        something
        """
        
    def test_ignore(self):
        """
        TempDirectories can also be set up to ignore certain files:
        
        >>> d = TempDirectory(ignore=('.svn',))
        >>> f = open(os.path.join(d.path,'.svn'),'wb')
        >>> f.write('stuff')
        >>> f.close()
        >>> temp_dir.listdir()
        """
        
class TestTempDirectory:

    def test_cleanup(self):
        """
        >>> d = TempDirectory()
        >>> p = d.path
        >>> os.path.exists(p)
        True
        >>> f = open(os.path.join(d.path,'something'),'wb')
        >>> f.write('stuff')
        >>> f.close()
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

# using a set up and teardown function
# gets rid of the need for the imports in
# doc tests

def setUp(test):
    test.globs['temp_dir']=TempDirectory()

def tearDown(test):
    TempDirectory.cleanup_all()
    
def test_suite():
    return TestSuite((
        DocTestSuite(setUp=setUp,tearDown=tearDown),
        ))
