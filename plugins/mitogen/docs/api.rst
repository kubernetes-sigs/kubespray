
API Reference
*************

.. toctree::
    :hidden:

    signals


Package Layout
==============


mitogen Package
---------------

.. automodule:: mitogen

.. autodata:: mitogen.__version__
.. autodata:: mitogen.is_master
.. autodata:: mitogen.context_id
.. autodata:: mitogen.parent_id
.. autodata:: mitogen.parent_ids
.. autofunction:: mitogen.main


mitogen.core
------------

.. automodule:: mitogen.core

.. currentmodule:: mitogen.core
.. decorator:: takes_econtext

    Decorator that marks a function or class method to automatically receive a
    kwarg named `econtext`, referencing the
    :class:`mitogen.core.ExternalContext` active in the context in which the
    function is being invoked in. The decorator is only meaningful when the
    function is invoked via :data:`CALL_FUNCTION
    <mitogen.core.CALL_FUNCTION>`.

    When the function is invoked directly, `econtext` must still be passed to
    it explicitly.

.. currentmodule:: mitogen.core
.. decorator:: takes_router

    Decorator that marks a function or class method to automatically receive a
    kwarg named `router`, referencing the :class:`mitogen.core.Router`
    active in the context in which the function is being invoked in. The
    decorator is only meaningful when the function is invoked via
    :data:`CALL_FUNCTION <mitogen.core.CALL_FUNCTION>`.

    When the function is invoked directly, `router` must still be passed to it
    explicitly.


mitogen.master
--------------

.. automodule:: mitogen.master


mitogen.parent
--------------

.. automodule:: mitogen.parent


mitogen.fakessh
---------------

.. image:: images/fakessh.png
    :align: right

.. automodule:: mitogen.fakessh
.. currentmodule:: mitogen.fakessh
.. autofunction:: run (dest, router, args, daedline=None, econtext=None)



Message Class
=============

.. currentmodule:: mitogen.core

.. class:: Message

    Messages are the fundamental unit of communication, comprising fields from
    the :ref:`stream-protocol` header, an optional reference to the receiving
    :class:`mitogen.core.Router` for ingress messages, and helper methods for
    deserialization and generating replies.

    .. attribute:: router

        The :class:`mitogen.core.Router` responsible for routing the
        message. This is :data:`None` for locally originated messages.

    .. attribute:: receiver

        The :class:`mitogen.core.Receiver` over which the message was last
        received. Part of the :class:`mitogen.select.Select` interface.
        Defaults to :data:`None`.

    .. attribute:: dst_id

        Integer target context ID. :class:`mitogen.core.Router` delivers
        messages locally when their :attr:`dst_id` matches
        :data:`mitogen.context_id`, otherwise they are routed up or downstream.

    .. attribute:: src_id

        Integer source context ID. Used as the target of replies if any are
        generated.

    .. attribute:: auth_id

        The context ID under whose authority the message is acting. See
        :ref:`source-verification`.

    .. attribute:: handle

        Integer target handle in the destination context. This is one of the
        :ref:`standard-handles`, or a dynamically generated handle used to
        receive a one-time reply, such as the return value of a function call.

    .. attribute:: reply_to

        Integer target handle to direct any reply to this message. Used to
        receive a one-time reply, such as the return value of a function call.
        :data:`IS_DEAD` has a special meaning when it appears in this field.

    .. attribute:: data

        Message data, which may be raw or pickled.

    .. attribute:: is_dead

        :data:`True` if :attr:`reply_to` is set to the magic value
        :data:`mitogen.core.IS_DEAD`, indicating the sender considers the
        channel dead.

    .. py:method:: __init__ (\**kwargs)

        Construct a message from from the supplied `kwargs`. :attr:`src_id`
        and :attr:`auth_id` are always set to :data:`mitogen.context_id`.

    .. py:classmethod:: pickled (obj, \**kwargs)

        Construct a pickled message, setting :attr:`data` to the
        serialization of `obj`, and setting remaining fields using `kwargs`.

        :returns:
            The new message.

    .. method:: unpickle (throw=True)

        Unpickle :attr:`data`, optionally raising any exceptions present.

        :param bool throw:
            If :data:`True`, raise exceptions, otherwise it is the caller's
            responsibility.

        :raises mitogen.core.CallError:
            The serialized data contained CallError exception.
        :raises mitogen.core.ChannelError:
            The `is_dead` field was set.

    .. method:: reply (obj, router=None, \**kwargs)

        Compose a reply to this message and send it using :attr:`router`, or
        `router` is :attr:`router` is :data:`None`.

        :param obj:
            Either a :class:`Message`, or an object to be serialized in order
            to construct a new message.
        :param router:
            Optional router to use if :attr:`router` is :data:`None`.
        :param kwargs:
            Optional keyword parameters overriding message fields in the reply.



Router Class
============

.. currentmodule:: mitogen.core

