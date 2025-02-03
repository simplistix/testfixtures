from operator import setitem
from typing import Any, Callable, Tuple, TypeAlias, Literal

from testfixtures import not_there


Setter: TypeAlias = Callable[[object, str, Any], None] | Callable[[Any, int, Any], None] | None
Key: TypeAlias = Tuple[int, Setter, str | int | None]

class Resolved:

    def __init__(self, container: Any, setter: Setter, name: Any, found: Any):
        self.container: Any = container
        self.setter = setter
        self.name = name
        self.found: Any = found

    def key(self) -> Key:
        return id(self.container), self.setter, self.name

    def __repr__(self) -> str:
        return f'<Resolved: {self.found}>'


def resolve(dotted_name: str, container: Any | None = None, sep: str = '.') -> Resolved:
    names = dotted_name.split(sep)
    used = names.pop(0)
    found: Any
    if container is None:
        found = __import__(used)
        container = found
    else:
        assert not used, 'Absolute traversal not allowed when container supplied'
        used = ''
        found = container
    setter: Setter = None
    name: Any = None
    for name in names:
        container = found
        used += '.' + name
        try:
            found = getattr(found, name)
            setter = setattr
        except AttributeError:
            try:
                if sep != '.':
                    raise ImportError
                __import__(used)
            except ImportError:
                setter = setitem
                try:
                    found = found[name]
                except KeyError:
                    found = not_there
                except TypeError:
                    try:
                        name = int(name)
                    except ValueError:
                        setter = setattr
                        found = not_there
                    else:
                        found = found[name]
            else:
                found = getattr(found, name)
                setter = getattr
            if found is not_there:
                break
    return Resolved(container, setter, name, found)


class _Reference:

    @classmethod
    def classmethod(cls) -> None:  # pragma: no cover
        pass

    @staticmethod
    def staticmethod() -> None:  # pragma: no cover
        pass


class_type = type(_Reference)
classmethod_type = type(_Reference.classmethod)
