# -*- coding: utf-8 -*-
import datetime
import os
import time

import pkg_resources

on_rtd = os.environ.get('READTHEDOCS', None) == 'True'
build_date = datetime.datetime.utcfromtimestamp(int(os.environ.get('SOURCE_DATE_EPOCH', time.time())))

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx'
    ]

intersphinx_mapping = {
    'https://docs.python.org/3/': None,
    'https://django.readthedocs.io/en/latest/': None,
    'https://docs.pytest.org/en/latest/': None,
    'https://sybil.readthedocs.io/en/latest/': None,
    'https://zopecomponent.readthedocs.io/en/latest/': None,
}

# General
source_suffix = '.txt'
master_doc = 'index'
project = 'testfixtures'
copyright = '2008-2015 Simplistix Ltd, 2016-%s Chris Withers' % build_date.year
version = release = pkg_resources.get_distribution(project).version
exclude_trees = ['_build']
pygments_style = 'sphinx'

# Options for HTML output
html_theme = 'furo'
htmlhelp_basename = project+'doc'

# Options for LaTeX output
latex_documents = [
    ('index', project+'.tex', project+u' Documentation',
     'Simplistix Ltd', 'manual'),
]

exclude_patterns = ['**/furo.js.LICENSE.txt']