.. class:: Router

    Route messages between parent and child contexts, and invoke handlers
    defined on our parent context. :meth:`Router.route() <route>` straddles
    the :class:`Broker <mitogen.core.Broker>` and user threads, it is safe
    to call anywhere.

    **Note:** This is the somewhat limited core version of the Router class
    used by child contexts. The master subclass is documented below this one.

    .. attribute:: unidirectional

        When :data:`True`, permit children to only communicate with the current
        context or a parent of the current context. Routing between siblings or
        children of parents is prohibited, ensuring no communication is
        possible between intentionally partitioned networks, such as when a
        program simultaneously manipulates hosts spread across a corporate and
        a production network, or production networks that are otherwise
        air-gapped.

        Sending a prohibited message causes an error to be logged and a dead
        message to be sent in reply to the errant message, if that message has
        ``reply_to`` set.

        The value of :data:`unidirectional` becomes the default for the
        :meth:`local() <mitogen.master.Router.local>` `unidirectional`
        parameter.

    .. method:: stream_by_id (dst_id)

        Return the :class:`mitogen.core.Stream` that should be used to
        communicate with `dst_id`. If a specific route for `dst_id` is not
        known, a reference to the parent context's stream is returned.

    .. method:: add_route (target_id, via_id)

        Arrange for messages whose `dst_id` is `target_id` to be forwarded on
        the directly connected stream for `via_id`. This method is called
        automatically in response to ``ADD_ROUTE`` messages, but remains public
        for now while the design has not yet settled, and situations may arise
        where routing is not fully automatic.

    .. method:: register (context, stream)

        Register a new context and its associated stream, and add the stream's
        receive side to the I/O multiplexer. This This method remains public
        for now while hte design has not yet settled.

    .. method:: add_handler (fn, handle=None, persist=True, respondent=None, policy=None)

        Invoke `fn(msg)` for each Message sent to `handle` from this context.
        Unregister after one invocation if `persist` is :data:`False`. If
        `handle` is :data:`None`, a new handle is allocated and returned.

        :param int handle:
            If not :data:`None`, an explicit handle to register, usually one of
            the ``mitogen.core.*`` constants. If unspecified, a new unused
            handle will be allocated.

        :param bool persist:
            If :data:`False`, the handler will be unregistered after a single
            message has been received.

        :param mitogen.core.Context respondent:
            Context that messages to this handle are expected to be sent from.
            If specified, arranges for a dead message to be delivered to `fn`
            when disconnection of the context is detected.

            In future `respondent` will likely also be used to prevent other
            contexts from sending messages to the handle.

        :param function policy:
            Function invoked as `policy(msg, stream)` where `msg` is a
            :class:`mitogen.core.Message` about to be delivered, and
            `stream` is the :class:`mitogen.core.Stream` on which it was
            received. The function must return :data:`True`, otherwise an
            error is logged and delivery is refused.

            Two built-in policy functions exist:

            * :func:`mitogen.core.has_parent_authority`: requires the
              message arrived from a parent context, or a context acting with a
              parent context's authority (``auth_id``).

            * :func:`mitogen.parent.is_immediate_child`: requires the
              message arrived from an immediately connected child, for use in
              messaging patterns where either something becomes buggy or
              insecure by permitting indirect upstream communication.

            In case of refusal, and the message's ``reply_to`` field is
            nonzero, a :class:`mitogen.core.CallError` is delivered to the
            sender indicating refusal occurred.

        :return:
            `handle`, or if `handle` was :data:`None`, the newly allocated
            handle.

    .. method:: del_handler (handle)

        Remove the handle registered for `handle`

        :raises KeyError:
            The handle wasn't registered.

    .. method:: _async_route(msg, stream=None)

        Arrange for `msg` to be forwarded towards its destination. If its
        destination is the local context, then arrange for it to be dispatched
        using the local handlers.

        This is a lower overhead version of :meth:`route` that may only be
        called from the I/O multiplexer thread.

        :param mitogen.core.Stream stream:
            If not :data:`None`, a reference to the stream the message arrived
            on. Used for performing source route verification, to ensure
            sensitive messages such as ``CALL_FUNCTION`` arrive only from
            trusted contexts.

    .. method:: route(msg)

        Arrange for the :class:`Message` `msg` to be delivered to its
        destination using any relevant downstream context, or if none is found,
        by forwarding the message upstream towards the master context. If `msg`
        is destined for the local context, it is dispatched using the handles
        registered with :meth:`add_handler`.

        This may be called from any thread.


.. currentmodule:: mitogen.master

