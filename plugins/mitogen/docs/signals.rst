
.. _signals:

Signals
=======

Mitogen contains a simplistic signal mechanism to help decouple its internal
components. When a signal is fired by a particular instance of a class, any
functions registered to receive it will be called back.

.. warning::

    As signals execute on the Broker thread, and without exception handling,
    they are generally unsafe for consumption by user code, as any bugs could
    trigger crashes and hangs for which the broker is unable to forward logs,
    or ensure the buggy context always shuts down on disconnect.


Functions
---------

.. currentmodule:: mitogen.core

.. autofunction:: listen
.. autofunction:: fire


List
----

These signals are used internally by Mitogen.

.. list-table::
    :header-rows: 1
    :widths: auto

    * - Class
      - Name
      - Description

    * - :py:class:`mitogen.core.Stream`
      - ``disconnect``
      - Fired on the Broker thread when disconnection is detected.

    * - :py:class:`mitogen.core.Context`
      - ``disconnect``
      - Fired on the Broker thread during shutdown (???)

    * - :py:class:`mitogen.core.Router`
      - ``shutdown``
      - Fired on the Broker thread after Broker.shutdown() is called.

    * - :py:class:`mitogen.core.Broker`
      - ``shutdown``
      - Fired after Broker.shutdown() is called.

    * - :py:class:`mitogen.core.Broker`
      - ``exit``
      - Fired immediately prior to the broker thread exit.

