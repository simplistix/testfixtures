from __future__ import absolute_import

# Copyright (c) 2010-2011 Simplistix Ltd
#
# See license.txt for more details.
import re
import textwrap

from manuel import Manuel
from testfixtures import diff

FILEBLOCK_START = re.compile(r'^\.\.\s*topic::?\s*(.+)\b', re.MULTILINE)
FILEBLOCK_END = re.compile(r'(\n\Z|\n(?=\S))')
CLASS = re.compile(r'\s+:class:\s*(read|write)-file')

class FileBlock(object):
    def __init__(self,path,content,action):
        self.path,self.content,self.action = path,content,action

class FileResult(object):
    passed = True
    expected = None
    actual = None

class Files(Manuel):
    """
    A `Manuel <http://packages.python.org/manuel/>`__ plugin that
    parses certain ReST sections to read and write files in the
    configured :class:`TempDirectory`.

    :param name: This is the name of the :class:`TempDirectory` to use
                 in the Manual global namespace (ie: `globs`).

    """
    def __init__(self,name):
        self.name = name
        Manuel.__init__(self,
                        parsers=[self.parse],
                        evaluaters=[self.evaluate],
                        formatters=[self.format])
        
    def parse(self,document):
        for region in document.find_regions(FILEBLOCK_START,FILEBLOCK_END):
            lines = region.source.splitlines()
            class_ = CLASS.match(lines[1])
            if not class_:
                continue
            index = 3
            if lines[index].strip()=='::':
                index += 1
            source = textwrap.dedent('\n'.join(lines[index:])).lstrip()
            if source[-1]!='\n':
                source += '\n'
            region.parsed = FileBlock(
                region.start_match.group(1),
                source,
                class_.group(1)
                )
            document.claim_region(region)

    def evaluate(self,region, document, globs):
        if not isinstance(region.parsed, FileBlock):
            return
        block = region.parsed
        dir = globs[self.name]
        result = region.evaluated=FileResult()
        if block.action=='read':
            actual=dir.read(block.path, 'r')
            if actual!=block.content:
                result.passed = False
                result.path = block.path
                result.expected = block.content
                result.actual = actual
        if block.action=='write':
            dir.write(block.path,block.content)

    def format(self,document):
        for region in document:
            result = region.evaluated
            if not isinstance(result, FileResult):
                continue
            if not result.passed:
                region.formatted = (
                    'File "%s", line %i:\n'
                    'Reading from "%s":\n'
                    '%s' % (
                        document.location,
                        region.lineno,
                        result.path,
                        diff(result.expected,result.actual)
                        )
                    )
        
        return