.. class:: Router (broker=None)

    Extend :class:`mitogen.core.Router` with functionality useful to
    masters, and child contexts who later become masters. Currently when this
    class is required, the target context's router is upgraded at runtime.

    .. note::

        You may construct as many routers as desired, and use the same broker
        for multiple routers, however usually only one broker and router need
        exist. Multiple routers may be useful when dealing with separate trust
        domains, for example, manipulating infrastructure belonging to separate
        customers or projects.

    :param mitogen.master.Broker broker:
        :class:`Broker` instance to use. If not specified, a private
        :class:`Broker` is created.

    .. attribute:: profiling

        When :data:`True`, cause the broker thread and any subsequent broker
        and main threads existing in any child to write
        ``/tmp/mitogen.stats.<pid>.<thread_name>.log`` containing a
        :mod:`cProfile` dump on graceful exit. Must be set prior to
        construction of any :class:`Broker`, e.g. via:

        .. code::

             mitogen.master.Router.profiling = True

    .. method:: enable_debug

        Cause this context and any descendant child contexts to write debug
        logs to /tmp/mitogen.<pid>.log.

    .. method:: allocate_id

        Arrange for a unique context ID to be allocated and associated with a
        route leading to the active context. In masters, the ID is generated
        directly, in children it is forwarded to the master via an
        ``ALLOCATE_ID`` message that causes the master to emit matching
        ``ADD_ROUTE`` messages prior to replying.

    .. method:: context_by_id (context_id, via_id=None)

        Messy factory/lookup function to find a context by its ID, or construct
        it. In future this will be replaced by a much more sensible interface.

    .. _context-factories:

    **Context Factories**

    .. method:: fork (on_fork=None, on_start=None, debug=False, profiling=False, via=None)

        Construct a context on the local machine by forking the current
        process. The forked child receives a new identity, sets up a new broker
        and router, and responds to function calls identically to children
        created using other methods.

        For long-lived processes, :meth:`local` is always better as it
        guarantees a pristine interpreter state that inherited little from the
        parent. Forking should only be used in performance-sensitive scenarios
        where short-lived children must be spawned to isolate potentially buggy
        code, and only after accounting for all the bad things possible as a
        result of, at a minimum:

        * Files open in the parent remaining open in the child,
          causing the lifetime of the underlying object to be extended
          indefinitely.

          * From the perspective of external components, this is observable
            in the form of pipes and sockets that are never closed, which may
            break anything relying on closure to signal protocol termination.

          * Descriptors that reference temporary files will not have their disk
            space reclaimed until the child exits.

        * Third party package state, such as urllib3's HTTP connection pool,
          attempting to write to file descriptors shared with the parent,
          causing random failures in both parent and child.

        * UNIX signal handlers installed in the parent process remaining active
          in the child, despite associated resources, such as service threads,
          child processes, resource usage counters or process timers becoming
          absent or reset in the child.

        * Library code that makes assumptions about the process ID remaining
          unchanged, for example to implement inter-process locking, or to
          generate file names.

        * Anonymous ``MAP_PRIVATE`` memory mappings whose storage requirement
          doubles as either parent or child dirties their pages.

        * File-backed memory mappings that cannot have their space freed on
          disk due to the mapping living on in the child.

        * Difficult to diagnose memory usage and latency spikes due to object
          graphs becoming unreferenced in either parent or child, causing
          immediate copy-on-write to large portions of the process heap.

        * Locks held in the parent causing random deadlocks in the child, such
          as when another thread emits a log entry via the :mod:`logging`
          package concurrent to another thread calling :meth:`fork`.

        * Objects existing in Thread-Local Storage of every non-:meth:`fork`
          thread becoming permanently inaccessible, and never having their
          object destructors called, including TLS usage by native extension
          code, triggering many new variants of all the issues above.

        * Pseudo-Random Number Generator state that is easily observable by
          network peers to be duplicate, violating requirements of
          cryptographic protocols through one-time state reuse. In the worst
          case, children continually reuse the same state due to repeatedly
          forking from a static parent.

        :meth:`fork` cleans up Mitogen-internal objects, in addition to
        locks held by the :mod:`logging` package, reseeds
        :func:`random.random`, and the OpenSSL PRNG via
        :func:`ssl.RAND_add`, but only if the :mod:`ssl` module is
        already loaded. You must arrange for your program's state, including
        any third party packages in use, to be cleaned up by specifying an
        `on_fork` function.

        The associated stream implementation is
        :class:`mitogen.fork.Stream`.

        :param function on_fork:
            Function invoked as `on_fork()` from within the child process. This
            permits supplying a program-specific cleanup function to break
            locks and close file descriptors belonging to the parent from
            within the child.

        :param function on_start:
            Invoked as `on_start(econtext)` from within the child process after
            it has been set up, but before the function dispatch loop starts.
            This permits supplying a custom child main function that inherits
            rich data structures that cannot normally be passed via a
            serialization.

        :param mitogen.core.Context via:
            Same as the `via` parameter for :meth:`local`.

        :param bool debug:
            Same as the `debug` parameter for :meth:`local`.

        :param bool profiling:
            Same as the `profiling` parameter for :meth:`local`.

    .. method:: local (remote_name=None, python_path=None, debug=False, connect_timeout=None, profiling=False, via=None)

        Construct a context on the local machine as a subprocess of the current
        process. The associated stream implementation is
        :class:`mitogen.master.Stream`.

        :param str remote_name:
            The ``argv[0]`` suffix for the new process. If `remote_name` is
            ``test``, the new process ``argv[0]`` will be ``mitogen:test``.

            If unspecified, defaults to ``<username>@<hostname>:<pid>``.

            This variable cannot contain slash characters, as the resulting
            ``argv[0]`` must be presented in such a way as to allow Python to
            determine its installation prefix. This is required to support
            virtualenv.

        :param str|list python_path:
            String or list path to the Python interpreter to use for bootstrap.
            Defaults to :data:`sys.executable` for local connections, and
            ``python`` for remote connections.

            It is possible to pass a list to invoke Python wrapped using
            another tool, such as ``["/usr/bin/env", "python"]``.

        :param bool debug:
            If :data:`True`, arrange for debug logging (:meth:`enable_debug`) to
            be enabled in the new context. Automatically :data:`True` when
            :meth:`enable_debug` has been called, but may be used
            selectively otherwise.

        :param bool unidirectional:
            If :data:`True`, arrange for the child's router to be constructed
            with :attr:`unidirectional routing
            <mitogen.core.Router.unidirectional>` enabled. Automatically
            :data:`True` when it was enabled for this router, but may still be
            explicitly set to :data:`False`.

        :param float connect_timeout:
            Fractional seconds to wait for the subprocess to indicate it is
            healthy. Defaults to 30 seconds.

        :param bool profiling:
            If :data:`True`, arrange for profiling (:data:`profiling`) to be
            enabled in the new context. Automatically :data:`True` when
            :data:`profiling` is :data:`True`, but may be used selectively
            otherwise.

        :param mitogen.core.Context via:
            If not :data:`None`, arrange for construction to occur via RPCs
            made to the context `via`, and for :data:`ADD_ROUTE
            <mitogen.core.ADD_ROUTE>` messages to be generated as appropriate.

            .. code-block:: python

                # SSH to the remote machine.
                remote_machine = router.ssh(hostname='mybox.com')

                # Use the SSH connection to create a sudo connection.
                remote_root = router.sudo(username='root', via=remote_machine)

    .. method:: doas (username=None, password=None, doas_path=None, password_prompt=None, incorrect_prompts=None, \**kwargs)

        Construct a context on the local machine over a ``doas`` invocation.
        The ``doas`` process is started in a newly allocated pseudo-terminal,
        and supports typing interactive passwords.

        Accepts all parameters accepted by :meth:`local`, in addition to:

        :param str username:
            Username to use, defaults to ``root``.
        :param str password:
            The account password to use if requested.
        :param str doas_path:
            Filename or complete path to the ``doas`` binary. ``PATH`` will be
            searched if given as a filename. Defaults to ``doas``.
        :param bytes password_prompt:
            A string that indicates ``doas`` is requesting a password. Defaults
            to ``Password:``.
        :param list incorrect_prompts:
            List of bytestrings indicating the password is incorrect. Defaults
            to `(b"doas: authentication failed")`.
        :raises mitogen.doas.PasswordError:
            A password was requested but none was provided, the supplied
            password was incorrect, or the target account did not exist.

    .. method:: docker (container=None, image=None, docker_path=None, \**kwargs)

        Construct a context on the local machine within an existing or
        temporary new Docker container using the ``docker`` program. One of
        `container` or `image` must be specified.

        Accepts all parameters accepted by :meth:`local`, in addition to:

        :param str container:
            Existing container to connect to. Defaults to :data:`None`.
        :param str username:
            Username within the container to :func:`setuid` to. Defaults to
            :data:`None`, which Docker interprets as ``root``.
        :param str image:
            Image tag to use to construct a temporary container. Defaults to
            :data:`None`.
        :param str docker_path:
            Filename or complete path to the Docker binary. ``PATH`` will be
            searched if given as a filename. Defaults to ``docker``.

    .. method:: jail (container, jexec_path=None, \**kwargs)

        Construct a context on the local machine within a FreeBSD jail using
        the ``jexec`` program.

        Accepts all parameters accepted by :meth:`local`, in addition to:

        :param str container:
            Existing container to connect to. Defaults to :data:`None`.
        :param str username:
            Username within the container to :func:`setuid` to. Defaults to
            :data:`None`, which ``jexec`` interprets as ``root``.
        :param str jexec_path:
            Filename or complete path to the ``jexec`` binary. ``PATH`` will be
            searched if given as a filename. Defaults to ``/usr/sbin/jexec``.

    .. method:: kubectl (pod, kubectl_path=None, kubectl_args=None, \**kwargs)

        Construct a context in a container via the Kubernetes ``kubectl``
        program.

        Accepts all parameters accepted by :meth:`local`, in addition to:

        :param str pod:
            Kubernetes pod to connect to.
        :param str kubectl_path:
            Filename or complete path to the ``kubectl`` binary. ``PATH`` will
            be searched if given as a filename. Defaults to ``kubectl``.
        :param list kubectl_args:
            Additional arguments to pass to the ``kubectl`` command.

    .. method:: lxc (container, lxc_attach_path=None, \**kwargs)

        Construct a context on the local machine within an LXC classic
        container using the ``lxc-attach`` program.

        Accepts all parameters accepted by :meth:`local`, in addition to:

        :param str container:
            Existing container to connect to. Defaults to :data:`None`.
        :param str lxc_attach_path:
            Filename or complete path to the ``lxc-attach`` binary. ``PATH``
            will be searched if given as a filename. Defaults to
            ``lxc-attach``.

    .. method:: lxc (container, lxc_attach_path=None, \**kwargs)

        Construct a context on the local machine within a LXD container using
        the ``lxc`` program.

        Accepts all parameters accepted by :meth:`local`, in addition to:

        :param str container:
            Existing container to connect to. Defaults to :data:`None`.
        :param str lxc_path:
            Filename or complete path to the ``lxc`` binary. ``PATH`` will be
            searched if given as a filename. Defaults to ``lxc``.

    .. method:: setns (container, kind, username=None, docker_path=None, lxc_info_path=None, machinectl_path=None, \**kwargs)

        Construct a context in the style of :meth:`local`, but change the
        active Linux process namespaces via calls to `setns(1)` before
        executing Python.

        The namespaces to use, and the active root file system are taken from
        the root PID of a running Docker, LXC, LXD, or systemd-nspawn
        container.

        A program is required only to find the root PID, after which management
        of the child Python interpreter is handled directly.

        :param str container:
            Container to connect to.
        :param str kind:
            One of ``docker``, ``lxc``, ``lxd`` or ``machinectl``.
        :param str username:
            Username within the container to :func:`setuid` to. Defaults to
            ``root``.
        :param str docker_path:
            Filename or complete path to the Docker binary. ``PATH`` will be
            searched if given as a filename. Defaults to ``docker``.
        :param str lxc_path:
            Filename or complete path to the LXD ``lxc`` binary. ``PATH`` will
            be searched if given as a filename. Defaults to ``lxc``.
        :param str lxc_info_path:
            Filename or complete path to the LXC ``lxc-info`` binary. ``PATH``
            will be searched if given as a filename. Defaults to ``lxc-info``.
        :param str machinectl_path:
            Filename or complete path to the ``machinectl`` binary. ``PATH``
            will be searched if given as a filename. Defaults to
            ``machinectl``.

    .. method:: su (username=None, password=None, su_path=None, password_prompt=None, incorrect_prompts=None, \**kwargs)

        Construct a context on the local machine over a ``su`` invocation. The
        ``su`` process is started in a newly allocated pseudo-terminal, and
        supports typing interactive passwords.

        Accepts all parameters accepted by :meth:`local`, in addition to:

        :param str username:
            Username to pass to ``su``, defaults to ``root``.
        :param str password:
            The account password to use if requested.
        :param str su_path:
            Filename or complete path to the ``su`` binary. ``PATH`` will be
            searched if given as a filename. Defaults to ``su``.
        :param bytes password_prompt:
            The string that indicates ``su`` is requesting a password. Defaults
            to ``Password:``.
        :param str incorrect_prompts:
            Strings that signal the password is incorrect. Defaults to `("su:
            sorry", "su: authentication failure")`.

        :raises mitogen.su.PasswordError:
            A password was requested but none was provided, the supplied
            password was incorrect, or (on BSD) the target account did not
            exist.

    .. method:: sudo (username=None, sudo_path=None, password=None, \**kwargs)

        Construct a context on the local machine over a ``sudo`` invocation.
        The ``sudo`` process is started in a newly allocated pseudo-terminal,
        and supports typing interactive passwords.

        Accepts all parameters accepted by :meth:`local`, in addition to:

        :param str username:
            Username to pass to sudo as the ``-u`` parameter, defaults to
            ``root``.
        :param str sudo_path:
            Filename or complete path to the sudo binary. ``PATH`` will be
            searched if given as a filename. Defaults to ``sudo``.
        :param str password:
            The password to use if/when sudo requests it. Depending on the sudo
            configuration, this is either the current account password or the
            target account password. :class:`mitogen.sudo.PasswordError`
            will be raised if sudo requests a password but none is provided.
        :param bool set_home:
            If :data:`True`, request ``sudo`` set the ``HOME`` environment
            variable to match the target UNIX account.
        :param bool preserve_env:
            If :data:`True`, request ``sudo`` to preserve the environment of
            the parent process.
        :param list sudo_args:
            Arguments in the style of :data:`sys.argv` that would normally
            be passed to ``sudo``. The arguments are parsed in-process to set
            equivalent parameters. Re-parsing ensures unsupported options cause
            :class:`mitogen.core.StreamError` to be raised, and that
            attributes of the stream match the actual behaviour of ``sudo``.

    .. method:: ssh (hostname, username=None, ssh_path=None, ssh_args=None, port=None, check_host_keys='enforce', password=None, identity_file=None, identities_only=True, compression=True, \**kwargs)

        Construct a remote context over an OpenSSH ``ssh`` invocation.

        The ``ssh`` process is started in a newly allocated pseudo-terminal to
        support typing interactive passwords and responding to prompts, if a
        password is specified, or `check_host_keys=accept`. In other scenarios,
        ``BatchMode`` is enabled and no PTY is allocated. For many-target
        configurations, both options should be avoided as most systems have a
        conservative limit on the number of pseudo-terminals that may exist.

        Accepts all parameters accepted by :meth:`local`, in addition to:

        :param str username:
            The SSH username; default is unspecified, which causes SSH to pick
            the username to use.
        :param str ssh_path:
            Absolute or relative path to ``ssh``. Defaults to ``ssh``.
        :param list ssh_args:
            Additional arguments to pass to the SSH command.
        :param int port:
            Port number to connect to; default is unspecified, which causes SSH
            to pick the port number.
        :param str check_host_keys:
            Specifies the SSH host key checking mode. Defaults to ``enforce``.

            * ``ignore``: no host key checking is performed. Connections never
              fail due to an unknown or changed host key.
            * ``accept``: known hosts keys are checked to ensure they match,
              new host keys are automatically accepted and verified in future
              connections.
            * ``enforce``: known host keys are checked to ensure they match,
              unknown hosts cause a connection failure.
        :param str password:
            Password to type if/when ``ssh`` requests it. If not specified and
            a password is requested, :class:`mitogen.ssh.PasswordError` is
            raised.
        :param str identity_file:
            Path to an SSH private key file to use for authentication. Default
            is unspecified, which causes SSH to pick the identity file.

            When this option is specified, only `identity_file` will be used by
            the SSH client to perform authenticaion; agent authentication is
            automatically disabled, as is reading the default private key from
            ``~/.ssh/id_rsa``, or ``~/.ssh/id_dsa``.
        :param bool identities_only:
            If :data:`True` and a password or explicit identity file is
            specified, instruct the SSH client to disable any authentication
            identities inherited from the surrounding environment, such as
            those loaded in any running ``ssh-agent``, or default key files
            present in ``~/.ssh``. This ensures authentication attempts only
            occur using the supplied password or SSH key.
        :param bool compression:
            If :data:`True`, enable ``ssh`` compression support. Compression
            has a minimal effect on the size of modules transmitted, as they
            are already compressed, however it has a large effect on every
            remaining message in the otherwise uncompressed stream protocol,
            such as function call arguments and return values.
        :param int ssh_debug_level:
            Optional integer `0..3` indicating the SSH client debug level.
        :raises mitogen.ssh.PasswordError:
            A password was requested but none was specified, or the specified
            password was incorrect.

        :raises mitogen.ssh.HostKeyError:
            When `check_host_keys` is set to either ``accept``, indicates a
            previously recorded key no longer matches the remote machine. When
            set to ``enforce``, as above, but additionally indicates no
            previously recorded key exists for the remote machine.


