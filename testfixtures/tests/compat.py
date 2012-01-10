# Copyright (c) 2012 Simplistix Ltd
# See license.txt for license details.

# This module contains bits and pieces to achieve compatibility across all the
# versions of python supported.

import sys

py_27_plus = sys.version_info[:2] == (2, 7)
