from importlib import metadata
import datetime
import os
import time

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
source_suffix = '.rst'
master_doc = 'index'
project = 'testfixtures'
copyright = '2008-2015 Simplistix Ltd, 2016 onwards Chris Withers'
release = metadata.version(project)
exclude_trees = ['_build']
pygments_style = 'sphinx'
autodoc_typehints = 'description'

# Options for HTML output
html_theme = 'furo'
htmlhelp_basename = project+'doc'

exclude_patterns = ['**/furo.js.LICENSE.txt']

autodoc_member_order = 'bysource'

nitpicky = True
nitpick_ignore = [
    ('py:class', 'P'),  # param spec
    ('py:class', '~P'),  # param spec
    ('py:class', 'constantly._constants.NamedConstant'),  # twisted logging constants
    ('py:class', 'django.db.models.base.Model'),  # not documented upstream
    ('py:class', 'module'),  # ModuleType not documented.
    ('py:class', 'tempfile.TemporaryFile'),  # not documented as a class so type annotation broken
    ('py:class', 'testfixtures.comparison.S'),  # type var
    ('py:class', 'testfixtures.comparison.S_'),  # type var
    ('py:class', 'testfixtures.comparison.T'),  # type var
    ('py:class', 'testfixtures.datetime.MockedCurrent'),  # internal class that shouldn't be doc'ed
    ('py:class', 'testfixtures.replace.R'),  # type var
    ('py:class', 'testfixtures.shouldraise.E'),  # type var
    ('py:class', 'testfixtures.tempdirectory.P'),  # type var
    ('py:class', 'testfixtures.utils.T'),  # type var
    ('py:class', 'testfixtures.utils.U'),  # type var
    ('py:class', 'twisted.trial.unittest.TestCase'),  # twisted doesn't use sphinx
    ('py:class', 'unittest.case.TestCase'),  # no docs, apparently
    ('py:class', 'unittest.mock._Call'),  # No docstring.
]

try:
    import mock
except ImportError:
    pass
else:
    # If the mock backport is installed when docs are built, don't warn.
    # This is common for development: if you see broken refs to Mock or _Call,
    # then `uv sync --all-groups --all-extras --no-extra mock-backport`.
    nitpick_ignore.extend([
        # ('py:class', 'mock.mock._Call'),
        # ('py:class', 'mock.mock.Mock'),
    ])