Context Class
=============

.. currentmodule:: mitogen.core

.. class:: Context

    Represent a remote context regardless of connection method.

    **Note:** This is the somewhat limited core version of the Context class
    used by child contexts. The master subclass is documented below this one.

    .. method:: send (msg)

        Arrange for `msg` to be delivered to this context.
        :attr:`dst_id <Message.dst_id>` is set to the target context ID.

        :param mitogen.core.Message msg:
            The message.

    .. method:: send_async (msg, persist=False)

        Arrange for `msg` to be delivered to this context, with replies
        directed to a newly constructed receiver. :attr:`dst_id
        <Message.dst_id>` is set to the target context ID, and :attr:`reply_to
        <Message.reply_to>` is set to the newly constructed receiver's handle.

        :param bool persist:
            If :data:`False`, the handler will be unregistered after a single
            message has been received.

        :param mitogen.core.Message msg:
            The message.

        :returns:
            :class:`mitogen.core.Receiver` configured to receive any replies
            sent to the message's `reply_to` handle.

    .. method:: send_await (msg, deadline=None)

        Like :meth:`send_async`, but expect a single reply (`persist=False`)
        delivered within `deadline` seconds.

        :param mitogen.core.Message msg:
            The message.
        :param float deadline:
            If not :data:`None`, seconds before timing out waiting for a reply.
        :returns:
            The deserialized reply.
        :raises mitogen.core.TimeoutError:
            No message was received and `deadline` passed.


