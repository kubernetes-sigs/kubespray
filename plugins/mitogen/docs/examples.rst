
Examples
========


Fixing Bugs By Replacing Shell
------------------------------

Have you ever encountered shell like this? It arranges to conditionally execute
an ``if`` statement as root on a file server behind a bastion host:

.. code-block:: bash

    ssh bastion "
        if [ \"$PROD\" ];
        then
            ssh fileserver sudo su -c \"
                if grep -qs /dev/sdb1 /proc/mounts;
                then
                    echo \\\"sdb1 already mounted!\\\";
                    umount /dev/sdb1
                fi;
                rm -rf \\\"/media/Main Backup Volume\\\"/*;
                mount /dev/sdb1 \\\"/media/Main Backup Volume\\\"
            \";
        fi;
        sudo touch /var/run/start_backup;
    "

Chances are high this is familiar territory, we've all seen it, and those
working in infrastructure have almost certainly written it. At first glance,
ignoring that annoying quoting, it looks perfectly fine: well structured,
neatly indented, and the purpose of the snippet seems clear.

1. At first glance, is ``"/media/Main Backup Volume"`` quoted correctly?
2. How will the ``if`` statement behave if there is a problem with the machine,
   and, say, the ``/bin/grep`` binary is absent?
3. Ignoring quoting, are there any other syntax problems?
4. If this snippet is pasted from its original script into an interactive
   shell, will it behave the same as before?
5. Can you think offhand of differences in how the arguments to ``sudo
   ...`` and ``ssh fileserver ...`` are parsed?
6. In which context will the ``*`` glob be expanded, if it is expanded at all?
7. What will the exit status of ``ssh bastion`` be if ``ssh fileserver`` fails?


Innocent But Deadly
~~~~~~~~~~~~~~~~~~~

1. The quoting used is nonsense! At best, ``mount`` will receive 3 arguments.
   At worst, the snippet will not parse at all.
2. The ``if`` statement will treat a missing ``grep`` binary (exit status 127)
   the same as if ``/dev/sdb1`` was not mounted at all (exit status 1). Unless
   the program executing this script is parsing ``stderr`` output, the failure
   won't be noticed. Consequently, since the volume was still mounted when
   ``rm`` was executed, it got wiped.
3. There is at least one more syntax error present: a semicolon missing after
   the ``umount`` command.
4. If you paste the snippet into an interactive shell, the apparently quoted
   "!" character in the ``echo`` command will be interpreted as a history
   expansion.
5. ``sudo`` preserves the remainder of the argument vector as-is, while
   ``ssh`` **concatenates** each part into a single string that is passed to
   the login shell. While quotes appearing within arguments are preserved by
   ``sudo``, without additional effort, pairs of quotes are effectively
   stripped by ``ssh``.
6. As for where the glob is expanded, the answer is I have absolutely no idea
   without running the code, which might wipe out the backups!
7. If the ``ssh fileserver`` command fails, the exit status of ``ssh bastion``
   will continue to indicate success.
8. Depending in which environment the ``PROD`` variable is set, either it will
   always evaluate to false, because it was set by the bastion host, or it
   will do the right thing, because it was set by the script host.

Golly, we've managed to hit at least 8 potentially mission-critical gotchas in
only 14 lines of code, and they are just those I can count! Welcome to the
reality of "programming" in shell.

In the end, superficial legibility counted for nothing, it's 4AM, you've been
paged, the network is down and your boss is angry.


Shell Quoting Madness
~~~~~~~~~~~~~~~~~~~~~

Let's assume on first approach that we really want to handle those quoting
issues. I wrote a little Python script based around the :py:func:`shlex.quote`
function to construct, to the best of my knowledge, the quoting required for
each stage:

.. code-block:: bash

    ssh bastion '
        if [ "$PROD" ];
        then
            ssh fileserver sudo su -c '"'"'
                if grep -qs /dev/sdb1 /proc/mounts;
                then
                    echo "sdb1 already mounted!";
                    umount /dev/sdb1
                fi;
                rm -rf "/media/Main Backup Volume"/*;
                mount /dev/sdb1 "/media/Main Backup Volume"
            '"'"';
        fi;
        sudo touch /var/run/start_backup
    '

Even with Python handling the heavy lifting of quoting each shell layer, and
even if the aforementioned minor disk-wiping issue was fixed, it is still not
100% clear that argument handling rules for all of ``su``, ``sudo``, ``ssh``,
and ``bash`` are correctly respected.

Finally, if any login shell involved is not ``bash``, we must introduce
additional quoting in order to explicitly invoke ``bash`` at each stage,
causing an explosion in quoting:

.. code-block:: bash

    ssh bastion 'bash -c '"'"'if [ "$PROD" ]; then ssh fileserver bash -c '"'"'
    "'"'"'"'"'"'sudo su -c '"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"
    'bash -c '"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"
    '"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'
    "'"'"'"'"'"'"'"'"'"'if grep -qs /dev/sdb1 /proc/mounts; then echo "sdb1 alr
    eady mounted!"; umount /dev/sdb1 fi; rm -rf "/media/Main Backup Volume"/*;
    mount /dev/sdb1 "/media/Main Backup Volume"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"
    '"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'
    "'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"''"'"'"'"'"'"'"'"'"'"'
    "'"'"'"'"'"'"'"'"'"'"'"'"'"'"'"''"'"'"'"'"'"'"'"'; fi; sudo touch /var/run/
    start_backup'"'"''


There Is Hope
~~~~~~~~~~~~~

We could instead express the above using Mitogen:

::

    def run(*args):
        return subprocess.check_call(args)

    def file_contains(s, path):
        with open(path, 'rb') as fp:
            return s in fp.read()

    device = '/dev/sdb1'
    mount_point = '/media/Media Volume'

    bastion = router.ssh(hostname='bastion')
    bastion_sudo = router.sudo(via=bastion)

    if PROD:
        fileserver = router.ssh(hostname='fileserver', via=bastion)
        if fileserver.call(file_contains, device, '/proc/mounts'):
            print('{} already mounted!'.format(device))
            fileserver.call(run, 'umount', device)
        fileserver.call(shutil.rmtree, mount_point)
        fileserver.call(os.mkdir, mount_point, 0777)
        fileserver.call(run, 'mount', device, mount_point)

    bastion_sudo.call(run, 'touch', '/var/run/start_backup')

* In which context must the ``PROD`` variable be defined?
* On which machine is each step executed?
* Are there any escaping issues?
* What will happen if the ``grep`` binary is missing?
* What will happen if any step fails?
* What will happen if any login shell is not ``bash``?


Recursively Nested Bootstrap
----------------------------

This demonstrates the library's ability to use slave contexts to recursively
proxy connections to additional slave contexts, with a uniform API to any
slave, and all features (function calls, import forwarding, stdio forwarding,
log forwarding) functioning transparently.

This example uses a chain of local contexts for clarity, however SSH and sudo
contexts work identically.

nested.py:

.. code-block:: python

    import os
    import mitogen.utils

    @mitogen.utils.run_with_router
    def main(router):
        mitogen.utils.log_to_file()

        context = None
        for x in range(1, 11):
            print('Connect local%d via %s' % (x, context))
            context = router.local(via=context, name='local%d' % x)

        context.call(os.system, 'pstree -s python -s mitogen')


Output:

.. code-block:: shell

    $ python nested.py
    Connect local1 via None
    Connect local2 via Context(1, 'local1')
    Connect local3 via Context(2, 'local2')
    Connect local4 via Context(3, 'local3')
    Connect local5 via Context(4, 'local4')
    Connect local6 via Context(5, 'local5')
    Connect local7 via Context(6, 'local6')
    Connect local8 via Context(7, 'local7')
    Connect local9 via Context(8, 'local8')
    Connect local10 via Context(9, 'local9')
    18:14:07 I ctx.local10: stdout: -+= 00001 root /sbin/launchd
    18:14:07 I ctx.local10: stdout:  \-+= 08126 dmw /Applications/iTerm.app/Contents/MacOS/iTerm2
    18:14:07 I ctx.local10: stdout:    \-+= 10638 dmw /Applications/iTerm.app/Contents/MacOS/iTerm2 --server bash --login
    18:14:07 I ctx.local10: stdout:      \-+= 10639 dmw bash --login
    18:14:07 I ctx.local10: stdout:        \-+= 13632 dmw python nested.py
    18:14:07 I ctx.local10: stdout:          \-+- 13633 dmw mitogen:dmw@Eldil.local:13632
    18:14:07 I ctx.local10: stdout:            \-+- 13635 dmw mitogen:dmw@Eldil.local:13633
    18:14:07 I ctx.local10: stdout:              \-+- 13637 dmw mitogen:dmw@Eldil.local:13635
    18:14:07 I ctx.local10: stdout:                \-+- 13639 dmw mitogen:dmw@Eldil.local:13637
    18:14:07 I ctx.local10: stdout:                  \-+- 13641 dmw mitogen:dmw@Eldil.local:13639
    18:14:07 I ctx.local10: stdout:                    \-+- 13643 dmw mitogen:dmw@Eldil.local:13641
    18:14:07 I ctx.local10: stdout:                      \-+- 13645 dmw mitogen:dmw@Eldil.local:13643
    18:14:07 I ctx.local10: stdout:                        \-+- 13647 dmw mitogen:dmw@Eldil.local:13645
    18:14:07 I ctx.local10: stdout:                          \-+- 13649 dmw mitogen:dmw@Eldil.local:13647
    18:14:07 I ctx.local10: stdout:                            \-+- 13651 dmw mitogen:dmw@Eldil.local:13649
    18:14:07 I ctx.local10: stdout:                              \-+- 13653 dmw pstree -s python -s mitogen
    18:14:07 I ctx.local10: stdout:                                \--- 13654 root ps -axwwo user,pid,ppid,pgid,command
