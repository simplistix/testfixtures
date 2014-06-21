# Copyright (c) 2011-2013 Simplistix Ltd
# See license.txt for license details.

# This module contains bits and pieces to achieve compatibility across all the
# versions of python supported.

import doctest
import manuel
import re
import sys
import textwrap

from manuel.codeblock import (
    CODEBLOCK_START,
    CODEBLOCK_END,
    CodeBlock,
    execute_code_block,
    )

# version markers

from ..compat import PY2 as py_2
py_27_plus = sys.version_info[:2] >=  (2, 7)
py_33_plus = sys.version_info[:2] >=  (3, 3)
py_34_plus = sys.version_info[:2] >=  (3, 4)

# Python 2.6/2.7 compatibility stuff

BYTE_LITERALS = re.compile("^b('.*')$", re.MULTILINE)

def find_code_blocks(document):
    for region in document.find_regions(CODEBLOCK_START, CODEBLOCK_END):
        start_end = CODEBLOCK_START.search(region.source).end()
        source = textwrap.dedent(region.source[start_end:])
        if py_2:
            source = BYTE_LITERALS.sub('\\1', source)
        source = 'from __future__ import print_function\n'+ source
        source_location = '%s:%d' % (document.location, region.lineno)
        code = compile(source, source_location, 'exec', 0, True)
        document.claim_region(region)
        region.parsed = CodeBlock(code, source)
        
class Manuel(manuel.Manuel):
    def __init__(self):
        manuel.Manuel.__init__(self, [find_code_blocks], [execute_code_block])

if py_2:
    class DocTestChecker(doctest.OutputChecker):
        def check_output(self, want, got, optionflags):
            want = BYTE_LITERALS.sub('\\1', want)
            return doctest.OutputChecker.check_output(
                self, want, got, optionflags
                )
else:
    DocTestChecker = doctest.OutputChecker
    
# The following is adapted from Python 2.7
# Copyright 2001-2010 Python Software Foundation. All rights reserved.
# Copyright 2000 BeOpen.com. All rights reserved.
# Copyright 1995-2000 Corporation for National Research Initiatives. All rights reserved.
# Copyright 1991-1995 Stichting Mathematisch Centrum. All rights reserved.
class WarningMessage(object):
    _WARNING_DETAILS = ("message", "category", "filename", "lineno", "file",
                        "line")
    def __init__(self, message, category, filename, lineno, file=None,
                    line=None):
        local_values = locals()
        for attr in self._WARNING_DETAILS:
            setattr(self, attr, local_values[attr])
        self._category_name = category.__name__ if category else None

class catch_warnings(object):
    def __init__(self, record=True):
        if not record: # pragma: no cover
            raise TypeError('This implementation only supports record=True')
        self._module = sys.modules['warnings']
        self._entered = False

    def __enter__(self):
        if self._entered:  # pragma: no cover
            raise RuntimeError("Cannot enter %r twice" % self)
        self._entered = True
        self._filters = self._module.filters
        self._module.filters = self._filters[:]
        self._showwarning = self._module.showwarning
        log = []
        def showwarning(*args, **kwargs):
            log.append(WarningMessage(*args, **kwargs))
        self._module.showwarning = showwarning
        return log

    def __exit__(self, *exc_info):
        if not self._entered:  # pragma: no cover
            raise RuntimeError("Cannot exit %r without entering first" % self)
        self._module.filters = self._filters
        self._module.showwarning = self._showwarning