.. currentmodule:: mitogen.parent

.. autoclass:: CallChain
    :members:

.. class:: Context

    Extend :class:`mitogen.core.Context` with functionality useful to masters,
    and child contexts who later become parents. Currently when this class is
    required, the target context's router is upgraded at runtime.

    .. attribute:: default_call_chain

        A :class:`CallChain` instance constructed by default, with pipelining
        disabled. :meth:`call`, :meth:`call_async` and :meth:`call_no_reply`
        use this instance.

    .. method:: shutdown (wait=False)

        Arrange for the context to receive a ``SHUTDOWN`` message, triggering
        graceful shutdown.

        Due to a lack of support for timers, no attempt is made yet to force
        terminate a hung context using this method. This will be fixed shortly.

        :param bool wait:
            If :data:`True`, block the calling thread until the context has
            completely terminated.
        :returns:
            If `wait` is :data:`False`, returns a :class:`mitogen.core.Latch`
            whose :meth:`get() <mitogen.core.Latch.get>` method returns
            :data:`None` when shutdown completes. The `timeout` parameter may
            be used to implement graceful timeouts.

    .. method:: call_async (fn, \*args, \*\*kwargs)

        See :meth:`CallChain.call_async`.

    .. method:: call (fn, \*args, \*\*kwargs)

        See :meth:`CallChain.call`.

    .. method:: call_no_reply (fn, \*args, \*\*kwargs)

        See :meth:`CallChain.call_no_reply`.


