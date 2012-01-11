# Copyright (c) 2012 Simplistix Ltd
# See license.txt for license details.

# This module contains bits and pieces to achieve compatibility across all the
# versions of python supported.

import sys

py_27_plus = sys.version_info[:2] == (2, 7)

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
    def __str__(self):
        return ("{message : %r, category : %r, filename : %r, lineno : %s, "
                    "line : %r}" % (self.message, self._category_name,
                                    self.filename, self.lineno, self.line))

class catch_warnings(object):
    def __init__(self, record=True):
        if not record:
            raise TypeError('This implementation only support record=True')
        self._module = sys.modules['warnings']
        self._entered = False

    def __enter__(self):
        if self._entered:
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
        if not self._entered:
            raise RuntimeError("Cannot exit %r without entering first" % self)
        self._module.filters = self._filters
        self._module.showwarning = self._showwarning
