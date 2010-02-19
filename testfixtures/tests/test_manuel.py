# Copyright (c) 2010 Simplistix Ltd
#
# See license.txt for more details.

import re

from manuel import Document, Manuel
from manuel import capture,codeblock
from mock import Mock
from testfixtures import compare, Comparison as C
from testfixtures.manuel import Files,FileBlock,evaluate_file_block,format_code_block
from unittest import TestCase,makeSuite,TestSuite

class TestManuel(TestCase):

    def test_multiple_files(self):
        d = Document("""

.. topic:: file.txt
 :class: write-file

  line 1

  line 2
  line 3

.. topic:: file2.txt
 :class: read-file


  line 4

  line 5
  line 6

""")
        d.parse_with(Files())
        compare([
                None,
                C(FileBlock,
                  path='file.txt',
                  content="line 1\n\nline 2\nline 3\n",
                  action='write'),
                C(FileBlock,
                  path='file2.txt',
                  content='line 4\n\nline 5\nline 6\n',
                  action='read'),
                ],[r.parsed for r in d])
        

    def test_file_followed_by_text(self):
        d = Document("""

.. topic:: file.txt
 :class: write-file

  .. code-block:: python

  print "hello"
  out = 'there'

  foo = 'bar'

This is just some normal text!
""")
        d.parse_with(Files())
        compare([
                None,
                C(FileBlock,
                  path='file.txt',
                  content='.. code-block:: python\n\nprint "hello"'
                          '\nout = \'there\'\n\nfoo = \'bar\'\n',
                  action='write'),
                None,
                ],[r.parsed for r in d])
    
    def test_red_herring(self):
        d = Document("""
.. topic:: file.txt
 :class: not-a-file

  print "hello"
  out = 'there'

""")
        d.parse_with(Files())
        compare([r.parsed for r in d],[None])

    def test_no_class(self):
        d = Document("""
.. topic:: file.txt

  print "hello"
  out = 'there'

""")
        d.parse_with(Files())
        compare([r.parsed for r in d],[None])
    
    def test_unclaimed_works(self):
        # a test manuel
        CLASS = re.compile(r'^\s+:class:',re.MULTILINE)
        class Block(object):
            def __init__(self,source): self.source = source
        def find_class_blocks(document):
            for region in document.find_regions(CLASS):
                region.parsed = Block(region.source)
                document.claim_region(region)
        def Test():
            return Manuel(parsers=[find_class_blocks])

        # now our test
        d = Document("""

.. topic:: something-else
 :class: not-a-file
  line 1
  line 2
  line 3

""")
        d.parse_with(Files()+Test())
        # now check FileBlock didn't mask class block
        compare([
                None,
                C(Block,
                  source=' :class:\n'),
                None,
                ],[r.parsed for r in d])

    def test_evaluate_read(self):
        pass

    def test_evaulate_write(self):
        pass

    def test_formatter_write(self):
        pass

    def test_formatter_read_ok(self):
        pass

    def test_formatter_read_fail(self):
        pass
    
