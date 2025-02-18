import os
import warnings
from contextlib import contextmanager
from functools import partial
from gc import get_referrers, get_referents
from operator import setitem, getitem
from types import ModuleType, MethodType, TracebackType
from typing import Any, TypeVar, Callable, Tuple, Generic, Self, Iterator

from testfixtures.utils import wrap, extend_docstring
from .resolve import resolve, not_there, Resolved, classmethod_type, class_type, Key

Accessor = Callable[[Any, str], Any]


def not_same_descriptor(x: Any, y: Any, descriptor: type[classmethod] | type[staticmethod]) -> bool:
    return isinstance(x, descriptor) and not isinstance(y, descriptor)


R = TypeVar('R')


class Replacer:
    """
    These are used to manage the mocking out of objects so that units
    of code can be tested without having to rely on their normal
    dependencies.
    """

    def __init__(self) -> None:
        self.originals: dict[Key, Tuple[Any, Resolved]] = {}

    def _replace(self, resolved: Resolved, value: Any) -> None:
        if value is not_there:
            if resolved.setter is setattr:
                try:
                    delattr(resolved.container, resolved.name)
                except AttributeError:
                    pass
            if resolved.setter is setitem:
                try:
                    del resolved.container[resolved.name]
                except KeyError:
                    pass
        elif resolved.setter is not None:
            resolved.setter(resolved.container, resolved.name, value)

    def __call__(
            self,
            target: Any,
            replacement: R,
            strict: bool = True,
            container: Any | None = None,
            accessor: Accessor | None = None,
            name: str | None = None,
            sep: str = '.',
    ) -> R:
        """
        Replace the specified target with the supplied replacement.
        """
        if name is None and accessor is not None:
            raise TypeError('accessor is not used unless name is specified')

        if isinstance(target, str) and not name:
            resolved = resolve(target, container, sep)
        else:
            if container is None:
                container = target

            name = name or getattr(target, '__name__', None)
            if name is None:
                raise TypeError('name must be specified when target is not a string')
            else:
                if accessor is None:
                    try:
                        accessor = getitem
                        found = accessor(container, name)
                    except KeyError:
                        found = not_there
                    except TypeError:
                        accessor = getattr
                        found = accessor(container, name, not_there)
                else:
                    try:
                        found = accessor(container, name)
                    except (KeyError, AttributeError):
                        found = not_there

            if strict and not (found is not_there or target is container):
                if found is not target:
                    if isinstance(found, MethodType):
                        raise TypeError(
                            'Cannot replace methods on instances with strict=True, '
                            'replace on class or use strict=False'
                        )
                    raise AssertionError(
                        f'{accessor} of {name!r} from {container!r} gave {found!r}, '
                        f'expected {target}'
                    )

            resolved = Resolved(
                container,
                setitem if accessor is getitem else setattr,
                name,
                found
            )

        if resolved.setter is None:
            raise ValueError('target must contain at least one dot!')

        if resolved.found is not_there and strict:
            raise AttributeError('Original %r not found' % resolved.name)

        if (
                hasattr(resolved.container, '__dict__') and
                resolved.setter is setattr and
                resolved.name not in resolved.container.__dict__
        ):
            if strict:
                raise AttributeError(
                    f'{resolved.container!r} has __dict__ but {resolved.name!r} is not in it'
                )
            else:
                resolved.found = not_there


        replacement_to_use: Any = replacement

        if isinstance(resolved.container, type):

            # if we have a descriptor, don't accidentally use the result of its __get__ method:
            if resolved.name in resolved.container.__dict__:
                resolved.found = resolved.container.__dict__[resolved.name]

            if not_same_descriptor(resolved.found, replacement, classmethod):
                replacement_to_use = classmethod(replacement)  # type: ignore[arg-type]

            elif not_same_descriptor(resolved.found, replacement, staticmethod):
                replacement_to_use = staticmethod(replacement)  # type: ignore[arg-type]

        self._replace(resolved, replacement_to_use)
        key = resolved.key()
        if key not in self.originals:
            self.originals[key] = target, resolved
        return replacement

    def replace(self, target: Any, replacement: Any, strict: bool = True,
                container: Any | None = None, accessor: Accessor | None = None, name: str | None = None) -> None:
        """
        Replace the specified target with the supplied replacement.
        """
        self(target, replacement, strict, container, accessor, name)

    def in_environ(self, name: str, replacement: Any) -> None:
        """
        This method provides a convenient way of ensuring an environment variable
        in :any:`os.environ` is set to a particular value.

        If you wish to ensure that an environment variable is *not* present,
        then use :any:`not_there` as the ``replacement``.
        """
        self(os.environ, name=name, accessor=getitem, strict=False,
             replacement=not_there if replacement is not_there else str(replacement))

    def _find_container(
            self, attribute: Callable, name: str | None, break_on_static: bool
    ) -> tuple[Any, Any]:
        for referrer in get_referrers(attribute):
            if break_on_static and isinstance(referrer, staticmethod):
                return None, referrer
            elif isinstance(referrer, dict):
                if referrer.get(name) is attribute:
                    for container in get_referrers(referrer):
                        if isinstance(container, type):
                            return container, None
        return None, None

    def on_class(self, attribute: Callable, replacement: Any, name: str | None = None) -> None:
        """
        This method provides a convenient way to replace methods, static methods and class
        methods on their classes.

        If the attribute being replaced has a ``__name__`` that differs from the attribute
        name on the class, such as that returned by poorly implemented decorators, then
        ``name`` must be used to provide the correct name.
        """
        name = name or getattr(attribute, '__name__', None)
        if not callable(attribute):
            name_text = f' named {name!r} ' if name else ' '
            raise TypeError(f'attribute{name_text}must be a method')
        container = None
        if isinstance(attribute, classmethod_type):
            for referred in get_referents(attribute):
                if isinstance(referred, class_type):
                    container = referred
        else:
            container, staticmethod_ = self._find_container(attribute, name, break_on_static=True)
            if staticmethod_ is not None:
                container, _ = self._find_container(staticmethod_, name, break_on_static=False)

        if container is None:
            raise AttributeError(f'could not find container of {attribute!r} using name {name!r}')

        self(container, name=name, accessor=getattr, replacement=replacement)

    def in_module(self, target: Any, replacement: Any, module: ModuleType | None = None) -> None:
        """
        This method provides a convenient way to replace targets that are module globals,
        particularly functions or other objects with a ``__name__`` attribute.

        If an object has been imported into a module other than the one where it has been
        defined, then ``module`` should be used to specify the module where you would
        like the replacement to occur.
        """
        container = module or resolve(target.__module__).found
        name = target.__name__
        self(container, name=name, accessor=getattr, replacement=replacement)

    def restore(self) -> None:
        """
        Restore all the original objects that have been replaced by
        calls to the :meth:`replace` method of this :class:`Replacer`.
        """
        for id_, (target, resolved) in tuple(self.originals.items()):
            self._replace(resolved, resolved.found)
            del self.originals[id_]

    def __enter__(self) -> Self:
        return self

    def __exit__(
            self,
            exc_type: type[BaseException] | None,
            value: BaseException | None,
            traceback: TracebackType | None,
    ) -> None:
        self.restore()

    def __del__(self) -> None:
        if self.originals:
            # no idea why coverage misses the following statement
            # it's covered by test_replace.TestReplace.test_replacer_del
            warnings.warn(  # pragma: no cover
                'Replacer deleted without being restored, '
                'originals left: %r' % {k:v for (k, v) in self.originals.values()}
                )


