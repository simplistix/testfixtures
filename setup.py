# Copyright (c) 2010 Simplistix Ltd
#
# This Software is released under the MIT License:
# http://www.opensource.org/licenses/mit-license.html
# See license.txt for more details.

from setuptools import setup

package_name = 'zope2instance'
base_dir = os.path.join(os.path.dirname(__file__))

setup(
    name=package_name,
    version='1.0',
    author='Chris Withers',
    author_email='chris@simplistix.co.uk',
    license='MIT',
    description="zc.buildout recipe for Zope 2.12+ instances.",
    long_description=open(os.path.join(base_dir,'docs','description.txt')).read(),
    # url='http://',
    classifiers=[
    'Development Status :: 5 - Production/Stable',
    'License :: OSI Approved :: MIT License',
    ],
    packages=[package_name],
    zip_safe=False,
    include_package_data=True,
    install_requires=[
        'zc.buildout',
        'ZConfig',
        'Zope2',
        'zc.recipe.egg',
    ],
    entry_points = { 
        'zc.buildout': [
             'server = %s:Instance' % package_name,
             ]
        },
    extras_require=dict(
           test=[
            'manuel',
            'mailinglogger',
            'testfixtures',
            'gocept.recipe.deploymentsandbox',
            ],
           )
    )
