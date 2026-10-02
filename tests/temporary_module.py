import importlib
import sys
from contextlib import contextmanager
from types import ModuleType
from typing import Iterator

from testfixtures import TempDir, Replace


@contextmanager
def temporary_module(name: str, content: str) -> Iterator[ModuleType]:
    with TempDir() as d:
        d.write(f'{name}.py', content)
        with Replace(target=sys.path, container=sys, name='path', replacement=[d.as_string()]):
            try:
                yield importlib.import_module(name)
            finally:
                if name in sys.modules:
                    del sys.modules[name]
