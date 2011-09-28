# Copyright (c) 2010-2011 Simplistix Ltd
#
# This Software is released under the MIT License:
# http://www.opensource.org/licenses/mit-license.html
# See license.txt for more details.

from setuptools import setup, find_packages

import os

base_dir = os.path.join(os.path.dirname(__file__))

setup(
    name='buildout-versions',
    version='1.7',
    author='Chris Withers',
    author_email='chris@simplistix.co.uk',
    license='MIT',
    description="zc.buildout extension to display and record versions of packages used.",
    long_description=open(os.path.join(base_dir,'docs','description.txt')).read(),
    url='http://packages.python.org/buildout-versions',
    classifiers=[
    'Development Status :: 5 - Production/Stable',
    'License :: OSI Approved :: MIT License',
    ],
    packages = find_packages('src'),
    package_dir = {'':'src'},
    zip_safe=False,
    include_package_data=True,
    install_requires=[
        'zc.buildout>=1.5.0',
    ],
    entry_points = { 
        'zc.buildout.extension': [
             'default = buildout_versions:start',
             ],
        'zc.buildout.unloadextension': [
             'default = buildout_versions:finish',
             ],
        },
    extras_require=dict(
           test=[
            'manuel',
            'testfixtures',
            'zc.recipe.egg',
            ],
           )
    )
