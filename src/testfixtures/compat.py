# compatibility module for different python versions
import sys
from typing import Tuple

PY_VERSION: Tuple[int, int] = sys.version_info[:2]

PY_312_PLUS: bool = PY_VERSION >= (3, 12)
PY_313_PLUS: bool = PY_VERSION >= (3, 13)
