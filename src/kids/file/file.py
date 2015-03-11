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
import itertools
import inspect
import collections

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


##
## Part of upcoming kids.inspect
##


def get_arg_spec(f):
    args, varargs, keywords, defaults = inspect.getargspec(f)
    defaults = [] if defaults is None else defaults
    defaults = collections.OrderedDict(
        reversed(list(
            (k, v)
            for k, v in __builtins__["zip"](reversed(args), reversed(defaults)))))
    return args, varargs, keywords, defaults


def get_valued_prototype(f, a, kw):
    """Returns an ordered dict of the label/value received by given function


    Returns the mapping applied to the function::

       >>> get_valued_prototype(lambda a, b: None, [1, 2], {})
       OrderedDict([('a', 1), ('b', 2)])

    So this means 'a' will be valuated with 1, etc...

    default values
    --------------

    It works also if you have default values::

       >>> get_valued_prototype(lambda a, b, c=None: None, [1, 2], {})
       OrderedDict([('a', 1), ('b', 2), ('c', None)])

       >>> get_valued_prototype(lambda a, b, c=None: None, [1, 2, 3], {})
       OrderedDict([('a', 1), ('b', 2), ('c', 3)])

    keyword values
    --------------

       >>> get_valued_prototype(
       ...     lambda a, b=None, c=None: None,
       ...     [1, ], {'c': 3})
       OrderedDict([('a', 1), ('b', None), ('c', 3)])

    """
    args, _varargs, _keywords, defaults = get_arg_spec(f)
    a = list(a)
    if defaults:
        a.extend(defaults.values())
    res = collections.OrderedDict(
        (label, a[idx]) for idx, label in enumerate(args))
    if kw:
        for k, v in kw.items():
            res[k] = v
    return res


def call_with_valued_prototype(f, valued_prototype):
    """Call and return the result of the given function applied to prototype


    For instance, here, we will call the lambda with the given values::

        >>> call_with_valued_prototype(
        ...     lambda a, b: "a: %s, b: %s" % (a, b),
        ...     {'a': 1, 'b': 2})
        'a: 1, b: 2'

    If you fail valuating all the necessary values, it should bail out with
    an exception::

        >>> call_with_valued_prototype(
        ...     lambda a, b: "a: %s, b: %s" % (a, b),
        ...     {'a': 1, 'c': 2})
        Traceback (most recent call last):
        ...
        ValueError: Missing value for argument 'b'.

    If you provide wrong values, it should fail as if you called it yourself::

        >>> call_with_valued_prototype(
        ...     lambda a, b: "a: %s, b: %s" % (a, b),
        ...     {'a': 1, 'b': 2, 'foo': 'bar'})
        Traceback (most recent call last):
        ...
        TypeError: '<lambda>' got unexpecteds keywords argument foo

    """
    args, _varargs, _keywords, defaults = get_arg_spec(f)
    build_args = []
    valued_prototype = valued_prototype.copy()
    for arg in args:
        if arg in valued_prototype:
            value = valued_prototype.pop(arg)
        else:
            try:
                value = defaults[arg]
            except KeyError:
                raise ValueError("Missing value for argument %r." % arg)
        build_args.append(value)
    if len(valued_prototype):
        raise TypeError("%r got unexpecteds keywords argument %s"
                        % (f.__name__, ", ".join(valued_prototype.keys())))
    return f(*build_args)

## part of upcoming kids.decorator


def multi(margs):
    """Demultiply execution of a function along given argument.

    This offers support on specified argument of multiple values.

    For instance::

        >>> @multi('x')
        ... def foo(x):
        ...     print("I like %s." % x)

    Normal call is preserved::

        >>> foo('apples')
        I like apples.

    But now we can provide lists to the first argument, and this will
    call the underlying function for each subvalues::

        >>> foo(['carrot', 'steak', 'banana'])
        I like carrot.
        I like steak.
        I like banana.

    You can actualy given also multiple argument to ``mutli`` itself to
    specify several argument to support expantion::

        >>> @multi(['x', 'y'])
        ... def bar(x, y):
        ...     print("%s likes %s." % (x, y))

    Normal call is preserved::

        >>> bar('Jane', 'apples')
        Jane likes apples.

    But multiple calls are supported in both arguments::

        >>> bar(['Jane', 'Cheetah', 'Tarzan'], ['apples', 'banana'])
        Jane likes apples.
        Jane likes banana.
        Cheetah likes apples.
        Cheetah likes banana.
        Tarzan likes apples.
        Tarzan likes banana.

    Please also notice that multi will return None whatever the actual
    results of the inner function.

    """
    if not isinstance(margs, (tuple, list)):
        margs = [margs]

    def decorator(f):
        def _f(*a, **kw):
            prototype = get_valued_prototype(f, a, kw)
            all_mvalues = [prototype[marg] for marg in margs]
            all_mvalues = [v if isinstance(v, (tuple, list)) else [v]
                           for v in all_mvalues]
            ret = []
            for mvalues in itertools.product(*all_mvalues):
                prototype.copy()
                prototype.update(dict(__builtins__["zip"](margs, mvalues)))
                ret.append(call_with_valued_prototype(f, prototype))
        return _f
    return decorator


##
## Actual code
##


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


@multi('dir')
def mkdir(dir, recursive=False, mode=None):
    args = () if mode is None else (mode, )
    if recursive:
        os.makedirs(dir, *args)
    else:
        os.mkdir(dir, *args)


## From stackoverflow:
## http://stackoverflow.com/questions/1158076/implement-touch-using-python
@multi('fname')
def touch(fname):
    """Create file if not existent"""
    with open(fname, 'a'):
        os.utime(fname, None)


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


@multi('filename')
def rm(filename, force=False, recursive=False):
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


@multi('path')
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
    """Return the filename without dirpath and given possible suffix(es)

    Very similar to command line in UNIX world::

        >>> filename = '/a/b/toto.py'
        >>> print(basename(filename, '.py'))
        toto

    Support multiple suffixes, first suffix that matches the end of
    the string wins::

        >>> filename = '/a/b/toto.pyc'
        >>> print(basename(filename, ('.py', '.pyc')))
        toto

    """
    bname = os.path.basename(filename)
    if suffix:
        if not isinstance(suffix, (list, tuple)):
            suffix = [suffix]
        for s in suffix:
            if bname.endswith(s):
                return bname[0:-len(s)]
    return bname


def normpath(path, cwd=None):
    """path can be absolute or relative, if relative it uses the cwd given as
    param.

    """
    if os.path.isabs(path):
        return path
    cwd = cwd if cwd else os.getcwd()
    return os.path.normpath(os.path.join(cwd, path))