Receiver Class
==============

.. currentmodule:: mitogen.core

.. class:: Receiver (router, handle=None, persist=True, respondent=None)

    Receivers are used to wait for pickled responses from another context to be
    sent to a handle registered in this context. A receiver may be single-use
    (as in the case of :meth:`mitogen.parent.Context.call_async`) or
    multiple use.

    :param mitogen.core.Router router:
        Router to register the handler on.

    :param int handle:
        If not :data:`None`, an explicit handle to register, otherwise an
        unused handle is chosen.

    :param bool persist:
        If :data:`True`, do not unregister the receiver's handler after the
        first message.

    :param mitogen.core.Context respondent:
        Reference to the context this receiver is receiving from. If not
        :data:`None`, arranges for the receiver to receive a dead message if
        messages can no longer be routed to the context, due to disconnection
        or exit.

    .. attribute:: notify = None

        If not :data:`None`, a reference to a function invoked as
        `notify(receiver)` when a new message is delivered to this receiver.
        Used by :class:`mitogen.select.Select` to implement waiting on
        multiple receivers.

    .. py:method:: to_sender ()

        Return a :class:`mitogen.core.Sender` configured to deliver messages
        to this receiver. Since a Sender can be serialized, this makes it
        convenient to pass `(context_id, handle)` pairs around::

            def deliver_monthly_report(sender):
                for line in open('monthly_report.txt'):
                    sender.send(line)
                sender.close()

            remote = router.ssh(hostname='mainframe')
            recv = mitogen.core.Receiver(router)
            remote.call(deliver_monthly_report, recv.to_sender())
            for msg in recv:
                print(msg)

    .. py:method:: empty ()

        Return :data:`True` if calling :meth:`get` would block.

        As with :class:`Queue.Queue`, :data:`True` may be returned even
        though a subsequent call to :meth:`get` will succeed, since a
        message may be posted at any moment between :meth:`empty` and
        :meth:`get`.

        :meth:`empty` is only useful to avoid a race while installing
        :attr:`notify`:

        .. code-block:: python

            recv.notify = _my_notify_function
            if not recv.empty():
                _my_notify_function(recv)

            # It is guaranteed the receiver was empty after the notification
            # function was installed, or that it was non-empty and the
            # notification function was invoked at least once.

    .. py:method:: close ()

        Cause :class:`mitogen.core.ChannelError` to be raised in any thread
        waiting in :meth:`get` on this receiver.

    .. py:method:: get (timeout=None)

        Sleep waiting for a message to arrive on this receiver.

        :param float timeout:
            If not :data:`None`, specifies a timeout in seconds.

        :raises mitogen.core.ChannelError:
            The remote end indicated the channel should be closed, or
            communication with its parent context was lost.

        :raises mitogen.core.TimeoutError:
            Timeout was reached.

        :returns:
            `(msg, data)` tuple, where `msg` is the
            :class:`mitogen.core.Message` that was received, and `data` is
            its unpickled data part.

    .. py:method:: get_data (timeout=None)

        Like :meth:`get`, except only return the data part.

    .. py:method:: __iter__ ()

        Block and yield `(msg, data)` pairs delivered to this receiver until
        :class:`mitogen.core.ChannelError` is raised.


Sender Class
============

.. currentmodule:: mitogen.core

.. class:: Sender (context, dst_handle)

    Senders are used to send pickled messages to a handle in another context,
    it is the inverse of :class:`mitogen.core.Sender`.

    Senders may be serialized, making them convenient to wire up data flows.
    See :meth:`mitogen.core.Receiver.to_sender` for more information.

    :param mitogen.core.Context context:
        Context to send messages to.
    :param int dst_handle:
        Destination handle to send messages to.

    .. py:method:: close ()

        Send a dead message to the remote end, causing :meth:`ChannelError`
        to be raised in any waiting thread.

    .. py:method:: send (data)

        Send `data` to the remote end.


Select Class
============

