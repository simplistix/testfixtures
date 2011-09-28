# Copyright (c) 2010 Simplistix Ltd
#
# See license.txt for more details.

from datetime import datetime
from doctest import REPORT_NDIFF,ELLIPSIS
from manuel import doctest,codeblock,capture
from manuel.testing import TestSuite
from os.path import dirname,join,pardir
from pkg_resources import require
from testfixtures import compare, TempDirectory

import buildout_versions
import os
import re
import zc.buildout.testing

class Fixer:

    def __init__(self,*filters):
        self.filters = filters
    def __call__(self,in_):
        out_ = []
        for line in in_.split('\n'):
            for f in self.filters:
                line = f(line)
                if line is None:
                    break
            if line is None:
                continue
            elif isinstance(line,list):
                out_.extend(line)
            else:
                out_.append(line)
        return '\n'.join(out_)

def setUp(test):
    zc.buildout.testing.buildoutSetUp(test)

    # set up any required eggs
    zc.buildout.testing.install('zc.recipe.egg',test)

    # get some useful bits
    g = test.globs
    write = g['write']
    system = g['system']
    buildout = g['buildout']
    buildout_dir = TempDirectory(path=os.getcwd())

    # set up some packages
    buildout_dir.write('sample_package/setup.py','''
from setuptools import setup
setup(name='sample_package')
''')

    buildout_dir.write('package_a/setup.py','''
from setuptools import setup
setup(name='package_a',version='1.0',install_requires='package_b')
''')
    system(buildout+' setup package_a bdist_egg')
    
    buildout_dir.write('package_b/setup.py','''
from setuptools import setup
setup(name='package_b',version='2.0')
''')
    system(buildout+' setup package_b bdist_egg')

    buildout_dir.write('PackageC/setup.py','''
from setuptools import setup
setup(name='PackageC',version='3.0',install_requires='packaged')
''')
    system(buildout+' setup PackageC bdist_egg')

    buildout_dir.write('PackageD/setup.py','''
from setuptools import setup
setup(name='PackageD',version='4.0')
''')
    system(buildout+' setup PackageD bdist_egg')
    buildout_dir.write('PackageD/setup.py','''
from setuptools import setup
setup(name='PackageD',version='5.0')
''')
    system(buildout+' setup PackageD bdist_egg')

    def buildout_line(line):
        # ignore the $ bin/buildout line
        if not line.startswith('$ bin/buildout'):
            return line

    def couldnt_find(line):
        # ignore spurious "Couldn't find " lines
        if not line.startswith("Couldn't find index page"):
            return line

    spec_re = re.compile('([a-z\.\-]+) = \d')
    def normalise_versions(line):
        # normalise versions to those currently installed
        line = line.replace('\r','')
        match = spec_re.match(line)
        if match:
            package = match.group(1)
            # don't try and fix versions for our test packages
            if not (package.lower().startswith('package') or package=='python'):
                version = require(package)[0].version
                line = '%s = %s' % (package,version)
        return line

    def our_index(line):
        if '<our index>' in line:
            line = []
            line.append('find-links =')
            for name in (
                'package_a','package_b',
                'PackageC','PackageD',
                ):
                line.append(
                    '  '+test.globs['start_server'](
                        join(buildout_dir.path,name,'dist')
                             )
                    )
        return line

    def splat_buildout_dir(line):
        return line.replace(
            "'.../sample_package'",
            repr(os.path.join(buildout_dir.path,'sample_package'))
            )

    time_re = re.compile('\d{4}-\d{2}-\d{2} [\d:.]+')
    def fix_time(line):
        return time_re.sub(str(datetime(
                   2010, 7, 30, 15, 44, 45, 23559
                   )),line)

    fix_buildout = Fixer(
        normalise_versions,
        fix_time,
        our_index,
        )

    fix_expected = Fixer(
        buildout_line,
        normalise_versions,
        splat_buildout_dir,
        )

    fix_actual = Fixer(
        couldnt_find,
        normalise_versions,
        )
    
    # the buildout runner and checkers
    def run_buildout(buildout_cfg,expected):
        # setup buildout_versions as a development egg
        write('buildout.cfg','''
[buildout]
develop = %s
parts =
''' % join(dirname(buildout_versions.__file__),pardir,pardir))
        system(buildout)
        # run the buildout we were given
        write('buildout.cfg',fix_buildout(buildout_cfg))
        actual = system(buildout)
        compare(fix_expected(expected),fix_actual(actual))
        
    g['run_buildout'] = run_buildout
    g['buildout_dir'] = buildout_dir
    g['fix_buildout'] = fix_buildout

def test_suite():
    m = capture.Manuel()
    m += codeblock.Manuel()
    return TestSuite(
        m,
        join(dirname(__file__),pardir,pardir,pardir,'docs','use.txt'),
        setUp=setUp,
        tearDown=zc.buildout.testing.buildoutTearDown,
        )
