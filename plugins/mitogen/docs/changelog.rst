
.. _changelog:

Release Notes
=============


.. raw:: html

    <style>
        div#release-notes h2 {
            border-bottom: 1px dotted #c0c0c0;
            margin-top: 40px;
        }
    </style>


v0.2.4 (2018-??-??)
------------------

Mitogen for Ansible
~~~~~~~~~~~~~~~~~~~

Enhancements
^^^^^^^^^^^^

* `#369 <https://github.com/dw/mitogen/issues/369>`_: :meth:`Connection.reset`
  is implemented, allowing `meta: reset_connection
  <https://docs.ansible.com/ansible/latest/modules/meta_module.html>`_ to shut
  down the remote interpreter as expected, and improving support for the
  `reboot
  <https://docs.ansible.com/ansible/latest/modules/reboot_module.html>`_
  module.


Fixes
^^^^^

* `#334 <https://github.com/dw/mitogen/issues/334>`_: the SSH method
  tilde-expands private key paths using Ansible's logic. Previously Mitogen
  passed the path unmodified to SSH, which would expand it using
  :func:`os.getpwent`.

  This differs from :func:`os.path.expanduser`, which prefers the ``HOME``
  environment variable if it is set, causing behaviour to diverge when Ansible
  was invoked using sudo without appropriate flags to cause the ``HOME``
  environment variable to be reset to match the target account.

* `#373 <https://github.com/dw/mitogen/issues/373>`_: the LXC and LXD methods
  now print a useful hint when Python fails to start, as no useful error is
  normally logged to the console by these tools.


Core Library
~~~~~~~~~~~~

* `#76 <https://github.com/dw/mitogen/issues/76>`_: routing maintains the set
  of destination context ID ever received on each stream, and when
  disconnection occurs, propagates ``DEL_ROUTE`` messages downwards towards
  every stream that ever communicated with a disappearing peer, rather than
  simply toward parents.

  Conversations between nodes in any level of the tree receive ``DEL_ROUTE``
  messages when a participant disconnects, allowing receivers to be woken with
  :class:`mitogen.core.ChannelError` to signal the connection has broken, even
  when one participant is not a parent of the other.

* `#405 <https://github.com/dw/mitogen/issues/405>`_: if a message is rejected
  due to being too large, and it has a ``reply_to`` set, a dead message is
  returned to the sender. This ensures function calls exceeding the configured
  maximum size crash rather than hang.

* `#411 <https://github.com/dw/mitogen/issues/411>`_: the SSH method typed
  "``y``" rather than the requisite "``yes``" when `check_host_keys="accept"`
  was configured. This would lead to connection timeouts due to the hung
  response.

* `16ca111e <https://github.com/dw/mitogen/commit/16ca111e>`_: handle OpenSSH
  7.5 permission denied prompts when ``~/.ssh/config`` rewrites are present.

* `9ec360c2 <https://github.com/dw/mitogen/commit/9ec360c2>`_: a new
  :meth:`mitogen.core.Broker.defer_sync` utility function is provided.


Thanks!
~~~~~~~

Mitogen would not be possible without the support of users. A huge thanks for
bug reports, features and fixes in this release contributed by
`Brian Candler <https://github.com/candlerb>`_, and
`Guy Knights <https://github.com/knightsg>`_.


v0.2.3 (2018-10-23)
-------------------

Mitogen for Ansible
~~~~~~~~~~~~~~~~~~~

Enhancements
^^^^^^^^^^^^

* `#315 <https://github.com/dw/mitogen/pull/315>`_,
  `#392 <https://github.com/dw/mitogen/issues/392>`_: Ansible 2.6 and 2.7 are
  supported.

