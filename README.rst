=========
kids.file
=========

.. image:: https://pypip.in/v/kids.file/badge.png
    :target: https://pypi.python.org/pypi/kids.file

.. image:: https://secure.travis-ci.org/0k/kids.file.png?branch=master
    :target: http://travis-ci.org/0k/kids.file


This very small module is part of KIDS (Keep It Dead Simple), and propose some
python coding shorcuts on very common tasks. Original tasks I've shortcuted
often requires to know 2 to 10 lines of python or special cases or different
modules location.

It is, for now, a very humble package.


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

    >>> filepath1 = kf.mk_tmp_file(content='foo')
    >>> filepath2 = kf.mk_tmp_file(content='bar')
    >>> kf.rm(filepath1, filepath2)

And of course still catches bad usage, and tries to be clear about it::

    >>> kf.rm(filepath1, foo=True)
    Traceback (most recent call last):
    ...
    SyntaxError: Unknown keyword argument 'foo'.


chown, mkdir, touch
-------------------

A ``chown`` function is provided, with an optional ``recursive`` keyword argument.

Let's now create a small tree directory (using ``mk_tmp_dir``, ``mkdir``,
``touch``)::

    >>> from os.path import join

    >>> tmp_dirpath = kf.mk_tmp_dir()
    >>> base = join(tmp_dirpath, 'base')

    >>> kf.mkdir(join(base, 'foo'), recursive=True)
    >>> kf.touch(join(base, 'plop'))


We will mock the legacy ``os.chown`` to see what happens under the hood::

    >>> import os
    >>> import minimock
    >>> m = minimock.mock('os.chown')

And call ``kids``'s ``chown`` on user 'root'::

    >>> kf.chown(base, 'root', recursive=True)  ## doctest: +ELLIPSIS
    Called os.chown('/.../base', 0, 0)
    Called os.chown('/.../base/plop', 0, 0)
    Called os.chown('/.../base/foo', 0, 0)

Let's clean up our mess::

    >>> minimock.restore()

    >>> kf.rm(tmp_dirpath, recursive=True)


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
