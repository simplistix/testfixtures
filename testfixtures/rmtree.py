# lamosity needed to make things reliable on Windows :-(
# (borrowed from Python's test_support.py)
import os, sys, shutil

if sys.platform.startswith("win"):
    def _waitfor(func, pathname, waitall=False):
        # Perform the operation
        func(pathname)
        # Now setup the wait loop
        if waitall:
            dirname = pathname
        else:
            dirname, name = os.path.split(pathname)
            dirname = dirname or '.'
        # Check for `pathname` to be removed from the filesystem.
        # The exponential backoff of the timeout amounts to a total
        # of ~1 second after which the deletion is probably an error
        # anyway.
        # Testing on a i7@4.3GHz shows that usually only 1 iteration is
        # required when contention occurs.
        timeout = 0.001
        while timeout < 1.0:
            # Note we are only testing for the existence of the file(s) in
            # the contents of the directory regardless of any security or
            # access rights.  If we have made it this far, we have sufficient
            # permissions to do that much using Python's equivalent of the
            # Windows API FindFirstFile.
            # Other Windows APIs can fail or give incorrect results when
            # dealing with files that are pending deletion.
            L = os.listdir(dirname)
            if not (L if waitall else name in L):
                return
            # Increase the timeout and try again
            time.sleep(timeout)
            timeout *= 2
        warnings.warn('tests may fail, delete still pending for ' + pathname,
                      RuntimeWarning, stacklevel=4)

    def _rmtree(path):
        def _rmtree_inner(path):
            for name in os.listdir(path):
                fullname = os.path.join(path, name)
                if os.path.isdir(fullname):
                    _waitfor(_rmtree_inner, fullname, waitall=True)
                    os.rmdir(fullname)
                else:
                    os.unlink(fullname)
        _waitfor(_rmtree_inner, path, waitall=True)
        _waitfor(os.rmdir, path)
else:
    _rmtree = shutil.rmtree

def rmtree(path):
    try:
        _rmtree(path)
    except OSError, e:
        # Unix returns ENOENT, Windows returns ESRCH.
        if e.errno not in (errno.ENOENT, errno.ESRCH):
            raise