* `#321 <https://github.com/dw/mitogen/issues/321>`_,
  `#336 <https://github.com/dw/mitogen/issues/336>`_: temporary file handling
  was simplified, undoing earlier damage caused by compatibility fixes,
  improving 2.6 compatibility, and avoiding two network roundtrips for every
  related action
  (`assemble <http://docs.ansible.com/ansible/latest/modules/assemble_module.html>`_,
  `aws_s3 <http://docs.ansible.com/ansible/latest/modules/aws_s3_module.html>`_,
  `copy <http://docs.ansible.com/ansible/latest/modules/copy_module.html>`_,
  `patch <http://docs.ansible.com/ansible/latest/modules/patch_module.html>`_,
  `script <http://docs.ansible.com/ansible/latest/modules/script_module.html>`_,
  `template <http://docs.ansible.com/ansible/latest/modules/template_module.html>`_,
  `unarchive <http://docs.ansible.com/ansible/latest/modules/unarchive_module.html>`_,
  `uri <http://docs.ansible.com/ansible/latest/modules/uri_module.html>`_). See
  :ref:`ansible_tempfiles` for a complete description.

* `#376 <https://github.com/dw/mitogen/pull/376>`_,
  `#377 <https://github.com/dw/mitogen/pull/377>`_: the ``kubectl`` connection
  type is now supported. Contributed by Yannig Perré.

* `084c0ac0 <https://github.com/dw/mitogen/commit/084c0ac0>`_: avoid a
  roundtrip in
  `copy <http://docs.ansible.com/ansible/latest/modules/copy_module.html>`_ and
  `template <http://docs.ansible.com/ansible/latest/modules/template_module.html>`_
  due to an unfortunate default.

* `7458dfae <https://github.com/dw/mitogen/commit/7458dfae>`_: avoid a
  roundtrip when transferring files smaller than 124KiB. Copy and template
  actions are now 2-RTT, reducing runtime for a 20-iteration template loop over
  a 250 ms link from 30 seconds to 10 seconds compared to v0.2.2, down from 120
  seconds compared to vanilla.

* `#337 <https://github.com/dw/mitogen/issues/337>`_: To avoid a scaling
  limitation, a PTY is no longer allocated for an SSH connection unless the
  configuration specifies a password.

* `d62e6e2a <https://github.com/dw/mitogen/commit/d62e6e2a>`_: many-target
  runs executed the dependency scanner redundantly due to missing
  synchronization, wasting significant runtime in the connection multiplexer.
  In one case work was reduced by 95%, which may manifest as faster runs.

* `5189408e <https://github.com/dw/mitogen/commit/5189408e>`_: threads are
  cooperatively scheduled, minimizing `GIL
  <https://en.wikipedia.org/wiki/Global_interpreter_lock>`_ contention, and
  reducing context switching by around 90%. This manifests as an overall
  improvement, but is easily noticeable on short many-target runs, where
  startup overhead dominates runtime.

* The `faulthandler <https://faulthandler.readthedocs.io/>`_ module is
  automatically activated if it is installed, simplifying debugging of hangs.
  See :ref:`diagnosing-hangs` for details.

* The ``MITOGEN_DUMP_THREAD_STACKS`` environment variable's value now indicates
  the number of seconds between stack dumps. See :ref:`diagnosing-hangs` for
  details.


Fixes
^^^^^

* `#251 <https://github.com/dw/mitogen/issues/251>`_,
  `#340 <https://github.com/dw/mitogen/issues/340>`_: Connection Delegation
  could establish connections to the wrong target when ``delegate_to:`` is
  present.

* `#291 <https://github.com/dw/mitogen/issues/291>`_: when Mitogen had
  previously been installed using ``pip`` or ``setuptools``, the globally
  installed version could conflict with a newer version bundled with an
  extension that had been installed using the documented steps. Now the bundled
  library always overrides over any system-installed copy.

* `#324 <https://github.com/dw/mitogen/issues/324>`_: plays with a
  `custom module_utils <https://docs.ansible.com/ansible/latest/reference_appendices/config.html#default-module-utils-path>`_
  would fail due to fallout from the Python 3 port and related tests being
  disabled.

* `#331 <https://github.com/dw/mitogen/issues/331>`_: the connection
  multiplexer subprocess always exits before the main Ansible process, ensuring
  logs generated by it do not overwrite the user's prompt when ``-vvv`` is
  enabled.

* `#332 <https://github.com/dw/mitogen/issues/332>`_: support a new
  :func:`sys.excepthook`-based module exit mechanism added in Ansible 2.6.

* `#338 <https://github.com/dw/mitogen/issues/338>`_: compatibility: changes to
  ``/etc/environment`` and ``~/.pam_environment`` made by a task are reflected
  in the runtime environment of subsequent tasks. See
  :ref:`ansible_process_env` for a complete description.

