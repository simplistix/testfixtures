from functools import partial
from operator import setitem
from typing import Any, TypeVar, Callable, Dict

from testfixtures.resolve import resolve, not_there, Resolved
from testfixtures.utils import wrap, extend_docstring

import warnings


def not_same_descriptor(x, y, descriptor):
    return isinstance(x, descriptor) and not isinstance(y, descriptor)


R = TypeVar('R')


class Replacer:
    """
    These are used to manage the mocking out of objects so that units
    of code can be tested without having to rely on their normal
    dependencies.
    """

    def __init__(self):
        self.originals: Dict[Any, Resolved] = {}

    def _replace(self, resolved: Resolved, value):
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
        else:
            resolved.setter(resolved.container, resolved.name, value)

    def __call__(self, target: Any, replacement: R, strict: bool = True) -> R:
        """
        Replace the specified target with the supplied replacement.
        """
        resolved = resolve(target)
        if resolved.accessor is None:
            raise ValueError('target must contain at least one dot!')
        if resolved.found is not_there and strict:
            raise AttributeError('Original %r not found' % resolved.name)

        replacement_to_use = replacement

        if isinstance(resolved.container, type):

            if not_same_descriptor(resolved.found, replacement, classmethod):
                replacement_to_use = classmethod(replacement)

            elif not_same_descriptor(resolved.found, replacement, staticmethod):
                replacement_to_use = staticmethod(replacement)

        self._replace(resolved, replacement_to_use)
        if target not in self.originals:
            self.originals[target] = resolved
        return replacement

    def replace(self, target: str, replacement: Any, strict: bool = True) -> None:
        """
        Replace the specified target with the supplied replacement.
        """
        self(target, replacement, strict)

    def restore(self) -> None:
        """
        Restore all the original objects that have been replaced by
        calls to the :meth:`replace` method of this :class:`Replacer`.
        """
        for target, original in tuple(self.originals.items()):
            self._replace(original, original.found)
            del self.originals[target]

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.restore()

    def __del__(self):
        if self.originals:
            # no idea why coverage misses the following statement
            # it's covered by test_replace.TestReplace.test_replacer_del
            warnings.warn(  # pragma: no cover
                'Replacer deleted without being restored, '
                'originals left: %r' % self.originals
                )


def replace(target: str, replacement: Any, strict: bool = True) -> Callable[[Callable], Callable]:
    """
    A decorator to replace a target object for the duration of a test
    function.
    """
    r = Replacer()
    return wrap(partial(r.__call__, target, replacement, strict), r.restore)


class Replace(object):
    """
    A context manager that uses a :class:`Replacer` to replace a single target.
    """

    def __init__(self, target: Any, replacement: R, strict: bool = True):
        self.target = target
        self.replacement = replacement
        self.strict = strict
        self._replacer = Replacer()

    def __enter__(self) -> R:
        return self._replacer(self.target, self.replacement, self.strict)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._replacer.restore()


replace_params_doc = """
:param target: A string containing the dotted-path to the
               object to be replaced. This path may specify a
               module in a package, an attribute of a module,
               or any attribute of something contained within
               a module.

:param replacement: The object to use as a replacement.

:param strict: When `True`, an exception will be raised if an
               attempt is made to replace an object that does
               not exist.
"""

# add the param docs, so we only have one copy of them!
extend_docstring(replace_params_doc,
                 [Replacer.__call__, Replacer.replace, replace, Replace])
