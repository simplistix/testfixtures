# Copyright (c) 2008-2014 Simplistix Ltd, 2015 onwards Chris Withers
# See license.txt for license details.

import os

from setuptools import setup, find_packages

name = 'testfixtures'
base_dir = os.path.dirname(__file__)

optional = [
    'django',
    'sybil>=6',
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
        'Programming Language :: Python :: 3',
    ],
    packages=find_packages(),
    zip_safe=False,
    package_data={'testfixtures': ['py.typed']},
    include_package_data=True,
    python_requires=">=3.7",
    extras_require=dict(
        test=['mypy',
              'pytest>=7.1',
              'pytest-cov',
              'pytest-django',
              ]+optional,
        docs=['sphinx', 'furo']+optional,
        build=['setuptools-git', 'wheel', 'twine']
    )
)