* `#343 <https://github.com/dw/mitogen/issues/343>`_: the sudo ``--login``
  option is supported.

* `#344 <https://github.com/dw/mitogen/issues/344>`_: connections no longer
  fail when the controller's login username contains slashes.

* `#345 <https://github.com/dw/mitogen/issues/345>`_: the ``IdentitiesOnly
  yes`` option is no longer supplied to OpenSSH by default, better matching
  Ansible's behaviour.

* `#355 <https://github.com/dw/mitogen/issues/355>`_: tasks configured to run
  in an isolated forked subprocess were forked from the wrong parent context.
  This meant built-in modules overridden via a custom ``module_utils`` search
  path may not have had any effect.

* `#362 <https://github.com/dw/mitogen/issues/362>`_: to work around a slow
  algorithm in the :mod:`subprocess` module, the maximum number of open files
  in processes running on the target is capped to 512, reducing the work
  required to start a subprocess by >2000x in default CentOS configurations.

* `#397 <https://github.com/dw/mitogen/issues/397>`_: recent Mitogen master
  versions could fail to clean up temporary directories in a number of
  circumstances, and newer Ansibles moved to using :mod:`atexit` to effect
  temporary directory cleanup in some circumstances.

* `b9112a9c <https://github.com/dw/mitogen/commit/b9112a9c>`_,
  `2c287801 <https://github.com/dw/mitogen/commit/2c287801>`_: OpenSSH 7.5
  permission denied prompts are now recognized. Contributed by Alex Willmer.

* A missing check caused an exception traceback to appear when using the
  ``ansible`` command-line tool with a missing or misspelled module name.

* Ansible since >=2.7 began importing :mod:`__main__` from
  :mod:`ansible.module_utils.basic`, causing an error during execution, due to
  the controller being configured to refuse network imports outside the
  ``ansible.*`` namespace. Update the target implementation to construct a stub
  :mod:`__main__` module to satisfy the otherwise seemingly vestigial import.


Core Library
~~~~~~~~~~~~

* A new :class:`mitogen.parent.CallChain` class abstracts safe pipelining of
  related function calls to a target context, cancelling the chain if an
  exception occurs.

* `#305 <https://github.com/dw/mitogen/issues/305>`_: fix a long-standing minor
  race relating to the logging framework, where *no route for Message..*
  would frequently appear during startup.

* `#313 <https://github.com/dw/mitogen/issues/313>`_:
  :meth:`mitogen.parent.Context.call` was documented as capable of accepting
  static methods. While possible on Python 2.x the result is ugly, and in every
  case it should be trivial to replace with a classmethod. The documentation
  was fixed.

* `#337 <https://github.com/dw/mitogen/issues/337>`_: to avoid a scaling
  limitation, a PTY is no longer allocated for each OpenSSH client if it can be
  avoided. PTYs are only allocated if a password is supplied, or when
  `host_key_checking=accept`. This is since Linux has a default of 4096 PTYs
  (``kernel.pty.max``), while OS X has a default of 127 and an absolute maximum
  of 999 (``kern.tty.ptmx_max``).

* `#339 <https://github.com/dw/mitogen/issues/339>`_: the LXD connection method
  was erroneously executing LXC Classic commands.

* `#345 <https://github.com/dw/mitogen/issues/345>`_: the SSH connection method
  allows optionally disabling ``IdentitiesOnly yes``.

* `#356 <https://github.com/dw/mitogen/issues/356>`_: if the master Python
  process does not have :data:`sys.executable` set, the default Python
  interpreter used for new children on the local machine defaults to
  ``"/usr/bin/python"``.

* `#366 <https://github.com/dw/mitogen/issues/366>`_,
  `#380 <https://github.com/dw/mitogen/issues/380>`_: attempts by children to
  import :mod:`__main__` where the main program module lacks an execution guard
  are refused, and an error is logged. This prevents a common and highly
  confusing error when prototyping new scripts.

* `#371 <https://github.com/dw/mitogen/pull/371>`_: the LXC connection method
  uses a more compatible method to establish an non-interactive session.
  Contributed by Brian Candler.

