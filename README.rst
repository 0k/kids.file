=========================
kids.file
=========================

.. image:: http://img.shields.io/pypi/v/kids.file.svg?style=flat
   :target: https://pypi.python.org/pypi/kids.file/
   :alt: Latest PyPI version

.. image:: http://img.shields.io/pypi/dm/kids.file.svg?style=flat
   :target: https://pypi.python.org/pypi/kids.file/
   :alt: Number of PyPI downloads

.. image:: http://img.shields.io/travis/0k/kids.file/master.svg?style=flat
   :target: https://travis-ci.org/0k/kids.file/
   :alt: Travis CI build status

.. image:: http://img.shields.io/coveralls/0k/kids.file/master.svg?style=flat
   :target: https://coveralls.io/r/0k/kids.file
   :alt: Test coverage


This very small module is part of KIDS (Keep It Dead Simple), and proposes some
python coding shortcuts on very common tasks. Original tasks I've shortcuted
often requires to know 2 to 10 lines of python or special cases or different
modules location.

It is, for now, a very humble package.


Maturity
========

This code is in alpha stage. It wasn't tested on Windows. API may change.
This is more a draft for an ongoing reflection.


Documentation
=============


tmp, get_contents, put_contents
-------------------------------

Let's create a new temporary file containing the string 'bonjour'::

    >>> import kids.file as kf
    >>> filepath = kf.mk_tmp_file(content='bonjour')

``filepath`` holds the file path of the temporary file. Let's check what is the file
content with ``get_contents``::

    >>> kf.get_contents(filepath)
    'bonjour'

Let's now put some new content in this file, thanks to ``put_contents``::

    >>> kf.put_contents(filepath, 'hello\nfriend')
    >>> kf.get_contents(filepath)
    'hello\nfriend'

This is it.


remove files
------------

To remove files, you can use ``rm`` (or ``rm`` which is an alias).

This version works as python ``rm`` with some added usefull behaviors:::

    >>> kf.rm(filepath)

The file was removed. But notice if we try it again::

    >>> kf.rm(filepath)  ## doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    FileNotFoundError: [Errno 2] No such file or directory: '...'

To mimick the behavior of ``rm`` and the usage of its ``-f``, you have also
a ``force`` keyword argument, that will not cast an exception on non-existent
file::

    >>> kf.rm(filepath, force=True)

While it will continue to cast an exception whenever it is NOT a ``file not
found`` error::

    >>> kf.rm('/', force=True)
    Traceback (most recent call last):
    ...
    IsADirectoryError: [Errno 21] Is a directory: '/'

And of course, there's a ``recursive`` argument which remove directories with all
files and subdirectories (as would shell ``rm`` on a Unix like system shell)::

    >>> tmp_dirpath = kf.mk_tmp_dir()
    >>> kf.rm(tmp_dirpath, recursive=True)
    >>> kf.rm(tmp_dirpath, recursive=True)  ## doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    FileNotFoundError: [Errno 2] No such file or directory: '...'
    >>> kf.rm(tmp_dirpath, recursive=True, force=True)

It supports also multiple files::

    >>> filepath1 = kf.mk_tmp_file()
    >>> filepath2 = kf.mk_tmp_file()
    >>> kf.rm([filepath1, filepath2])

And of course still catches bad usage, and tries to be clear about it::

    >>> kf.rm(filepath1, foo=True)
    Traceback (most recent call last):
    ...
    TypeError: 'rm' got unexpecteds keywords argument foo


chown, mkdir, touch
-------------------

A ``chown`` function is provided, with an optional ``recursive`` keyword argument.

Let's now create a small tree directory (using ``mk_tmp_dir``, ``mkdir``,
``touch``)::

    >>> from os.path import join

    >>> tmp_dirpath = kf.mk_tmp_dir()
    >>> base = join(tmp_dirpath, 'base')

    >>> kf.mkdir(join(base, 'foo'), recursive=True)
    >>> kf.mkdir([join(base, 'foo', 'bar1'),
    ...           join(base, 'foo', 'bar2')])
    >>> kf.touch(join(base, 'plop'))
    >>> kf.touch([join(base, 'foo', 'bar1', 'README'), ])

Notice that both ``mkdir`` and ``touch`` support multiple files at once.


We will mock the legacy ``os.chown`` to see what happens under the hood::

    >>> import os
    >>> import minimock
    >>> m = minimock.mock('os.chown')

