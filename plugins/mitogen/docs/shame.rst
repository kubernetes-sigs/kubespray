
Importer Wall Of Shame
----------------------

The following modules and packages violate protocol or best practice in some way:

* They run magic during ``__init.py__`` that makes life hard for Mitogen.
  Executing code during module import is always bad, and Mitogen is a concrete
  benchmark for why it's bad.

* They install crap in :py:data:`sys.modules` that completely ignore or
  partially implement the protocols laid out in PEP-302.

* They "vendor" a third party package, either incompletely, using hacks visible
  through the runtime's standard interfaces, or with ancient versions of code
  that in turn mess with :py:data:`sys.modules` in some horrible way.

Bugs will probably be filed for these in time, but it does not address the huge
installed base of existing old software versions, so hacks are needed anyway.


``pbr``
=======

It claims to use ``pkg_resources`` to read version information
(``_get_version_from_pkg_metadata()``), which would result in PEP-302 being
reused and everything just working wonderfully, but instead it actually does
direct filesystem access.

**What could it do instead?**

* ``pkg_resources.resource_stream()``

**What Mitogen is forced to do**

When it sees ``pbr`` being loaded, it smodges the process environment with a
``PBR_VERSION`` variable to override any attempt to auto-detect the version.
This will probably break code I haven't seen yet.


``pkg_resources``
=================

Anything that imports ``pkg_resources`` will eventually cause ``pkg_resources``
to try and import and scan ``__main__`` for its ``__requires__`` attribute
(``pkg_resources/__init__.py::_build_master()``). This breaks any app that is
not expecting its ``__main__`` to suddenly be sucked over a network and
injected into a remote process, like py.test.

A future version of Mitogen might have a more general hack that doesn't import
the master's ``__main__`` as ``__main__`` in the slave, avoiding all kinds of
issues like these.

**What could it do instead?**

* Explicit is better than implicit: wait until the magical behaviour is
  explicitly requested (i.e. an API call).

* Use ``get("__main__")`` on :py:data:`sys.modules` rather than ``import``, but
  this method isn't general enough, it only really helps tools like Mitogen.

**What Mitogen is forced to do**

Examine the stack during every attempt to import ``__main__`` and check if the
requestee module is named ``pkg_resources``, if so then refuse the import.


``six``
=======

The ``six`` module makes some effort to conform to PEP-302, but it is missing
several critical pieces, e.g. the ``__loader__`` attribute. This not only
breaks the Python standard library tooling (such as the :py:mod:`inspect`
module), but also Mitogen. Newer versions of ``six`` improve things somewhat,
but there are still outstanding issues preventing Mitogen from working with
``six``.

This package is sufficiently popular that it must eventually be supported. See
`here for an example issue`_.

.. _here for an example issue: https://github.com/dw/mitogen/issues/31

**What could it do instead?**

* Any custom hacks installed into :py:data:`sys.modules` should support the
  protocols laid out in PEP-302.

**What Mitogen is forced to do**

Vendored versions of ``six`` currently don't work at all.
