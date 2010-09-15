# Copyright (c) 2010 Simplistix Ltd
# See license.txt for license details.
from __future__ import with_statement

from buildout_versions import _constrain
from pkg_resources import parse_requirements, Requirement
from testfixtures import LogCapture,ShouldRaise,compare
from unittest import TestSuite,makeSuite,TestCase
from zc.buildout.easy_install import IncompatibleVersionError

class FakeInstaller:
    def __init__(self,versions):
        self._versions = versions
        
class TestConstrain(TestCase):

    def setUp(self):
        self._versions = {}
        self.i=FakeInstaller(self._versions)
        self.logging = LogCapture('zc.buildout.easy_install')

    def tearDown(self):
        self.logging.uninstall()

    def _check(self,requirement,expected):
        result = _constrain(
            self.i,
            tuple(parse_requirements(requirement))[0]
            )
        self.failUnless(isinstance(result,Requirement))
        compare(expected,str(result))
        
    def test_normal(self):
        self._versions['a-package']='1.0'
        self._check('a_package','a-package==1.0')
        self.logging.check()
    
    def test_extras(self):
        self._versions['a-package']='1.0'
        self._check('a_package[some,thing]',
                    'a-package[some,thing]==1.0')
        self.logging.check()
    
    def test_capitalisation(self):
        self._versions['a-package']='1.0'
        self._check('A-Package','A-Package==1.0')
        self.logging.check()

    def test_no_version(self):
        self._check('a_package','a-package')
        self.logging.check()
    
    def test_incompatible_version(self):
        self._versions['a-package']='1.0'
        with ShouldRaise(IncompatibleVersionError(
                'Bad version','1.0'
                )):
            self._check('a-package==2.0','xxx')
        self.logging.check(
            ('zc.buildout.easy_install',
             'ERROR',
             "The version, 1.0, is not consistent with"
             " the requirement, 'a-package==2.0'.")
            )

def test_suite():
    return TestSuite((
        makeSuite(TestConstrain),
        ))

