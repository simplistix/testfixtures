# -*- coding: utf-8 -*-
import sys, os, pkginfo, datetime

pkg_info = pkginfo.Develop(os.path.join(os.path.dirname(__file__),'..','src'))

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx'
    ]

intersphinx_mapping = {'http://docs.python.org/dev': None}

# General
source_suffix = '.txt'
master_doc = 'index'
project = pkg_info.name

# copyright
first_year = 2010
current_year = datetime.datetime.now().year
if first_year==current_year:
    date_str = str(current_year)
else:
    date_str = '%s-%s'%(first_year,current_year)
copyright = date_str+' Simplistix Ltd' 


version = release = pkg_info.version
exclude_trees = ['_build']
unused_docs = ['description']
pygments_style = 'sphinx'

# Options for HTML output
html_theme = 'default'
htmlhelp_basename = project+'doc'

# Options for LaTeX output
latex_documents = [
  ('index',project+'.tex', project+u' Documentation',
   'Simplistix Ltd', 'manual'),
]

