# Copyright (c) 2011-2013 Simplistix Ltd, 2015 Chris Withers
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
py_33_plus = sys.version_info[:2] >= (3, 3)
py_34_plus = sys.version_info[:2] >= (3, 4)
py_35_plus = sys.version_info[:2] >= (3, 5)

# Python 2.7 compatibility stuff

BYTE_LITERALS = re.compile("^b('.*')$", re.MULTILINE)


def find_code_blocks(document):
    for region in document.find_regions(CODEBLOCK_START, CODEBLOCK_END):
        start_end = CODEBLOCK_START.search(region.source).end()
        source = textwrap.dedent(region.source[start_end:])
        if py_2:
            source = BYTE_LITERALS.sub('\\1', source)
        source = 'from __future__ import print_function\n' + source
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
