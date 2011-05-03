# Copyright (c) 2011 Simplistix Ltd
# See license.txt for license details.
from buildout_versions import start, _constrain
from pkg_resources import parse_requirements, Requirement
from testfixtures import LogCapture, compare, replace
from unittest import TestSuite, makeSuite, TestCase
from zc.buildout.easy_install import Installer
from zc.buildout.easy_install import default_versions

class TestStartExtension(TestCase):
    """Test the start extension.
    """

    def setUp(self):
        self.buildout_config = {
            'buildout': {'versions': 'versions'},
            'versions': {'A-Package': '1.0'},
            }
        self.i = Installer(versions=self.buildout_config['versions'])
        self.logging = LogCapture('zc.buildout.easy_install')
        # Run the extension, which includes installing our patches.
        start(self.buildout_config)
        # Some other extension, like mr.developer, may run after us
        # and call 'default_versions' after changing something to the
        # buildout config versions.  We should be fine with that.
        self.buildout_config['versions']['extra-lower'] = '4.2'
        self.buildout_config['versions']['ExtraUpper'] = '4.2'
        default_versions(self.buildout_config['versions'])

    def tearDown(self):
        self.logging.uninstall()

    def _check(self, requirement, expected):
        parsed_req = tuple(parse_requirements(requirement))[0]
        result = self.i._constrain(parsed_req)
        self.failUnless(isinstance(result, Requirement))
        compare(expected, str(result))

    def test_normal(self):
        self._check('A-Package', 'A-Package==1.0')
        self.logging.check()

    def test_lowercase(self):
        self._check('a_package', 'a-package==1.0')
        self.logging.check()

    def test_uppercase(self):
        self._check('A_PACKAGE', 'A-PACKAGE==1.0')
        self.logging.check()

    def test_sanity(self):
        # A non-pinned package should still be reported as such.
        self._check('B_Package', 'B-Package')
        self.logging.check()

    def test_extra(self):
        # A pin added after our extension has run is picked up as well.
        self._check('extra-lower', 'extra-lower==4.2')
        self.logging.check()

    def test_extra_lower(self):
        # A pin added after our extension has run is not lowercased
        # though.
        self._check('ExtraUpper', 'ExtraUpper')
        self.logging.check()

class DummyInstaller:

    def __init__(self):
        self._versions = {}
        
class Test_constrain(TestCase):

    def setUp(self):
        self.Installer = DummyInstaller()

    @replace('buildout_versions.is_distribute',False)
    def test_setuptools_no_distribute(self):
        compare(
            Requirement.parse('setuptools'),
            _constrain(self.Installer,Requirement.parse('setuptools'))
            )

    @replace('buildout_versions.is_distribute',True)
    def test_setuptools_distribute(self):
        compare(
            Requirement.parse('distribute'),
            _constrain(self.Installer,Requirement.parse('setuptools'))
            )
    
def test_suite():
    return TestSuite((
        makeSuite(TestStartExtension),
        makeSuite(Test_constrain),
        ))