* `af2ded66 <https://github.com/dw/mitogen/commit/af2ded66>`_: add
  :func:`mitogen.fork.on_fork` to allow non-Mitogen managed process forks to
  clean up Mitogen resources in the child.

* `d6784242 <https://github.com/dw/mitogen/commit/d6784242>`_: the setns method
  always resets ``HOME``, ``SHELL``, ``LOGNAME`` and ``USER`` environment
  variables to an account in the target container, defaulting to ``root``.

* `830966bf <https://github.com/dw/mitogen/commit/830966bf>`_: the UNIX
  listener no longer crashes if the peer process disappears in the middle of
  connection setup.


Thanks!
~~~~~~~

Mitogen would not be possible without the support of users. A huge thanks for
bug reports, features and fixes in this release contributed by
`Alex Russu <https://github.com/alexrussu>`_,
`Alex Willmer <https://github.com/moreati>`_,
`atoom <https://github.com/atoom>`_,
`Berend De Schouwer <https://github.com/berenddeschouwer>`_,
`Brian Candler <https://github.com/candlerb>`_,
`Dan Quackenbush <https://github.com/danquack>`_,
`dsgnr <https://github.com/dsgnr>`_,
`Jesse London <https://github.com/jesteria>`_,
`John McGrath <https://github.com/jmcgrath207>`_,
`Jonathan Rosser <https://github.com/jrosser>`_,
`Josh Smift <https://github.com/jbscare>`_,
`Luca Nunzi <https://github.com/0xlc>`_,
`Orion Poplawski <https://github.com/opoplawski>`_,
`Peter V. Saveliev <https://github.com/svinota>`_,
`Pierre-Henry Muller <https://github.com/pierrehenrymuller>`_,
`Pierre-Louis Bonicoli <https://github.com/jesteria>`_,
`Prateek Jain <https://github.com/prateekj201>`_,
`RedheatWei <https://github.com/RedheatWei>`_,
`Rick Box <https://github.com/boxrick>`_,
`nikitakazantsev12 <https://github.com/nikitakazantsev12>`_,
`Tawana Musewe <https://github.com/tbtmuse>`_,
`Timo Beckers <https://github.com/ti-mo>`_, and
`Yannig Perré <https://github.com/yannig>`_.


v0.2.2 (2018-07-26)
-------------------

Mitogen for Ansible
~~~~~~~~~~~~~~~~~~~

* `#291 <https://github.com/dw/mitogen/issues/291>`_: ``ansible_*_interpreter``
  variables are parsed using a restrictive shell-like syntax, supporting a
  common idiom where ``ansible_python_interpreter`` is set to ``/usr/bin/env
  python``.

* `#299 <https://github.com/dw/mitogen/issues/299>`_: fix the ``network_cli``
  connection type when the Mitogen strategy is active. Mitogen cannot help
  network device connections, however it should still be possible to use device
  connections while Mitogen is active.

* `#301 <https://github.com/dw/mitogen/pull/301>`_: variables like ``$HOME`` in
  the ``remote_tmp`` setting are evaluated correctly.

* `#303 <https://github.com/dw/mitogen/pull/303>`_: the :ref:`doas` become method
  is supported. Contributed by `Mike Walker
  <https://github.com/napkindrawing>`_.

* `#309 <https://github.com/dw/mitogen/issues/309>`_: fix a regression to
  process environment cleanup, caused by the change in v0.2.1 to run local
  tasks with the correct environment.

* `#317 <https://github.com/dw/mitogen/issues/317>`_: respect the verbosity
  setting when writing to Ansible's ``log_path``, if it is enabled. Child log
  filtering was also incorrect, causing the master to needlessly wake many
  times. This nets a 3.5% runtime improvement running against the local
  machine.

* The ``mitogen_ssh_debug_level`` variable is supported, permitting SSH debug
  output to be included in Mitogen's ``-vvv`` output when both are specified.


Core Library
~~~~~~~~~~~~

* `#291 <https://github.com/dw/mitogen/issues/291>`_: the ``python_path``
  parameter may specify an argument vector prefix rather than a string program
  path.

