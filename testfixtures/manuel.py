from __future__ import absolute_import

# Copyright (c) 2010 Simplistix Ltd
#
# See license.txt for more details.
import re
import textwrap

from manuel import Manuel

FILEBLOCK_START = re.compile(r'^\.\.\s*topic::?\s*(.+)\b', re.MULTILINE)
FILEBLOCK_END = re.compile(r'(\n\Z|\n(?=\S))')
CLASS = re.compile(r'\s+:class:\s*(read|write)-file')

class FileBlock(object):
    def __init__(self,path,content,action):
        self.path,self.content,self.action = path,content,action

def find_file_blocks(document):
    for region in document.find_regions(FILEBLOCK_START,FILEBLOCK_END):
        lines = region.source.splitlines()
        class_ = CLASS.match(lines[1])
        if not class_:
            continue
        source = textwrap.dedent('\n'.join(lines[2:])).lstrip()
        region.parsed = FileBlock(
            region.start_match.group(1),
            source,
            class_.group(1)
            )
        document.claim_region(region)
        
def Files():
    return Manuel(parsers=[find_file_blocks],evaluaters=None,formatters=None)
