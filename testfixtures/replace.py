# Copyright (c) 2008-2011 Simplistix Ltd
# See license.txt for license details.

from functools import partial
from testfixtures.resolve import resolve, not_there
from testfixtures.utils import wrap
from types import MethodType

import warnings

class Replacer:
    """
    These are used to manage the mocking out of objects so that units
    of code can be tested without having to rely on their normal
    dependencies.
    """

    def __init__(self,replace_returns=False):
        self.originals = {}
        self.replace_returns=replace_returns

    def _replace(self, container, name, method, value, strict=True):
        if value is not_there:
            if method=='a':
                delattr(container, name)
            if method=='i':
                del container[name]
        else:
            if method=='a':
                setattr(container, name, value)
            if method=='i':
                container[name] = value

    def replace(self,target,replacement,strict=True):
        """
        Replace the specified target with the supplied replacement.

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
        container, method, attribute, t_obj = resolve(target)
        if method is None:
            raise ValueError('target must contain at least one dot!')
        if t_obj is not_there and strict:
            raise AttributeError('Original %r not found'%attribute)
        if t_obj is not_there and replacement is not_there:
            return not_there
        if (isinstance(t_obj,MethodType)
            and t_obj.im_self is container
            and not isinstance(replacement,MethodType)):
            replacement_to_use = classmethod(replacement)
        else:
            replacement_to_use = replacement
        self._replace(container, attribute, method, replacement_to_use, strict)
        if target not in self.originals:
            self.originals[target] = t_obj
        if self.replace_returns:
            return replacement

    def restore(self):
        """
        Restore all the original objects that have been replaced by
        calls to the :meth:`replace` method of this :class:`Replacer`.
        """
        for target,original in tuple(self.originals.items()):
            container, method, attribute, found = resolve(target)
            self._replace(container, attribute, method, original, strict=False)
            del self.originals[target]
            
    def __enter__(self):
        return self
    
    def __exit__(self,type,value,traceback):
        self.restore()

    def __del__(self):
        if self.originals:
            # no idea why coverage misses the following statement
            # it's covered by test_replace.TestReplace.test_replacer_del
            warnings.warn( # pragma: no cover
                'Replacer deleted without being restored, '
                'originals left: %r' % self.originals
                )

def replace(target,replacement,strict=True):
    """
    A decorator to replace a target object for the duration of a test
    function.

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
    r  = Replacer(replace_returns=True)
    return wrap(partial(r.replace,target,replacement,strict),r.restore)

