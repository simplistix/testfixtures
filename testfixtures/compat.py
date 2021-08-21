# compatibility module for different python versions
import sys

PY_VERSION = sys.version_info[:2]

PY_36_PLUS = PY_VERSION >= (3, 6)
PY_37_PLUS = PY_VERSION >= (3, 7)
PY_310_PLUS = PY_VERSION >= (3, 10)


if PY_VERSION > (3, 0):

    PY2 = False
    PY3 = True

    Bytes = bytes
    Unicode = str
    basestring = str
    BytesLiteral = lambda x: x.encode('latin1')
    UnicodeLiteral = lambda x: x

    class_type_name = 'class'
    ClassType = type
    exception_module = 'builtins'
    new_class = type
    self_name = '__self__'
    from io import StringIO
    xrange = range
    from itertools import zip_longest
    from functools import reduce
    from collections.abc import Iterable
    from abc import ABC

else:

    PY2 = True
    PY3 = False

    Bytes = str
    Unicode = unicode
    basestring = basestring
    BytesLiteral = lambda x: x
    UnicodeLiteral = lambda x: x.decode('latin1')

    class_type_name = 'type'
    from types import ClassType
    exception_module = 'exceptions'
    from new import classobj as new_class
    self_name = 'im_self'
    from StringIO import StringIO
    xrange = xrange
    from itertools import izip_longest as zip_longest
    reduce = reduce
    from collections import Iterable
    from abc import ABCMeta
    ABC = ABCMeta('ABC', (object,), {}) # compatible with Python 2 *and* 3
