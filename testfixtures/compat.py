# compatibility module for different python versions
import sys

PY_VERSION = sys.version_info[:2]

PY_37_PLUS = PY_VERSION >= (3, 7)
PY_310_PLUS = PY_VERSION >= (3, 10)
