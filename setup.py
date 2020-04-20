# Copyright (c) 2008-2014 Simplistix Ltd, 2015-2020 Chris Withers
# See license.txt for license details.

import os

from setuptools import setup, find_packages

name = 'testfixtures'
base_dir = os.path.dirname(__file__)

optional = [
    'mock;python_version<"3"',
    'zope.component',
    'django<2;python_version<"3"',
    'django;python_version>="3"',
    'sybil',
    'twisted'
]

setup(
    name=name,
    version=open(os.path.join(base_dir, name, 'version.txt')).read().strip(),
    author='Chris Withers',
    author_email='chris@simplistix.co.uk',
    license='MIT',
    description=("A collection of helpers and mock objects "
                 "for unit tests and doc tests."),
    long_description=open(os.path.join(base_dir, 'README.rst')).read(),
    url='https://github.com/Simplistix/testfixtures',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    extras_require=dict(
        test=['pytest>=3.6',
              'pytest-cov',
              'pytest-django',
              ]+optional,
        docs=['sphinx']+optional,
        build=['setuptools-git', 'wheel', 'twine']
    )
)
