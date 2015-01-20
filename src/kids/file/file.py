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
else:  ## pragma: no cover
    class FileNotFoundError(OSError):
        pass

    class IsADirectoryError(OSError):
        pass


## XXXvlab: I don't like all these arguments...
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
    else:  ## pragma: no cover
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


## aliasing, because still not sure of the naming convention
mk_tmp_file = tmpfile

## importing these KIDS methods from other modules
mk_tmp_dir = tmpdir = tempfile.mkdtemp


def rm(*filenames, **options):
    force = options.pop("force", False)
    recursive = options.pop("recursive", False)
    if len(options):
        raise SyntaxError(
            "Unknown keyword argument %s." % (", ".join("%r" % k for k in options.keys())))
    if len(filenames) != 1 or isinstance(filenames[0], list):
        for filename in filenames:
            rm(filename, force=force, recursive=recursive)
        return
    filename = filenames[0]
    try:
        if recursive:
            shutil.rmtree(filename)
        else:
            os.unlink(filename)
    except (OSError, FileNotFoundError) as e:
        # catch file does not exists
        if e.errno == 2:
            if not force:
                if PY3:
                    raise
                else:  ## pragma: no cover
                    raise FileNotFoundError(str(e))
        elif e.errno == 21:
            if PY3:
                raise
            else:  ## pragma: no cover
                raise IsADirectoryError(str(e))
        else:
            raise

## aliasing, because still not sure of the naming convention
unlink = rm


def chown(path, user=None, group=None, uid=None, gid=None, recursive=False):
    """Retrieve uid of user then change ownership of the path"""

    if all(e is None for e in (user, uid, group, gid)):
        raise SyntaxError("No user nor group provided.")

    if user is not None and uid is not None:
        raise SyntaxError("uid and user keyword arguments are exclusive.")

    if group is not None and gid is not None:
        raise SyntaxError("gid and group keyword arguments are exclusive.")

    if uid is None:
        if user is not None:
            uid = pwd.getpwnam(user).pw_uid
        else:
            uid = -1

    if gid is None:
        if group is not None:
            gid = grp.getgrnam(group).gr_gid
        else:
            gid = -1

    if not recursive:
        os.chown(path, uid, gid)
    else:
        for filepath in sorted(os.listdir(path)):
            fullname = os.path.join(path, filepath)
            os.chown(fullname, uid, gid)
            if os.path.isdir(fullname):
                chown(fullname, uid=uid, gid=gid, recursive=recursive)


def file_zip(filename, destination=''):
    """zip a file and put it in destination dir"""
    dest = destination if destination else (filename + '.gz')

    out = gzip.open(dest, 'wb')
    try:
        out.write(file_get_contents(filename, binary=True))
    finally:
        out.close()
    return dest

## aliasing, because still not sure of the naming convention
zip = file_zip  ## pylint: disable=W0622


def basename(filename, suffix=None):
    bname = os.path.basename(filename)
    if suffix and bname.endswith(suffix):
        bname = bname[0:-len(suffix)]
    return bname
