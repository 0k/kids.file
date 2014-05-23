# -*- coding: utf-8 -*-
"""
>>> False
False

"""

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


class Codec(object):

    def encode(self, value):
        raise NotImplementedError

    def decode(self, value):
        raise NotImplementedError

    def __union__(self, value):
        if not isinstance(value, Codec):
            raise TypeError('Can not pipe with non-codec value: %r' % value)
        return PipeCodec(a, b)


## To develop when I'll have time:

## codecs should be composable:

##
## file_contents_unicode = (fs("myfile") | codec.auto).contents
## url_contents_binary = url("myurl").read(10)   ## 10 first bytes of url
## zip_contents

## construct readers:
##     file_get_contents = (fs | codec.preferredstringencoding)
## or:
##     file_get_contents = (fs |
##
## A codec is not a compressor or decompressor: it's a chain
##   the chain can or can't be reversable. It'll be reversable
##   only if element of the chain give bothways.
##
## file_put_content = reverse(file_get_contents)
##
## You put a value at one end: the "filename" for example, and it
## get transformer to its binary content, then get decoded to python string.
##
## In the other way: you put a value at one end: the content string, and it
## gets encoded to binary, then pushed into a given file.
##
## if you give the name, you can really built a full bothway passage of codecs
## and you could add gzip, and YAML to python dict decoder.
##
## Stream interface (open/read) can be concerved on stream codecs.
## Discrete interface (get_content) may be much broader and can transform any python type.
##

class PipeCodec(Codec):

    def __init__(self, codec1, codec2):
        for codec in (codec1, codec2):
            if not isinstance(codec, Codec):
                raise TypeError("Can't pipe with non-codec value: %r"
                                % codec)
        self.codec1 = codec1
        self.codec2 = codec2

    def encode(self, value):
        return self.codec2.encode(self.codec1.encode(value))

    def decode(self, value):
        return self.codec1.decode(self.codec2.decode(value))


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


def basename(filename, suffix=None):
    bname = os.path.basename(filename)
    if suffix and bname.endswith(suffix):
        bname = bname[0:-len(suffix)]
    return bname
