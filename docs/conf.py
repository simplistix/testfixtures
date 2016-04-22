# -*- coding: utf-8 -*-
import datetime
import os
import pkginfo
import sys

on_rtd = os.environ.get('READTHEDOCS', None) == 'True'
pkg_info = pkginfo.Develop(os.path.join(os.path.dirname(__file__), '..'))

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx'
    ]

intersphinx_mapping = {'http://docs.python.org': None}

# General
source_suffix = '.txt'
master_doc = 'index'
project = pkg_info.name
copyright = '2008-2015 Simplistix Ltd, %s Chris Withers' % datetime.datetime.now().year
version = release = pkg_info.version
exclude_trees = ['_build']
exclude_patterns = ['description.txt']
pygments_style = 'sphinx'

# Options for HTML output
if on_rtd:
    html_theme = 'default'
else:
    html_theme = 'classic'
htmlhelp_basename = project+'doc'

# Options for LaTeX output
latex_documents = [
    ('index', project+'.tex', project+u' Documentation',
     'Simplistix Ltd', 'manual'),
]
