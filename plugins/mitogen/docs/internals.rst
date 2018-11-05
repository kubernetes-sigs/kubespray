
Internal API Reference
**********************

.. toctree::
    :hidden:

    signals


Constants
=========

.. currentmodule:: mitogen.core
.. autodata:: CHUNK_SIZE


Latch Class
===========

.. currentmodule:: mitogen.core
.. autoclass:: Latch
   :members:


PidfulStreamHandler Class
=========================

.. currentmodule:: mitogen.core
.. autoclass:: PidfulStreamHandler
   :members:


Side Class
----------

.. currentmodule:: mitogen.core

.. class:: Side (stream, fd, keep_alive=True)

    Represent a single side of a :py:class:`BasicStream`. This exists to allow
    streams implemented using unidirectional (e.g. UNIX pipe) and bidirectional
    (e.g. UNIX socket) file descriptors to operate identically.

    :param mitogen.core.Stream stream:
        The stream this side is associated with.

    :param int fd:
        Underlying file descriptor.

    :param bool keep_alive:
        Value for :py:attr:`keep_alive`

    During construction, the file descriptor has its :py:data:`os.O_NONBLOCK`
    flag enabled using :py:func:`fcntl.fcntl`.

    .. attribute:: stream

        The :py:class:`Stream` for which this is a read or write side.

    .. attribute:: fd

        Integer file descriptor to perform IO on, or :data:`None` if
        :py:meth:`close` has been called.

    .. attribute:: keep_alive

        If :data:`True`, causes presence of this side in :py:class:`Broker`'s
        active reader set to defer shutdown until the side is disconnected.

    .. method:: fileno

        Return :py:attr:`fd` if it is not :data:`None`, otherwise raise
        :py:class:`StreamError`. This method is implemented so that
        :py:class:`Side` can be used directly by :py:func:`select.select`.

    .. method:: close

        Call :py:func:`os.close` on :py:attr:`fd` if it is not :data:`None`,
        then set it to :data:`None`.

    .. method:: read (n=CHUNK_SIZE)

        Read up to `n` bytes from the file descriptor, wrapping the underlying
        :py:func:`os.read` call with :py:func:`io_op` to trap common
        disconnection conditions.

        :py:meth:`read` always behaves as if it is reading from a regular UNIX
        file; socket, pipe, and TTY disconnection errors are masked and result
        in a 0-sized read just like a regular file.

        :returns:
            Bytes read, or the empty to string to indicate disconnection was
            detected.

    .. method:: write (s)

        Write as much of the bytes from `s` as possible to the file descriptor,
        wrapping the underlying :py:func:`os.write` call with :py:func:`io_op`
        to trap common disconnection connditions.

        :returns:
            Number of bytes written, or :data:`None` if disconnection was
            detected.


Stream Classes
--------------

.. currentmodule:: mitogen.core

.. class:: BasicStream

    .. attribute:: receive_side

        A :py:class:`Side` representing the stream's receive file descriptor.

    .. attribute:: transmit_side

        A :py:class:`Side` representing the stream's transmit file descriptor.

    .. method:: on_disconnect (broker)

        Called by :py:class:`Broker` to force disconnect the stream. The base
        implementation simply closes :py:attr:`receive_side` and
        :py:attr:`transmit_side` and unregisters the stream from the broker.

    .. method:: on_receive (broker)

        Called by :py:class:`Broker` when the stream's :py:attr:`receive_side` has
        been marked readable using :py:meth:`Broker.start_receive` and the
        broker has detected the associated file descriptor is ready for
        reading.

        Subclasses must implement this method if
        :py:meth:`Broker.start_receive` is ever called on them, and the method
        must call :py:meth:`on_disconect` if reading produces an empty string.

    .. method:: on_transmit (broker)

        Called by :py:class:`Broker` when the stream's :py:attr:`transmit_side`
        has been marked writeable using :py:meth:`Broker._start_transmit` and
        the broker has detected the associated file descriptor is ready for
        writing.

        Subclasses must implement this method if
        :py:meth:`Broker._start_transmit` is ever called on them.

    .. method:: on_shutdown (broker)

        Called by :py:meth:`Broker.shutdown` to allow the stream time to
        gracefully shutdown. The base implementation simply called
        :py:meth:`on_disconnect`.