* `#300 <https://github.com/dw/mitogen/issues/300>`_: the broker could crash on
  OS X during shutdown due to scheduled `kqueue
  <https://www.freebsd.org/cgi/man.cgi?query=kevent>`_ filter changes for
  descriptors that were closed before the IO loop resumes. As a temporary
  workaround, kqueue's bulk change feature is not used.

* `#303 <https://github.com/dw/mitogen/pull/303>`_: the :ref:`doas` become method
  is now supported. Contributed by `Mike Walker
  <https://github.com/napkindrawing>`_.

* `#307 <https://github.com/dw/mitogen/issues/307>`_: SSH login banner output
  containing the word 'password' is no longer confused for a password prompt.

* `#319 <https://github.com/dw/mitogen/issues/319>`_: SSH connections would
  fail immediately on Windows Subsystem for Linux, due to use of `TCSAFLUSH`
  with :func:`termios.tcsetattr`. The flag is omitted if WSL is detected.

* `#320 <https://github.com/dw/mitogen/issues/320>`_: The OS X poller
  could spuriously wake up due to ignoring an error bit set on events returned
  by the kernel, manifesting as a failure to read from an unrelated descriptor.

* `#342 <https://github.com/dw/mitogen/issues/342>`_: The ``network_cli``
  connection type would fail due to a missing internal SSH plugin method.

* Standard IO forwarding accidentally configured the replacement ``stdout`` and
  ``stderr`` write descriptors as non-blocking, causing subprocesses that
  generate more output than kernel buffer space existed to throw errors. The
  write ends are now configured as blocking.

* When :func:`mitogen.core.enable_profiling` is active, :mod:`mitogen.service`
  threads are profiled just like other threads.

* The ``ssh_debug_level`` parameter is supported, permitting SSH debug output
  to be redirected to a Mitogen logger when specified.

* Debug logs containing command lines are printed with the minimal quoting and
  escaping required.


Thanks!
~~~~~~~

Mitogen would not be possible without the support of users. A huge thanks for
the bug reports and pull requests in this release contributed by
`Alex Russu <https://github.com/alexrussu>`_,
`Andy Freeland <https://github.com/rouge8>`_,
`Ayaz Ahmed Khan <https://github.com/ayaz>`_,
`Colin McCarthy <https://github.com/colin-mccarthy>`_,
`Dan Quackenbush <https://github.com/danquack>`_,
`Duane Zamrok <https://github.com/dewthefifth>`_,
`Gonzalo Servat <https://github.com/gservat>`_,
`Guy Knights <https://github.com/knightsg>`_,
`Josh Smift <https://github.com/jbscare>`_,
`Mark Janssen <https://github.com/sigio>`_,
`Mike Walker <https://github.com/napkindrawing>`_,
`Orion Poplawski <https://github.com/opoplawski>`_,
`falbanese <https://github.com/falbanese>`_,
`Tawana Musewe <https://github.com/tbtmuse>`_, and
`Zach Swanson <https://github.com/zswanson>`_.


v0.2.1 (2018-07-10)
-------------------

Mitogen for Ansible
~~~~~~~~~~~~~~~~~~~

* `#297 <https://github.com/dw/mitogen/issues/297>`_: compatibility: local
  actions set their working directory to that of their defining playbook, and
  inherit a process environment as if they were executed as a subprocess of the
  forked task worker.


v0.2.0 (2018-07-09)
-------------------

Mitogen 0.2.x is the inaugural feature-frozen branch eligible for fixes only,
except for problem areas listed as in-scope below. While stable from a
development perspective, it should still be considered "beta" at least for the
initial releases.

**In Scope**

* Python 3.x performance improvements
* Subprocess reaping improvements
* Major documentation improvements
* PyPI/packaging improvements
* Test suite improvements
* Replacement CI system to handle every supported OS
* Minor deviations from vanilla Ansible behaviour
* Ansible ``raw`` action support

The goal is a *tick/tock* model where even-numbered series are a maturation of
the previous unstable series, and unstable series are released on PyPI with
``--pre`` enabled. The API and user visible behaviour should remain unchanged
within a stable series.


Mitogen for Ansible
~~~~~~~~~~~~~~~~~~~

* Support for Ansible 2.3 - 2.7.x and any mixture of Python 2.6, 2.7 or 3.6 on
  controller and target nodes.

