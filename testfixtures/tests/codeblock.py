# Copyright (c) 2011 Simplistix Ltd
#
# See license.txt for more details.

import manuel
import textwrap

from manuel.codeblock import (
    CODEBLOCK_START,
    CODEBLOCK_END,
    CodeBlock,
    execute_code_block,
    )

# Python 2.5 compatibility stuff

def find_code_blocks(document):
    for region in document.find_regions(CODEBLOCK_START, CODEBLOCK_END):
        start_end = CODEBLOCK_START.search(region.source).end()
        source = textwrap.dedent(region.source[start_end:])
        source = 'from __future__ import with_statement\n' + source
        source_location = '%s:%d' % (document.location, region.lineno)
        code = compile(source, source_location, 'exec', 0, True)
        document.claim_region(region)
        region.parsed = CodeBlock(code)
        
class Manuel(manuel.Manuel):
    def __init__(self):
        manuel.Manuel.__init__(self, [find_code_blocks], [execute_code_block])
