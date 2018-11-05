
.. currentmodule:: mitogen.service

.. _service:

Service Framework
=================

.. warning::

    This section is incomplete.

Mitogen includes a simple framework for implementing services exposed to other
contexts, with some built-in subclasses to capture common designs. This is a
work in progress, and new functionality will be added as common usage patterns
emerge.


Overview
--------

Service

* User-supplied class with explicitly exposed methods.
* May be auto-imported/constructed in a child from a parent simply by calling it
* Identified in calls by its canonical name (e.g. mypkg.mymod.MyClass) by
  default, but may use any naming scheme the configured activator understands.
* Children receive refusals if the class is not already activated by a aprent
* Has an associated Select instance which may be dynamically loaded with
  receivers over time, on_message_received() invoked if any receiver becomes
  ready.

Invoker

* Abstracts mechanism for calling a service method and verifying permissions.
* Built-in 'service.Invoker': concurrent execution of all methods on the thread pool.
* Built-in 'service.SerializedInvoker': serialization of all calls on a single
  thread borrowed from the pool while any request is pending.
* Built-in 'service.DeduplicatingInvoker': requests are aggregated by distinct
  (method, kwargs) key, only one such method ever executes, return value is
  cached and broadcast to all request waiters. Waiters do not block additional
  pool threads.

Activator

* Abstracts mechanism for activating a service and verifying activation
  permission.
* Built-in activator looks for service by fully.qualified.ClassName using
  Python import mechanism, and only permits parents to trigger activation.

Pool

* Manages a fixed-size thread pool, mapping of service name to Invoker, and an
  aggregate Select over every activate service's Selects.
* Constructed automatically in children in response to the first
  CALL_SERVICE message sent to them by a parent.
* Must be constructed manually in parent context.
* Has close() and add() methods.


Example
-------

.. code-block:: python

    import mitogen
    import mitogen.service


    class FileService(mitogen.service.Service):
        """
        Simple file server, for demonstration purposes only! Use of this in
        real code would be a security vulnerability as it would permit children
        to read arbitrary files from the master's disk.
        """
        handle = 500
        required_args = {
            'path': str
        }

        def dispatch(self, args, msg):
            with open(args['path'], 'r') as fp:
                return fp.read()


    def download_file(context, path):
        s = mitogen.service.call(context, FileService.handle, {
            'path': path
        })

        with open(path, 'w') as fp:
            fp.write(s)


    @mitogen.core.takes_econtext
    def download_some_files(paths, econtext):
        for path in paths:
            download_file(econtext.master, path)


    @mitogen.main()
    def main(router):
        pool = mitogen.service.Pool(router, size=1, services=[
            FileService(router),
        ])

        remote = router.ssh(hostname='k3')
        remote.call(download_some_files, [
            '/etc/passwd',
            '/etc/hosts',
        ])
        pool.stop()


Reference
---------

.. autoclass:: mitogen.service.Policy
.. autoclass:: mitogen.service.AllowParents
.. autoclass:: mitogen.service.AllowAny

.. autofunction:: mitogen.service.arg_spec
.. autofunction:: mitogen.service.expose

.. autofunction:: mitogen.service.Service

.. autoclass:: mitogen.service.Invoker
.. autoclass:: mitogen.service.SerializedInvoker
.. autoclass:: mitogen.service.DeduplicatingInvoker

.. autoclass:: mitogen.service.Service
    :members:

.. autoclass:: mitogen.service.Pool
    :members:

