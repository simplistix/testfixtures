# Copyright (c) 2008-2014 Simplistix Ltd
# See license.txt for license details.

import os, sys

if sys.version_info[:2] > (3, 0):
    from configparser import RawConfigParser
else:
    from ConfigParser import RawConfigParser
    
from setuptools import setup, find_packages

name = 'testfixtures'
base_dir = os.path.dirname(__file__)

# read test requirements from tox.ini
config = RawConfigParser()
config.read(os.path.join(base_dir, 'tox.ini'))
test_requires = []
for item in config.get('testenv', 'deps').split():
    test_requires.append(item)
# Tox doesn't need itself, but we need it for testing.
test_requires.append('tox')
# an optional dependency, but we want it present dev 
test_requires.append('zope.component')
# coveralls needed for travis
test_requires.append('coveralls')

setup(
    name=name,
    version=open(os.path.join(base_dir,name,'version.txt')).read().strip(),
    author='Chris Withers',
    author_email='chris@simplistix.co.uk',
    license='MIT',
    description="A collection of helpers and mock objects for unit tests and doc tests.",
    long_description=open(os.path.join(base_dir,'docs','description.txt')).read(),
    url='http://www.simplistix.co.uk/software/python/testfixtures',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],    
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    extras_require=dict(
        test=test_requires,
        build=['sphinx', 'pkginfo', 'setuptools-git', 'wheel', 'twine']
    )
)
