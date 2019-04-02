# -*- coding: utf-8 -*-

import sys
import locale


PY3 = sys.version_info[0] >= 3

if PY3:
    imap = map
else:  ## pragma: no cover
    import itertools
    imap = itertools.imap


if PY3:
    from io import BytesIO

    def filify(s):
        _obj = BytesIO()
        _obj.write(s.encode(_preferred_encoding))
        _obj.seek(0)
        return _obj
else:  ## pragma: no cover
    from cStringIO import StringIO as filify


_preferred_encoding = locale.getpreferredencoding()


def itermap(fun):

    def _new(orig_iter_method):

        def new_iter_method(*arg, **kwargs):
            return imap(
                fun, orig_iter_method(*arg, **kwargs))
        return new_iter_method
    return _new


def generic_read(obj, delimiter, read_fun, offset=0):
    """Take any object that could be read by chunks,
    return an iterator of records separated by delimiter.

    file or sockets comes to mind

    """

    buf = ""
    if PY3:
        delimiter = delimiter.encode(_preferred_encoding)
        buf = buf.encode(_preferred_encoding)
    while True:
        chunk = read_fun(obj)
        if not chunk:
            offset += len(buf)
            yield offset, buf
            return
        records = chunk.split(delimiter)
        records[0] = buf + records[0]
        for record in records[:-1]:
            offset += len(record) + 1
            yield offset, record
        buf = records[-1]


class File(object):
    """File like API to read fields separated by any delimiters

    It'll take care of file decoding to unicode.

    This is an adaptor on a file object.

        >>> f = File(filify("a-b-c-d"))

    Read provides an iterator:

        >>> def show(l):
        ...     print(", ".join(l))
        >>> show(f.read(delimiter="-"))
        a, b, c, d

    You can change the buffersize loaded into memory before outputing
    your changes. It should not change the iterator output:

        >>> f = File(filify("é-à-ü-d"), buffersize=3)
        >>> len(list(f.read(delimiter="-")))
        4

        >>> f = File(filify("foo-bang-yummy"), buffersize=3)
        >>> show(f.read(delimiter="-"))
        foo, bang, yummy

        >>> f = File(filify("foo-bang-yummy"), buffersize=1)
        >>> show(f.read(delimiter="-"))
        foo, bang, yummy

    """

    def __init__(self, file, buffersize=4096):
        self._file = file
        self._buffersize = buffersize
        try:
            self.offset = file.tell()
        except IOError:
            self.offset = 0

    @itermap(lambda r: r.decode(_preferred_encoding))
    def read(self, delimiter="\n"):
        reader = generic_read(
            self._file, delimiter,
            lambda f: f.read(self._buffersize), offset=self.offset)
        for new_offset, record in reader:
            self.offset = new_offset
            yield record

    @property
    def name(self):
        return self._file.name

    def write(self, buf):
        if PY3:
            buf = buf.encode(_preferred_encoding)
        return self._file.write(buf)

    def close(self):
        return self._file.close()

    def flush(self):
        self._file.flush()




