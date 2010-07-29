# Copyright (c) 2010 Simplistix Ltd
#
# See license.txt for more details.

from doctest import REPORT_NDIFF,ELLIPSIS
from glob import glob
from manuel import doctest,codeblock
from manuel.testing import TestSuite
from os.path import dirname,join,pardir
from pkg_resources import working_set, Requirement
from testfixtures import TempDirectory
from testfixtures.manuel import Files
from zope.testing import renormalizing

import os
import re
import shutil
import zc.buildout.testing

def install_with_deps(test,*packages):
    base = os.path.join(
        test.globs['sample_buildout'],'eggs'
        )

    seen = set()

    for dist in working_set.resolve(
        [Requirement.parse(p) for p in packages]
        ):
        name = dist.project_name
        if name in seen:
            continue
        seen.add(name)
        open(os.path.join(base, name+'.egg-link'), 'w'
             ).write(dist.location)

checker = renormalizing.RENormalizing([
    zc.buildout.testing.normalize_path,
    (re.compile(
    "Couldn't find index page for '[a-zA-Z0-9.]+' "
    "\(maybe misspelled\?\)"
    "\n"
    ), ''),
    (re.compile('#![^\n]+\n'), ''),                
    (re.compile('-\S+-py\d[.]\d(-\S+)?.egg'),
     '-pyN.N.egg',
    ),
    ])

def setUp(test):
    zc.buildout.testing.buildoutSetUp(test)
    # do a develop install of the recipe
    zc.buildout.testing.install_develop('zope2instance', test)
    # recipe eggs
    zc.buildout.testing.install('gocept.recipe.deploymentsandbox', test)
    zc.buildout.testing.install('mailinglogger', test)
    zc.buildout.testing.install('zc.recipe.egg', test)
    # install Zope2 along with all its dependencies
    install_with_deps(test,'Zope2')
    # setup the tempdir for testfixtures.manuel
    test.globs['td']=TempDirectory(path=os.getcwd())
    # do offline buildouts to make things a little quicker
    # and avoid spurious errors
    test.globs['buildout'] = test.globs['buildout']#+' -o'
    
def test_suite():
    m =  doctest.Manuel(
        optionflags=REPORT_NDIFF|ELLIPSIS,
        checker=checker,
        )
    m += codeblock.Manuel()
    m += Files('td')
    return TestSuite(
        m,
        join(dirname(__file__),pardir,'docs','use.txt'),
        setUp=setUp,
        tearDown=zc.buildout.testing.buildoutTearDown,
        )
