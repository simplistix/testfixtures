# Copyright (c) 2008-2011 Simplistix Ltd
# See license.txt for license details.

import os
from ConfigParser import RawConfigParser
from setuptools import setup, find_packages

name = 'testfixtures'
base_dir = os.path.dirname(__file__)

# read test requirements from tox.ini
config = RawConfigParser()
config.read(os.path.join(base_dir, 'tox.ini'))
test_requires = []
for item in config.get('testenv', 'deps').split():
    if item.endswith('==dev'):
        item = item[:-5]
    test_requires.append(item)
# Tox doesn't need itself, but we need it for testing.
test_requires.append('tox')
# Optional dependencies here:
test_requires.extend([
        'zope.component',
        ])

setup(
    name=name,
    version=file(os.path.join(base_dir,name,'version.txt')).read().strip(),
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
    ],    
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    extras_require=dict(
        test=test_requires,
        )
    )
