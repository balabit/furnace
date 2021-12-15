Furnace
=======

A lightweight pure-python container implementation.

.. |build_status| image:: https://github.com/balabit/furnace/workflows/build/badge.svg
.. |python_support| image:: python-support.svg

|build_status| |python_support|

It is a wrapper around the Linux namespace functionality through libc
functions like ``unshare()``, ``nsenter()`` and ``mount()``. You can
think of it as a sturdier chroot replacement, where cleanup is easy (no
lingering processes or leaked mountpoints). It needs superuser
privileges to run.

Usage
-----

Installation
~~~~~~~~~~~~

You can either install it with pip:

::

    pip3 install furnace

Or if you want, the following commands will install the bleeding-edge
version of furnace to your system.

::

    git clone https://github.com/balabit/furnace.git
    cd furnace
    python3 setup.py install

This will of course install it into a virtualenv, if you activate it
beforehand.

Dependencies
~~~~~~~~~~~~

The only dependencies are:

- Python3.6+
- Linux kernel 2.6.24+
- A libc that implements setns() and nsenter() (that’s basically any
  libc released after 2007)

Example
~~~~~~~

After installing, the main interface to use is the ``ContainerContext``
class. It is, as the name suggests, a context manager, and after
entering, its ``run()`` and ``Popen()`` methods can be used exactly like
``subprocess``\ ’s similarly named methods:

.. code:: python

    from furnace.context import ContainerContext

    with ContainerContext('/opt/ChrootMcChrootface') as container:
        container.run(['ps', 'aux'])

The above example will run ``ps`` in the new namespace. It should show
two processes, furnace’s PID1, and the ``ps`` process itself. After
leaving the context, furnace will kill all processes started inside, and
destroy the namespaces created, including any mountpoints that were
mounted inside (e.g. with ``container.run(['mount', '...'])``).

Of course, all other arguments of ``run()`` and ``Popen()`` are
supported:

.. code:: python

    import sys
    import subprocess
    from furnace.context import ContainerContext

    with ContainerContext('/opt/ChrootMcChrootface') as container:
        ls_result = container.run(['ls', '/bin'], env={'LISTFLAGS': '-la'}, stdout=subprocess.PIPE, check=True)
        print('Files:')
        print(ls_result.stdout.decode('utf-8'))

        file_outside_container = open('the_magic_of_file_descriptors.gz', 'wb')
        process_1 = container.Popen(['cat', '/etc/passwd'], stdout=subprocess.PIPE)
        process_2 = container.Popen(['gzip'], stdin=process_1.stdout, stdout=file_outside_container)
        process_2.communicate()
        process_1.wait()

As you can see, the processes started can inherit file descriptors from
each other, or outside the container, and can also be managed from the
python code outside the container, if you wish.

As a convenience feature, the context has an ``interactive_shell()``
method that takes you into bash shell inside the container. This is
mostly useful for debugging:

.. code:: python

    import traceback
    from furnace.context import ContainerContext

    with ContainerContext('/opt/ChrootMcChrootface') as container:
        try:
            container.run(['systemctl', '--enable', 'nginx.service'])
        except Exception as e:
            print("OOOPS, an exception occured:")
            traceback.print_exc(file=sys.stdout)
            print("Entering debug shell")
            container.interactive_shell()
            raise

Development
-----------

Contributing
~~~~~~~~~~~~

We appreciate any feedback, so if you have problems, or even
suggestions, don’t hesitate to open an issue. Of course, Pull Requests
are extra-welcome, as long as tests pass, and the code is not much worse
than all other existing code :)

Setting up a development environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To set up a virtualenv with all the necessary tools for development,
install the GNU make tool and the python3-venv package (it is supposed to be
part of the standard python3 library, but on Ubuntu systems is an invidual
package).
Then simply run:

::

    make dev

This will create a virtualenv in a directory named .venv. This
virtualenv is used it for all other make targets, like ``check``

Running tests
~~~~~~~~~~~~~

During and after development, you usually want to run both coding style
checks, and integration tests. Make sure if the 'loop' kernel module has been
loaded before you run the integration tests.

::

    make lint
    make check

Please make sure at least these pass before submitting a PR.

License
-------

This project is licensed under the GNU LGPLv2.1 License - see the
`LICENSE.txt`_ for details

.. _LICENSE.txt: LICENSE.txt
