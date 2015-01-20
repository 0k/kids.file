# -*- coding: utf-8 -*-

from __future__ import with_statement

import os
import sys
import tempfile
import pwd
import grp
import gzip
import shutil
import locale


PY3 = sys.version_info[0] >= 3

if PY3:
    str = str
    unicode = str
    bytes = bytes
    basestring = (str,bytes)
else:
    class FileNotFoundError(OSError):
        pass

    class IsADirectoryError(OSError):
        pass


def file_get_contents(filename, binary=False, encoding=None, uncompress=None):
    """Returns string content from filename"""
    ## notes that uncompress and encoding seems to be the same thing.

    mode = "rb" if binary else "r"

    open_action = gzip.open if uncompress == "zlib" else open

    if PY3:
        with open_action(filename, mode, encoding=encoding) as f:
            s = f.read()
        if isinstance(s, bytes) and not binary:
            ## in PY3, gzip.open doesn't encode the output:
            s = s.decode(locale.getpreferredencoding())
    else:
        with open_action(filename, mode) as f:
            s = f.read()
        if encoding:
            s = s.decode(encoding)
    return s

get_contents = file_get_contents


def file_put_contents(filename, string):
    """Write string to filename."""

    with open(filename, 'w') as f:
        f.write(string)

put_contents = file_put_contents


def mkdir(dirs, recursive=False, mode=None):
    if isinstance(dirs, basestring):
        dirs = [dirs]
    args = () if mode is None else (mode, )
    for d in dirs:
        if recursive:
            os.makedirs(d, *args)
        else:
            os.mkdir(d, *args)


def touch(fname):
    """Create file if not existent

    Note that it doesn't change access time.

    """
    open(fname, 'a').close()


def tmpfile(content=None):
    fp, _tmpfile = tempfile.mkstemp()
    os.close(fp)
    if content is not None:
        file_put_contents(_tmpfile, content)
    return _tmpfile

## importing these KIDS methods from other modules
tmpdir = tempfile.mkdtemp
rmtree = shutil.rmtree


def unlink(filename, force=False):
    try:
        os.unlink(filename)
    except (OSError, FileNotFoundError) as e:
        # catch file does not exists
        if e.errno == 2:
            if not force:
                if PY3:
                    raise
                else:
                    raise FileNotFoundError(str(e))
        elif e.errno == 21:
            if PY3:
                raise
            else:
                raise IsADirectoryError(str(e))
        else:
            raise


def chown(path, user, group=None, recursive=False):
    """Retrieve uid of user then change ownership of the path
    """

    if group is None:
        group = user

    uid = pwd.getpwnam(user).pw_uid
    gid = grp.getgrnam(group).gr_gid

    if not recursive:
        os.chown(path, uid, gid)
    else:
        for root, _dirs, files in os.walk(path):
            os.chown(root, uid, gid)
            for cfile in files:
                os.chown(os.path.join(root, cfile), uid, gid)


def file_zip(filename, destination=''):
    """zip a file and put it in destination dir"""
    dest = destination if destination else (filename + '.gz')

    out = gzip.open(dest, 'wb')
    try:
        out.write(file_get_contents(filename, binary=True))
    finally:
        out.close()
