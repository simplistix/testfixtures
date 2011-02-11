# Copyright (c) 2008-2011 Simplistix Ltd
# See license.txt for license details.

import os
from setuptools import setup, find_packages

name = 'testfixtures'
base_dir = os.path.dirname(__file__)

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
    install_requires=(
        'zope.dottedname',
        ),
    extras_require=dict(
        test=[
            # used in our own tests
            'mock','manuel',
            # required to test optional features
            'zope.component',
            ],
        )
    )
