# Copyright (c) 2008-2011 Simplistix Ltd
# See license.txt for license details.

from functools import partial
from testfixtures.compat import self_name
from testfixtures.resolve import resolve, not_there
from testfixtures.utils import wrap
from types import MethodType

import warnings

_SCALAR_TYPES = (basestring, int, float, long, bool, type(None),)

class Replacer:
    """
    These are used to manage the mocking out of objects so that units
    of code can be tested without having to rely on their normal
    dependencies.
    """

    def __init__(self, replace_returns=False):
        self.originals = {}
        self.replace_returns = replace_returns

    def _replace(self, container, name, method, value):
        if value is not_there:
            if method == 'a':
                delattr(container, name)
            if method == 'i':
                del container[name]
        else:
            if method == 'a':
                setattr(container, name, value)
            if method == 'i':
                container[name] = value

    def replace(self, target, replacement, strict=True, all=False):
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

        :param all: When `True`, the :mod:`gc` module to replace _all_ 
                    references of :param:`target` with :param:`replacement`.
                    There are few places the object cannot be replaced (e.g
                    within a frame object) but most instances of the obj
                    -- e.g. within a list, dict, nested datastructure, function
                    closure -- will be replaced.  See documention for all 
                    full notes when using this option. 

        """
        container, method, attribute, t_obj = resolve(target)
        if method is None:
            raise ValueError('target must contain at least one dot!')

        if t_obj is not_there and (strict or all):
            raise AttributeError('Original %r not found' % attribute)

        if replacement is not_there and all:
            raise TypeError("You cannot use 'not_there' with the all keyword")

        # Make sure when using 'all' that target/replacement not scalars --
        # very unsafe and may not be reversible to do so.
        if all and isinstance(t_obj, _SCALAR_TYPES):
            raise TypeError(
                "The target cannot be a scalar type when using 'all'.")
        if all and isinstance(replacement, _SCALAR_TYPES):
            raise TypeError(
                "The replacement cannot be a scalar type when using 'all'.")

        if t_obj is not_there and replacement is not_there:
            return not_there
        if (isinstance(t_obj, MethodType)
            and getattr(t_obj, self_name) is container
            and not isinstance(replacement, MethodType)):
            replacement_to_use = classmethod(replacement)
        else:
            replacement_to_use = replacement

        if all:
            _replace_all_refs(org_obj=t_obj, new_obj=replacement)
        else:
            self._replace(container, attribute, method, replacement_to_use)

        # To make the replacement reversible with the 'all' keyword, we need
        # to maintain a reference to whether the replacement was a 'all'
        # replacement or not and a reference to the original object.
        self.originals[target] = (all, t_obj, replacement,)

        if self.replace_returns:
            return replacement

    def restore(self):
        """
        Restore all the original objects that have been replaced by
        calls to the :meth:`replace` method of this :class:`Replacer`.
        """
        for target, original in tuple(self.originals.items()):
            replace_all, original_object, replacement = original
            if replace_all:
                _replace_all_refs(org_obj=replacement, new_obj=original_object)
            else:
                container, method, attribute, found = resolve(target)
                self._replace(container, attribute, method, original_object)
            del self.originals[target]

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.restore()

    def __del__(self):
        if self.originals:
            # no idea why coverage misses the following statement
            # it's covered by test_replace.TestReplace.test_replacer_del
            warnings.warn(# pragma: no cover
                'Replacer deleted without being restored, '
                'originals left: %r' % self.originals
                )


def replace(target, replacement, strict=True):
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
    r = Replacer(replace_returns=True)
    return wrap(partial(r.replace, target, replacement, strict), r.restore)


def _replace_all_refs(org_obj, new_obj):
    """
    :summary: Uses the :mod:`gc` module to replace all references to obj
              :attr:`org_obj` with :attr:`new_obj` (it tries it's best, 
              anyway). 
                      
    :param org_obj: The obj you want to replace. 
    
    :param new_obj: The new_obj you want in place of the old obj. 
    
    :returns: The org_obj
    
    Use looks like:
    
    >>> x = ('org', 1, 2, 3)
    >>> y = x
    >>> z = ('new', -1, -2, -3)
    >>> org_x = _replace_all_refs(x, z)
    >>> print x
    ('new', -1, -2, -3)
    >>> print y
    ('new', -1, -2, -3)
    >>> print org_x 
    ('org', 1, 2, 3)

    To reverse the process, do something like this:

    >>> z = _replace_all_refs(z, org_x)
    >>> del org_x
    >>> print x
    ('org', 1, 2, 3)
    >>> print y 
    ('org', 1, 2, 3)
    >>> print z
    ('new', -1, -2, -3)
        
    .. note:
        The obj returned is, by the way, the last copy of :attr:`org_obj` in 
        memory; if you don't save a copy, there is no way to put state of the 
        system back to original state.     
    
    .. warning:: 
       
       This function does not work reliably on strings, due to how the 
       Python runtime interns strings.
        
    """

    import gc as _gc
    import types as _types

    def proxy0(data):
        def proxy1(): return data
        return proxy1
    _CELLTYPE = type(proxy0(None).func_closure[0])

    _gc.collect()

    hit = False
    for referrer in _gc.get_referrers(org_obj):

        # FRAMES -- PASS THEM UP
        if isinstance(referrer, _types.FrameType):
            continue

        # DICTS
        if isinstance(referrer, dict):

            cls = None

            # THIS CODE HERE IS TO DEAL WITH DICTPROXY TYPES
            if '__dict__' in referrer and '__weakref__' in referrer:
                for cls in _gc.get_referrers(referrer):
                    if _inspect.isclass(cls) and cls.__dict__ == referrer:
                        break

            for key, value in referrer.items():
                # REMEMBER TO REPLACE VALUES ...
                if value is org_obj:
                    hit = True
                    value = new_obj
                    referrer[key] = value
                    if cls: # AGAIN, CLEANUP DICTPROXY PROBLEM
                        setattr(cls, key, new_obj)
                # AND KEYS.
                if key is org_obj:
                    hit = True
                    del referrer[key]
                    referrer[new_obj] = value

        # LISTS
        elif isinstance(referrer, list):
            for i, value in enumerate(referrer):
                if value is org_obj:
                    hit = True
                    referrer[i] = new_obj

        # SETS
        elif isinstance(referrer, set):
            referrer.remove(org_obj)
            referrer.add(new_obj)
            hit = True

        # TUPLE, FROZENSET
        elif isinstance(referrer, (tuple, frozenset,)):
            new_tuple = []
            for obj in referrer:
                if obj is org_obj:
                    new_tuple.append(new_obj)
                else:
                    new_tuple.append(obj)
            _replace_all_refs(referrer, type(referrer)(new_tuple))

        # CELLTYPE
        elif isinstance(referrer, _CELLTYPE):
            def proxy0(data):
                def proxy1(): return data
                return proxy1
            proxy = proxy0(new_obj)
            newcell = proxy.func_closure[0]
            replace_all_refs(referrer, newcell)

        # FUNCTIONS
        elif isinstance(referrer, _types.FunctionType):
            localsmap = {}
            for key in ['func_code', 'func_globals', 'func_name',
                        'func_defaults', 'func_closure']:
                orgattr = getattr(referrer, key)
                if orgattr is org_obj:
                    localsmap[key.split('func_')[-1]] = new_obj
                else:
                    localsmap[key.split('func_')[-1]] = orgattr
            localsmap['argdefs'] = localsmap['defaults']
            del localsmap['defaults']
            newfn = _types.FunctionType(**localsmap)
            replace_all_refs(referrer, newfn)

        # OTHER (IN DEBUG, SEE WHAT IS NOT SUPPORTED).
        else:
            # debug:
            # print type(referrer)
            pass

    if hit is False:
        raise AttributeError("Object '%r' not found" % org_obj)

    return org_obj


if __name__ == '__main__':

    import doctest
    doctest.testmod(optionflags=doctest.REPORT_ONLY_FIRST_FAILURE)


