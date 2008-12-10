# Copyright (c) 2008 Simplistix Ltd
# See license.txt for license details.

import os

from mock import Mock
from shutil import rmtree
from tempfile import mkdtemp
from testfixtures import compare,tempdir,should_raise,Replacer
from unittest import TestCase,TestSuite,makeSuite

class TestTempDir(TestCase):

    
    @tempdir()
    def test_simple(self,d):
        f = open(os.path.join(d.path,'something'),'wb')
        f.write('stuff')
        f.close()
        f = open(os.path.join(d.path,'.svn'),'wb')
        f.write('stuff')
        f.close()
        d.check(
            '.svn',
            'something',
            )

    @tempdir()
    def test_not_same(self,d):
        f = open(os.path.join(d.path,'something'),'wb')
        f.write('stuff')
        f.close()
        
        check = should_raise(d.check,AssertionError(
            "Sequence not as expected:\n  same:()\n first:('.svn', 'something')\nsecond:('something',)"
            ))

        check(
            '.svn',
            'something',
            )
        
    @tempdir(ignore=('.svn',))
    def test_ignore(self,d):
        f = open(os.path.join(d.path,'something'),'wb')
        f.write('stuff')
        f.close()
        f = open(os.path.join(d.path,'.svn'),'wb')
        f.write('stuff')
        f.close()
        d.check(
            'something',
            )

    def test_cleanup_properly(self):
        r = Replacer()
        try:
            m = Mock()
            d = mkdtemp()
            m.return_value = d
            r.replace('testfixtures.mkdtemp',m)

            self.failUnless(os.path.exists(d))

            self.assertFalse(m.called)
            
            @tempdir()
            def test_method(d):
                f = open(os.path.join(d.path,'something'),'wb')
                f.write('stuff')
                f.close()
                d.check(
                    'something',
                    )

            self.assertFalse(m.called)
            compare(os.listdir(d),[])

            test_method()
            
            self.assertTrue(m.called)
            self.failIf(os.path.exists(d))
            
        finally:
            r.restore()
            if os.path.exists(d):
                rmtree(d)
            
    @tempdir()
    def test_cleanup_test_deletes_dir(self,d):
        rmtree(d.path)
    
def test_suite():
    return TestSuite((
        makeSuite(TestTempDir),
        ))