def replace(
        target: Any, replacement: Any, strict: bool = True,
        container: Any | None = None, accessor: Accessor | None = None, name: str | None = None, sep: str ='.'
) -> Callable[[Callable], Callable]:
    """
    A decorator to replace a target object for the duration of a test
    function.
    """
    r = Replacer()
    return wrap(
        partial(r.__call__, target, replacement, strict, container, accessor, name, sep),
        r.restore
    )


@contextmanager
def replace_in_environ(name: str, replacement: Any) -> Iterator[None]:
    """
    This context manager provides a quick way to use :meth:`Replacer.in_environ`.
    """
    with Replacer() as r:
        r.in_environ(name, replacement)
        yield


@contextmanager
def replace_on_class(
        attribute: Callable, replacement: Any, name: str | None = None
) -> Iterator[None]:
    """
    This context manager provides a quick way to use :meth:`Replacer.on_class`.
    """
    with Replacer() as r:
        r.on_class(attribute, replacement, name)
        yield


@contextmanager
def replace_in_module(
        target: Any, replacement: Any, module: ModuleType | None = None
) -> Iterator[None]:
    """
    This context manager provides a quick way to use :meth:`Replacer.in_module`.
    """
    with Replacer() as r:
        r.in_module(target, replacement, module)
        yield


class Replace(Generic[R]):
    """
    A context manager that uses a :class:`Replacer` to replace a single target.
    """

    def __init__(
            self, target: Any, replacement: R, strict: bool = True,
            container: Any | None = None, accessor: Accessor | None = None, name: str | None = None, sep: str ='.'
    ):
        self.target = target
        self.replacement = replacement
        self.strict = strict
        self.container: Any = container
        self.accessor = accessor
        self.name = name
        self.sep: str = sep
        self._replacer = Replacer()

    def __enter__(self) -> R:
        return self._replacer(
            self.target,
            self.replacement,
            self.strict,
            self.container,
            self.accessor,
            self.name,
            self.sep,
        )

    def __exit__(
            self,
            exc_type: type[BaseException] | None,
            value: BaseException | None,
            traceback: TracebackType | None,
    ) -> None:
        self._replacer.restore()


replace_params_doc = """
:param target: 

  This must be one of the following:
  
  - A string containing the dotted-path to the object to be replaced, in which case it will be 
    resolved the the object to be replaced.
    
    This path may specify a module in a package, an attribute of a module, or any attribute of 
    something contained within a module.
    
  - The container of the object to be replaced, in which case ``name`` must be specified.
  
  - The object to be replaced, in which case ``container`` must be specified.
    ``name`` must also be specified if it cannot be obtained from the ``__name__`` attribute
    of the object to be replaced.

:param replacement: The object to use as a replacement.

:param strict: When `True`, an exception will be raised if an
               attempt is made to replace an object that does
               not exist or if the object that is obtained using the ``accessor`` to 
               access the ``name`` from the ``container`` is not identical to the ``target``.
               
:param container: 
  The container of the object from which ``target`` can be accessed using either
  :func:`getattr` or :func:`~operator.getitem`.
  
:param accessor:
  Either :func:`getattr` or :func:`~operator.getitem`. If not supplied, this will be inferred.
  
:param name:
  The name used to access the ``target`` from the ``container`` using the ``accessor``.
  If required but not specified, the ``__name__`` attribute of the ``target`` will be used. 
  
:param sep:
  When ``target`` is a string, this is the separator between traversal segments. 
"""

# add the param docs, so we only have one copy of them!
extend_docstring(replace_params_doc,
                 [Replacer.__call__, Replacer.replace, replace, Replace])