And call ``kids``'s ``chown`` on user 'root'::

    >>> kf.chown(base, user='root', recursive=True)  ## doctest: +ELLIPSIS
    Called os.chown('.../base/foo', 0, -1)
    Called os.chown('.../base/foo/bar1', 0, -1)
    Called os.chown('.../base/foo/bar1/README', 0, -1)
    Called os.chown('.../base/foo/bar2', 0, -1)
    Called os.chown('.../base/plop', 0, -1)

It support numerical ids if necessary::

    >>> kf.chown(base, gid=0)  ## doctest: +ELLIPSIS
    Called os.chown('.../base', -1, 0)

Is equivalent to::

    >>> kf.chown(base, group='root')  ## doctest: +ELLIPSIS
    Called os.chown('.../base', -1, 0)

You should of course avoid setting uid and user at the same time::

    >>> kf.chown(base, uid=0, user='root')  ## doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    SyntaxError: uid and user keyword arguments are exclusive.

Same for group and gid::

    >>> kf.chown(base, group='root', gid=0)  ## doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    SyntaxError: gid and group keyword arguments are exclusive.

And you must set at least a group or user (numerically or not)::

    >>> kf.chown(base)  ## doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    SyntaxError: No user nor group provided.

Let's clean up our mess::

    >>> minimock.restore()

    >>> kf.rm(tmp_dirpath, recursive=True)


Basename
--------

There's a full basename implementation::

     >>> kf.basename("/path/foo.bar", ".bar")
     'foo'
     >>> kf.basename("/path/foo.bar")
     'foo.bar'

Note that you can provide multiple suffixes::

     >>> kf.basename("/path/foo.bar", (".foo", ".bar"))
     'foo'

Only the first matching the end will be removed.


normpath
--------

Given a path, it'll return the absolute path::

    >>> kf.normpath('../tata' , cwd='/tmp/toto')
    '/tmp/tata'

if you don't give the ``cwd`` argument, it'll default to current
working directory.


File
----

File objects in python only offers to read line by line which are for
some reason, delimited by ``\n`` (or equivalent). This is quite
arbitrary, and so ``File`` is an adaptor on any file object to offer
the ability to read based on any delimiter.

To show how it work we'll use ``filify`` which takes a string and
returns a file object containing the string. (Yes, this is StringIO,
but with additional PY3 love).

    >>> from kids.file import File, filify

To use ``File``, you should use it as an adaptor, this means you give
him a file object, and it'll return his object that will make the
bridge between his new API and the old API::

    >>> f = File(filify("a-b-c-d"))

As read provides an iterator, here a convenient function to get the
contents::

    >>> def show(l):
    ...     print(", ".join(l))

So this is quite straightforward::

    >>> show(f.read(delimiter="-"))
    a, b, c, d

This should work with very large file or records and is very handy for instance
to parse file (like stdout) that use ``NUL`` separated fields.


Additional Shortcuts
====================

I'm not sure to keep these shortcuts. I'll see if these are really used often.


Compressed file
---------------

You should now read this easily::

    >>> filepath = kf.mk_tmp_file(content="foo")

Let's zip this file::

    >>> zip_filepath = kf.zip(filepath)

This created a new file along the previvous file. Let's check its contents::

    >>> kf.get_contents(zip_filepath, uncompress="zlib")
    'foo'

And now, we can clean up our mess::

    >>> kf.rm(filepath, zip_filepath)


Tests
=====

Well, this package is really small, and you've just read the tests.

To execute them, install ``nosetest``, and run::

    nosetests


Contributing
============

Any suggestion or issue is welcome. Push request are very welcome,
please check out the guidelines.


Push Request Guidelines
-----------------------

You can send any code. I'll look at it and will integrate it myself in
the code base and leave you as the author. This process can take time and
it'll take less time if you follow the following guidelines:

- check your code with PEP8 or pylint. Try to stick to 80 columns wide.
- separate your commits per smallest concern.
- each commit should pass the tests (to allow easy bisect)
- each functionality/bugfix commit should contain the code, tests,
  and doc.
- prior minor commit with typographic or code cosmetic changes are
  very welcome. These should be tagged in their commit summary with
  ``!minor``.
- the commit message should follow gitchangelog rules (check the git
  log to get examples)
- if the commit fixes an issue or finished the implementation of a
  feature, please mention it in the summary.

If you have some questions about guidelines which is not answered here,
please check the current ``git log``, you might find previous commit that
would show you how to deal with your issue.


License
=======

Copyright (c) 2015 Valentin Lab.

Licensed under the `BSD License`_.

.. _BSD License: http://raw.github.com/0k/kids.file/master/LICENSE