* Drop-in support for many Ansible connection types.

* Preview of Connection Delegation feature.

* Built-in file transfer compatible with connection delegation.


**Known Issues**

* The ``raw`` action executes as a regular Mitogen connection, which requires
  Python on the target, precluding its use for installing Python. This will be
  addressed in a future 0.2 release. For now, simply mix Mitogen and vanilla
  Ansible strategies in your playbook:

  .. code-block:: yaml

    - hosts: web-servers
      strategy: linear
      tasks:
      - name: Install Python if necessary.
        raw: test -e /usr/bin/python || apt install -y python-minimal

    - hosts: web-servers
      strategy: mitogen_linear
      roles:
      - nginx
      - initech_app
      - y2k_fix

.. * When running with ``-vvv``, log messages will be printed to the console
     *after* the Ansible run completes, as connection multiplexer shutdown only
     begins after Ansible exits. This is due to a lack of suitable shutdown hook
     in Ansible, and is fairly harmless, albeit cosmetically annoying. A future
     release may include a solution.

.. * Configurations will break that rely on the `hashbang argument splitting
     behaviour <https://github.com/ansible/ansible/issues/15635>`_ of the
     ``ansible_python_interpreter`` setting, contrary to the Ansible
     documentation. This will be addressed in a future 0.2 release.

* The Ansible 2.7 ``reboot`` module is not yet supported.

* Performance does not scale linearly with target count. This requires
  significant additional work, as major bottlenecks exist in the surrounding
  Ansible code. Performance-related bug reports for any scenario remain
  welcome with open arms.

* Performance on Python 3 is significantly worse than on Python 2. While this
  has not yet been investigated, at least some of the regression appears to be
  part of the core library, and should therefore be straightforward to fix as
  part of 0.2.x.

* *Module Replacer* style Ansible modules are not supported.

* Actions are single-threaded for each `(host, user account)` combination,
  including actions that execute on the local machine. Playbooks may experience
  slowdown compared to vanilla Ansible if they employ long-running
  ``local_action`` or ``delegate_to`` tasks delegating many target hosts to a
  single machine and user account.

* Connection Delegation remains in preview and has bugs around how it infers
  connections. Connection establishment will remain single-threaded for the 0.2
  series, however connection inference bugs will be addressed in a future 0.2
  release.

* Connection Delegation does not support automatic tunnelling of SSH-dependent
  actions, such as the ``synchronize`` module. This will be addressed in the
  0.3 series.


Core Library
~~~~~~~~~~~~

* Synchronous connection establishment via OpenSSH, sudo, su, Docker, LXC and
  FreeBSD Jails, local subprocesses and :func:`os.fork`. Parallel connection
  setup is possible using multiple threads. Connections may be used from one or
  many threads after establishment.

* UNIX masters and children, with Linux, MacOS, FreeBSD, NetBSD, OpenBSD and
  Windows Subsystem for Linux explicitly supported.

* Automatic tests covering Python 2.6, 2.7 and 3.6 on Linux only.


**Known Issues**

* Serialization is still based on :mod:`pickle`. While there is high confidence
  remote code execution is impossible in Mitogen's configuration, an untrusted
  context may at least trigger disproportionately high memory usage injecting
  small messages (*"billion laughs attack"*). Replacement is an important
  future priority, but not critical for an initial release.

* Child processes are not reliably reaped, leading to a pileup of zombie
  processes when a program makes many short-lived connections in a single
  invocation. This does not impact Mitogen for Ansible, however it limits the
  usefulness of the core library. A future 0.2 release will address it.

* Some races remain around :class:`mitogen.core.Broker <Broker>` destruction,
  disconnection and corresponding file descriptor closure. These are only
  problematic in situations where child process reaping is also problematic.

* The `fakessh` component does not shut down correctly and requires flow
  control added to the design. While minimal fixes are possible, due to the
  absence of flow control the original design is functionally incomplete.

* The multi-threaded :ref:`service` remains in a state of design flux and
  should be considered obsolete, despite heavy use in Mitogen for Ansible. A
  future replacement may be integrated more tightly with, or entirely replace
  the RPC dispatcher on the main thread.

* Documentation is in a state of disrepair. This will be improved over the 0.2
  series.