.. module:: mitogen.select

.. currentmodule:: mitogen.select

.. class:: Select (receivers=(), oneshot=True)

    Support scatter/gather asynchronous calls and waiting on multiple
    receivers, channels, and sub-Selects. Accepts a sequence of
    :class:`mitogen.core.Receiver` or :class:`mitogen.select.Select`
    instances and returns the first value posted to any receiver or select.

    If `oneshot` is :data:`True`, then remove each receiver as it yields a
    result; since :meth:`__iter__` terminates once the final receiver is
    removed, this makes it convenient to respond to calls made in parallel:

    .. code-block:: python

        total = 0
        recvs = [c.call_async(long_running_operation) for c in contexts]

        for msg in mitogen.select.Select(recvs):
            print('Got %s from %s' % (msg, msg.receiver))
            total += msg.unpickle()

        # Iteration ends when last Receiver yields a result.
        print('Received total %s from %s receivers' % (total, len(recvs)))

    :class:`Select` may drive a long-running scheduler:

    .. code-block:: python

        with mitogen.select.Select(oneshot=False) as select:
            while running():
                for msg in select:
                    process_result(msg.receiver.context, msg.unpickle())
                for context, workfunc in get_new_work():
                    select.add(context.call_async(workfunc))

    :class:`Select` may be nested:

    .. code-block:: python

        subselects = [
            mitogen.select.Select(get_some_work()),
            mitogen.select.Select(get_some_work()),
            mitogen.select.Select([
                mitogen.select.Select(get_some_work()),
                mitogen.select.Select(get_some_work())
            ])
        ]

        for msg in mitogen.select.Select(selects):
            print(msg.unpickle())

    .. py:classmethod:: all (it)

        Take an iterable of receivers and retrieve a :class:`Message` from
        each, returning the result of calling `msg.unpickle()` on each in turn.
        Results are returned in the order they arrived.

        This is sugar for handling batch
        :meth:`Context.call_async <mitogen.parent.Context.call_async>`
        invocations:

        .. code-block:: python

            print('Total disk usage: %.02fMiB' % (sum(
                mitogen.select.Select.all(
                    context.call_async(get_disk_usage)
                    for context in contexts
                ) / 1048576.0
            ),))

        However, unlike in a naive comprehension such as:

        .. code-block:: python

            recvs = [c.call_async(get_disk_usage) for c in contexts]
            sum(recv.get().unpickle() for recv in recvs)

        Result processing happens in the order results arrive, rather than the
        order requests were issued, so :meth:`all` should always be faster.

    .. py:method:: get (timeout=None, block=True)

        Fetch the next available value from any receiver, or raise
        :class:`mitogen.core.TimeoutError` if no value is available within
        `timeout` seconds.

        On success, the message's :attr:`receiver
        <mitogen.core.Message.receiver>` attribute is set to the receiver.

        :param float timeout:
            Timeout in seconds.
        :param bool block:
            If :data:`False`, immediately raise
            :class:`mitogen.core.TimeoutError` if the select is empty.
        :return:
            :class:`mitogen.core.Message`
        :raises mitogen.core.TimeoutError:
            Timeout was reached.
        :raises mitogen.core.LatchError:
            :meth:`close` has been called, and the underlying latch is no
            longer valid.

    .. py:method:: __bool__ ()

        Return :data:`True` if any receivers are registered with this select.

    .. py:method:: close ()

        Remove the select's notifier function from each registered receiver,
        mark the associated latch as closed, and cause any thread currently
        sleeping in :meth:`get` to be woken with
        :class:`mitogen.core.LatchError`.

        This is necessary to prevent memory leaks in long-running receivers. It
        is called automatically when the Python :keyword:`with` statement is
        used.

    .. py:method:: empty ()

        Return :data:`True` if calling :meth:`get` would block.

        As with :class:`Queue.Queue`, :data:`True` may be returned even
        though a subsequent call to :meth:`get` will succeed, since a
        message may be posted at any moment between :meth:`empty` and
        :meth:`get`.

        :meth:`empty` may return :data:`False` even when :meth:`get`
        would block if another thread has drained a receiver added to this
        select. This can be avoided by only consuming each receiver from a
        single thread.

    .. py:method:: __iter__ (self)

        Yield the result of :meth:`get` until no receivers remain in the
        select, either because `oneshot` is :data:`True`, or each receiver was
        explicitly removed via :meth:`remove`.

    .. py:method:: add (recv)

        Add the :class:`mitogen.core.Receiver` or
        :class:`mitogen.core.Channel` `recv` to the select.

    .. py:method:: remove (recv)

        Remove the :class:`mitogen.core.Receiver` or
        :class:`mitogen.core.Channel` `recv` from the select. Note that if
        the receiver has notified prior to :meth:`remove`, then it will
        still be returned by a subsequent :meth:`get`. This may change in a
        future version.


Channel Class
=============

.. currentmodule:: mitogen.core

.. class:: Channel (router, context, dst_handle, handle=None)

    A channel inherits from :class:`mitogen.core.Sender` and
    `mitogen.core.Receiver` to provide bidirectional functionality.

    Since all handles aren't known until after both ends are constructed, for
    both ends to communicate through a channel, it is necessary for one end to
    retrieve the handle allocated to the other and reconfigure its own channel
    to match. Currently this is a manual task.


Broker Class
============

.. currentmodule:: mitogen.core
.. class:: Broker

    Responsible for handling I/O multiplexing in a private thread.

    **Note:** This is the somewhat limited core version of the Broker class
    used by child contexts. The master subclass is documented below.

    .. attribute:: shutdown_timeout = 3.0

        Seconds grace to allow :class:`streams <Stream>` to shutdown
        gracefully before force-disconnecting them during :meth:`shutdown`.

    .. method:: defer (func, \*args, \*kwargs)

        Arrange for `func(\*args, \**kwargs)` to be executed on the broker
        thread, or immediately if the current thread is the broker thread. Safe
        to call from any thread.

    .. method:: defer_sync (func)

        Arrange for `func()` to execute on the broker thread, blocking the
        current thread until a result or exception is available.

        :returns:
            Call result.

    .. method:: start_receive (stream)

        Mark the :attr:`receive_side <Stream.receive_side>` on `stream` as
        ready for reading. Safe to call from any thread. When the associated
        file descriptor becomes ready for reading,
        :meth:`BasicStream.on_receive` will be called.

    .. method:: stop_receive (stream)

        Mark the :attr:`receive_side <Stream.receive_side>` on `stream` as
        not ready for reading. Safe to call from any thread.

    .. method:: _start_transmit (stream)

        Mark the :attr:`transmit_side <Stream.transmit_side>` on `stream` as
        ready for writing. Must only be called from the Broker thread. When the
        associated file descriptor becomes ready for writing,
        :meth:`BasicStream.on_transmit` will be called.

    .. method:: stop_receive (stream)

        Mark the :attr:`transmit_side <Stream.receive_side>` on `stream` as
        not ready for writing. Safe to call from any thread.

    .. method:: shutdown

        Request broker gracefully disconnect streams and stop.

    .. method:: join

        Wait for the broker to stop, expected to be called after
        :meth:`shutdown`.

    .. method:: keep_alive

        Return :data:`True` if any reader's :attr:`Side.keep_alive`
        attribute is :data:`True`, or any
        :class:`Context <mitogen.core.Context>` is still
        registered that is not the master. Used to delay shutdown while some
        important work is in progress (e.g. log draining).

    **Internal Methods**

    .. method:: _broker_main

        Handle events until :meth:`shutdown`. On shutdown, invoke
        :meth:`Stream.on_shutdown` for every active stream, then allow up to
        :attr:`shutdown_timeout` seconds for the streams to unregister
        themselves before forcefully calling
        :meth:`Stream.on_disconnect`.


.. currentmodule:: mitogen.master
.. class:: Broker (install_watcher=True)

    .. note::

        You may construct as many brokers as desired, and use the same broker
        for multiple routers, however usually only one broker need exist.
        Multiple brokers may be useful when dealing with sets of children with
        differing lifetimes. For example, a subscription service where
        non-payment results in termination for one customer.

    :param bool install_watcher:
        If :data:`True`, an additional thread is started to monitor the
        lifetime of the main thread, triggering :meth:`shutdown`
        automatically in case the user forgets to call it, or their code
        crashed.

        You should not rely on this functionality in your program, it is only
        intended as a fail-safe and to simplify the API for new users. In
        particular, alternative Python implementations may not be able to
        support watching the main thread.

    .. attribute:: shutdown_timeout = 5.0

        Seconds grace to allow :class:`streams <Stream>` to shutdown
        gracefully before force-disconnecting them during :meth:`shutdown`.


Utility Functions
=================

.. module:: mitogen.utils

A random assortment of utility functions useful on masters and children.

.. currentmodule:: mitogen.utils
.. function:: cast (obj)

    Many tools love to subclass built-in types in order to implement useful
    functionality, such as annotating the safety of a Unicode string, or adding
    additional methods to a dict. However, cPickle loves to preserve those
    subtypes during serialization, resulting in CallError during :meth:`call
    <mitogen.parent.Context.call>` in the target when it tries to deserialize
    the data.

    This function walks the object graph `obj`, producing a copy with any
    custom sub-types removed. The functionality is not default since the
    resulting walk may be computationally expensive given a large enough graph.

    See :ref:`serialization-rules` for a list of supported types.

    :param obj:
        Object to undecorate.
    :returns:
        Undecorated object.

.. currentmodule:: mitogen.utils
.. function:: disable_site_packages

    Remove all entries mentioning ``site-packages`` or ``Extras`` from the
    system path. Used primarily for testing on OS X within a virtualenv, where
    OS X bundles some ancient version of the :mod:`six` module.

.. currentmodule:: mitogen.utils
.. function:: log_to_file (path=None, io=False, level='INFO')

    Install a new :class:`logging.Handler` writing applications logs to the
    filesystem. Useful when debugging slave IO problems.

    Parameters to this function may be overridden at runtime using environment
    variables. See :ref:`logging-env-vars`.

    :param str path:
        If not :data:`None`, a filesystem path to write logs to. Otherwise,
        logs are written to :data:`sys.stderr`.

    :param bool io:
        If :data:`True`, include extremely verbose IO logs in the output.
        Useful for debugging hangs, less useful for debugging application code.

    :param str level:
        Name of the :mod:`logging` package constant that is the minimum
        level to log at. Useful levels are ``DEBUG``, ``INFO``, ``WARNING``,
        and ``ERROR``.

.. currentmodule:: mitogen.utils
.. function:: run_with_router(func, \*args, \**kwargs)

    Arrange for `func(router, \*args, \**kwargs)` to run with a temporary
    :class:`mitogen.master.Router`, ensuring the Router and Broker are
    correctly shut down during normal or exceptional return.

    :returns:
        `func`'s return value.

.. currentmodule:: mitogen.utils
.. decorator:: with_router

    Decorator version of :func:`run_with_router`. Example:

    .. code-block:: python

        @with_router
        def do_stuff(router, arg):
            pass

        do_stuff(blah, 123)


Exceptions
==========

.. currentmodule:: mitogen.core

.. autoclass:: Error
.. autoclass:: CallError
.. autoclass:: ChannelError
.. autoclass:: LatchError
.. autoclass:: StreamError
.. autoclass:: TimeoutError
