# Copyright (c) 2010-2011 Simplistix Ltd
#
# See license.txt for more details.

import re

from manuel import Document, Region, RegionContainer, Manuel
from manuel import capture,codeblock
from mock import Mock
from testfixtures import compare, Comparison as C, TempDirectory
from testfixtures.manuel import Files,FileBlock,FileResult
from unittest import TestCase,makeSuite,TestSuite

class TestContainer(RegionContainer):
    def __init__(self,attr,*blocks):
        self.regions = []
        for block in blocks:
            region = Region(0,' ')
            setattr(region,attr,block)
            self.regions.append(region)

class TestManuel(TestCase):

    def tearDown(self):
        TempDirectory.cleanup_all()
        
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
        d.parse_with(Files('td'))
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
        

    def test_ignore_literal_blocking(self):
        d = Document("""
.. topic:: file.txt
 :class: write-file

  ::

    line 1

    line 2
    line 3
""")
        d.parse_with(Files('td'))
        compare([
                None,
                C(FileBlock,
                  path='file.txt',
                  content="line 1\n\nline 2\nline 3\n",
                  action='write'),
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
        d.parse_with(Files('td'))
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
        d.parse_with(Files('td'))
        compare([r.parsed for r in d],[None])

    def test_no_class(self):
        d = Document("""
.. topic:: file.txt

  print "hello"
  out = 'there'

""")
        d.parse_with(Files('td'))
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
        d.parse_with(Files('td')+Test())
        # now check FileBlock didn't mask class block
        compare([
                None,
                C(Block,
                  source=' :class:\n'),
                None,
                ],[r.parsed for r in d])

    def test_evaluate_non_fileblock(self):
        m = Mock()
        d = TestContainer('parsed',m)
        d.evaluate_with(Files('td'),globs={})
        compare([None],[r.evaluated for r in d])
        compare(m.call_args_list,[])
        compare(m.method_calls,[])

    def test_evaluate_read_same(self):
        dir = TempDirectory()
        dir.write('foo','content')
        d = TestContainer('parsed',FileBlock('foo','content','read'))
        d.evaluate_with(Files('td'),globs={'td':dir})
        compare([C(FileResult,
                   passed=True,
                   expected=None,
                   actual=None)],
                [r.evaluated for r in d])

    def test_evaluate_read_difference(self):
        dir = TempDirectory()
        dir.write('foo','actual')
        d = TestContainer('parsed',FileBlock('foo','expected','read'))
        d.evaluate_with(Files('td'),globs={'td':dir})
        compare([C(FileResult,
                   passed=False,
                   path='foo',
                   expected='expected',
                   actual='actual')],
                [r.evaluated for r in d])

    def test_evaulate_write(self):
        dir = TempDirectory()
        d = TestContainer('parsed',FileBlock('foo','content','write'))
        d.evaluate_with(Files('td'),globs={'td':dir})
        compare([C(FileResult,
                   passed=True,
                   expected=None,
                   actual=None)],
                [r.evaluated for r in d])
        dir.check('foo')
        compare(dir.read('foo'),'content')

    def test_formatter_non_fileblock(self):
        d = TestContainer('evaluated',object)
        d.format_with(Files('td'))
        compare(d.formatted(),'')

    def test_formatter_passed(self):
        d = TestContainer('evaluated',FileResult())
        d.format_with(Files('td'))
        compare(d.formatted(),'')

    def test_formatter_failed(self):
        r = FileResult()
        r.passed = False
        r.path = '/foo/bar'
        r.expected = 'same\nexpected\n'
        r.actual = 'same\nactual\n'
        d = TestContainer('evaluated',r)
        d.format_with(Files('td'))
        compare('File "<memory>", line 0:\n'
                'Reading from "/foo/bar":\n'
                '@@ -1,3 +1,3 @@\n'
                ' same\n'
                '-expected\n'
                '+actual\n ',
                d.formatted()
                )

    
