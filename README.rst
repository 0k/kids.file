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


tmpfile, file_get_contents, file_put_contents
---------------------------------------------

Let's create a new temporary file containing the string 'bonjour'::

    >>> from kids.file import tmpfile, file_get_contents, file_put_contents
    >>> f = tmpfile(content='bonjour')

``f`` holds the file path of the temporary file. Let's check what is the file
content with ``file_get_contents``::

    >>> file_get_contents(f)
    'bonjour'

Let's now put some new content in this file, thanks to ``file_put_contents``::

    >>> file_put_contents(f, 'hello\nfriend')
    >>> file_get_contents(f)
    'hello\nfriend'

This is it.


unlink
------

This version of unlink has a special argument that suppress exception on
unexistent file::

    >>> from kids.file import unlink
    >>> unlink(f)
    >>> unlink(f)  ## doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    FileNotFoundError: [Errno 2] No such file or directory: '...'

This will not cast an exception::

    >>> unlink(f, force=True)

While it will continue to cast an exception whenever it is NOT a ``file not
found`` error::

    >>> unlink('/', force=True)
    Traceback (most recent call last):
    ...
    IsADirectoryError: [Errno 21] Is a directory: '/'


chown, mkdir, touch
-------------------

Let's now create a small tree directory (using ``tmpdir``, ``mkdir``,
``touch``)::

    >>> from kids.file import tmpdir, mkdir, touch
    >>> from os.path import join

    >>> d = tmpdir()
    >>> base = join(d, 'base')

    >>> mkdir(join(base, 'foo'), recursive=True)
    >>> touch(join(base, 'plop'))

We test ``chown`` for root as it will be with uid and gid 0 for sure. There
should be 3 chown issued.

We will mock the legacy 'os.chown' to monitor when it is called::

    >>> import os
    >>> import minimock
    >>> m = minimock.mock('os.chown')

And call our chown on user 'root'::

    >>> from kids.file import chown
    >>> chown(base, 'root', recursive=True)  ## doctest: +ELLIPSIS
    Called os.chown('/.../base', 0, 0)
    Called os.chown('/.../base/plop', 0, 0)
    Called os.chown('/.../base/foo', 0, 0)

Let's clean up our mess::

    >>> minimock.restore()

    >>> from kids.file import rmtree
    >>> rmtree(d)


Additional Shortcuts
====================

I'm not sure to keep these shortcuts. I'll see if these are really used often.


Compressed file
---------------

You should now read this easily::

    >>> f = tmpfile(content="foo")

Let's zip this file::

    >>> from kids.file import file_zip
    >>> file_zip(f)

This created a new file along the previvous file. Let's check its contents::

    >>> file_get_contents(f + '.gz', uncompress="zlib")
    'foo'

And now, we can clean up our mess::

    >>> unlink(f)
    >>> unlink(f + ".gz")


Tests
=====

Well, this package is really small, and you've just read the tests.

To execute them, install ``nosetest``, and run::

    nosetests