.. autoclass:: Stream
   :members:

   .. method:: pending_bytes ()

        Returns the number of bytes queued for transmission on this stream.
        This can be used to limit the amount of data buffered in RAM by an
        otherwise unlimited consumer.

        For an accurate result, this method should be called from the Broker
        thread, using a wrapper like:

        ::

            def get_pending_bytes(self, stream):
                latch = mitogen.core.Latch()
                self.broker.defer(
                    lambda: latch.put(stream.pending_bytes())
                )
                return latch.get()


.. currentmodule:: mitogen.fork

.. autoclass:: Stream
   :members:

.. currentmodule:: mitogen.parent

.. autoclass:: Stream
   :members:

.. currentmodule:: mitogen.ssh

.. autoclass:: Stream
   :members:

.. currentmodule:: mitogen.sudo

.. autoclass:: Stream
   :members:


Other Stream Subclasses
-----------------------

.. currentmodule:: mitogen.core

.. autoclass:: IoLogger
   :members:

.. autoclass:: Waker
   :members:


Poller Class
------------

.. currentmodule:: mitogen.core
.. autoclass:: Poller

.. currentmodule:: mitogen.parent
.. autoclass:: KqueuePoller

.. currentmodule:: mitogen.parent
.. autoclass:: EpollPoller


Importer Class
--------------

.. currentmodule:: mitogen.core
.. autoclass:: Importer
   :members:


Responder Class
---------------

.. currentmodule:: mitogen.master
.. autoclass:: ModuleResponder
   :members:


Forwarder Class
---------------

.. currentmodule:: mitogen.parent
.. autoclass:: ModuleForwarder
   :members:


ExternalContext Class
---------------------

.. currentmodule:: mitogen.core

.. class:: ExternalContext

    External context implementation.

    .. attribute:: broker

        The :py:class:`mitogen.core.Broker` instance.

    .. attribute:: context

            The :py:class:`mitogen.core.Context` instance.

    .. attribute:: channel

            The :py:class:`mitogen.core.Channel` over which
            :py:data:`CALL_FUNCTION` requests are received.

    .. attribute:: stdout_log

        The :py:class:`mitogen.core.IoLogger` connected to ``stdout``.

    .. attribute:: importer

        The :py:class:`mitogen.core.Importer` instance.

    .. attribute:: stdout_log

        The :py:class:`IoLogger` connected to ``stdout``.

    .. attribute:: stderr_log

        The :py:class:`IoLogger` connected to ``stderr``.

    .. method:: _dispatch_calls

        Implementation for the main thread in every child context.

mitogen.master
==============

.. currentmodule:: mitogen.master

.. class:: ProcessMonitor

    Install a :py:data:`signal.SIGCHLD` handler that generates callbacks when a
    specific child process has exitted.

    .. method:: add (pid, callback)

        Add a callback function to be notified of the exit status of a process.

        :param int pid:
            Process ID to be notified of.

        :param callback:
            Function invoked as `callback(status)`, where `status` is the raw
            exit status of the child process.


Blocking I/O Functions
======================

These functions exist to support the blocking phase of setting up a new
context. They will eventually be replaced with asynchronous equivalents.


.. currentmodule:: mitogen.parent
.. autofunction:: discard_until
.. autofunction:: iter_read
.. autofunction:: write_all


Subprocess Creation Functions
=============================

.. currentmodule:: mitogen.parent
.. autofunction:: create_child
.. autofunction:: hybrid_tty_create_child
.. autofunction:: tty_create_child


Helper Functions
================

.. currentmodule:: mitogen.core
.. autofunction:: to_text
.. autofunction:: has_parent_authority
.. autofunction:: set_cloexec
.. autofunction:: set_nonblock
.. autofunction:: set_block
.. autofunction:: io_op

.. currentmodule:: mitogen.parent
.. autofunction:: close_nonstandard_fds
.. autofunction:: create_socketpair

.. currentmodule:: mitogen.master
.. autofunction:: get_child_modules

.. currentmodule:: mitogen.minify
.. autofunction:: minimize_source


Signals
=======

:ref:`Please refer to Signals <signals>`.
