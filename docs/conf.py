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
    'python': ('https://docs.python.org/3/', None),
    'django': ('https://django.readthedocs.io/en/latest/', None),
    'pytest': ('https://docs.pytest.org/en/latest/', None),
    'sybil': ('https://sybil.readthedocs.io/en/latest/', None),
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

nitpicky = True
nitpick_ignore = [
    ('py:class', 'P'),  # param spec
    ('py:class', 'constantly._constants.NamedConstant'),  # twisted logging constants
    ('py:class', 'django.db.models.base.Model'),  # not documented upstream
    ('py:class', 'module'),  # ModuleType not documented.
    ('py:class', 'tempfile.TemporaryFile'),  # not documented as a class so type annotation broken
    ('py:class', 'testfixtures.replace.R'),  # type var
    ('py:class', 'testfixtures.utils.T'),  # type var
    ('py:class', 'testfixtures.utils.U'),  # type var
    ('py:class', 'twisted.trial.unittest.TestCase'),  # twisted doesn't use sphinx
    ('py:class', 'unittest.case.TestCase'),  # no docs, apparently
    ('py:class', 'unittest.mock._Call'),  # No docstring.
]
