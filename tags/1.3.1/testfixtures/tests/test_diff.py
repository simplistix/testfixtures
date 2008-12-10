# Copyright (c) 2008 Simplistix Ltd
# See license.txt for license details.

from unittest import TestCase,TestSuite,makeSuite

from testfixtures import diff

class TestDiff(TestCase):

    def test_example(self):
        actual = diff('''
        line1
        line2
        line3
        ''',
                      '''
        line1
        line changed
        line3
        ''')
        expected = '''@@ -1,5 +1,5 @@
 
         line1
-        line2
+        line changed
         line3
         '''
        self.assertEqual(
            expected,
            actual,
            '\n%r\n!=\n%r'%(expected,actual)
            )
        
    def test_no_newlines(self):
        actual = diff('x','y')
        expected = '''@@ -1,1 +1,1 @@
-x
+y'''
        self.assertEqual(
            expected,
            actual,
            '\n%r\n!=\n%r'%(expected,actual)
            )
    
def test_suite():
    return TestSuite((
        makeSuite(TestDiff),
        ))
