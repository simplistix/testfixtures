# Copyright (c) 2010 Simplistix Ltd
#
# This Software is released under the MIT License:
# http://www.opensource.org/licenses/mit-license.html
# See license.txt for more details.

from setuptools import setup

package_name = 'zope2instance'
package_dir = os.path.join(os.path.dirname(__file__),package_name)

setup(
    name=package_name,
    version='1.0',
    author='Chris Withers',
    author_email='chris@simplistix.co.uk',
    license='MIT',
    description="zc.buildout recipe for Zope 2.12+ instances.",
    # long_description=open(os.path.join(package_dir,'docs','description.txt')).read(),
    # url='http://',
    classifiers=[
    'Development Status :: 5 - Production/Stable',
    # 'Development Status :: 6 - Mature',
    'License :: OSI Approved :: MIT License',
    ],
    packages=['zope2instance'],
    zip_safe=False,
    include_package_data=True,
    install_requires=[
    'Zope2 >= 2.12.0',
    ],
    entry_points = { 
        'zc.buildout': [
             'server = %s:Instance' % package_name,
             ]
        },
    extras_require=dict(
           test=[
            'mock',
            'testfixtures',
            ],
           )
    )

# to build and upload the eggs, do:
# python setup.py sdist bdist_egg bdist_wininst register upload
# ...or...
#  bin/buildout setup setup.py sdist bdist_egg bdist_wininst register upload
# ...on a unix box!

# To check how things will show on pypi, install docutils and then:
# bin/buildout -q setup setup.py --long-description | rst2html.py --link-stylesheet --stylesheet=http://www.python.org/styles/styles.css > dist/desc.html
