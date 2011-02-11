from zope.component import getSiteManager
from zope.component.registry import Components

class TestComponents:
    """
    A helper for providing a sterile registry when testing
    with :mod:`zope.component`.

    Instantiation will install an empty registry that will be returned
    by :func:`zope.component.getSiteManager`.
    """
    def __init__(self):
        self.registry = Components('Testing')
        self.old = getSiteManager.sethook(lambda:self.registry)

    def uninstall(self):
        """
        Remove the sterile registry and replace it with the one that
        was in place before this :class:`TestComponents` was
        instantiated.
        """
        getSiteManager.sethook(self.old)

        
