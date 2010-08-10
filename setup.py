# Copyright (c) 2010 Simplistix Ltd
#
# This Software is released under the MIT License:
# http://www.opensource.org/licenses/mit-license.html
# See license.txt for more details.

from setuptools import setup

import os

base_dir = os.path.join(os.path.dirname(__file__))
setup(
    name='buildout-versions',
    version='1.2',
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
    packages=['buildout_versions'],
    zip_safe=False,
    include_package_data=True,
    install_requires=[
        'zc.buildout',
    ],
    entry_points = { 
        'zc.buildout.extension': [
             'default = %s:start' % 'buildout_versions',
             ],
        'zc.buildout.unloadextension': [
             'default = %s:finish' % 'buildout_versions',
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
