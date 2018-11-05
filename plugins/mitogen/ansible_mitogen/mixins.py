# Copyright 2017, David Wilson
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its contributors
# may be used to endorse or promote products derived from this software without
# specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

from __future__ import absolute_import
import logging
import os
import pwd
import shutil
import traceback

try:
    from shlex import quote as shlex_quote
except ImportError:
    from pipes import quote as shlex_quote

from ansible.module_utils._text import to_bytes
from ansible.parsing.utils.jsonify import jsonify

import ansible
import ansible.constants
import ansible.plugins
import ansible.plugins.action

import mitogen.core
import mitogen.select
import mitogen.utils

import ansible_mitogen.connection
import ansible_mitogen.planner
import ansible_mitogen.target
from ansible.module_utils._text import to_text


LOG = logging.getLogger(__name__)


class ActionModuleMixin(ansible.plugins.action.ActionBase):
    """
    The Mitogen-patched PluginLoader dynamically mixes this into every action
    class that Ansible attempts to load. It exists to override all the
    assumptions built into the base action class that should really belong in
    some middle layer, or at least in the connection layer.

    Functionality is defined here for:

    * Capturing the final set of task variables and giving Connection a chance
      to update its idea of the correct execution environment, before any
      attempt is made to call a Connection method. While it's not expected for
      the interpreter to change on a per-task basis, Ansible permits this, and
      so it must be supported.

    * Overriding lots of methods that try to call out to shell for mundane
      reasons, such as copying files around, changing file permissions,
      creating temporary directories and suchlike.

    * Short-circuiting any use of Ansiballz or related code for executing a
      module remotely using shell commands and SSH.

    * Short-circuiting most of the logic in dealing with the fact that Ansible
      always runs become: tasks across at least the SSH user account and the
      destination user account, and handling the security permission issues
      that crop up due to this. Mitogen always runs a task completely within
      the target user account, so it's not a problem for us.
    """
    def __init__(self, task, connection, *args, **kwargs):
        """
        Verify the received connection is really a Mitogen connection. If not,
        transmute this instance back into the original unadorned base class.

        This allows running the Mitogen strategy in mixed-target playbooks,
        where some targets use SSH while others use WinRM or some fancier UNIX
        connection plug-in. That's because when the Mitogen strategy is active,
        ActionModuleMixin is unconditionally mixed into any action module that
        is instantiated, and there is no direct way for the monkey-patch to
        know what kind of connection will be used upfront.
        """
        super(ActionModuleMixin, self).__init__(task, connection, *args, **kwargs)
        if not isinstance(connection, ansible_mitogen.connection.Connection):
            _, self.__class__ = type(self).__bases__

    def run(self, tmp=None, task_vars=None):
        """
        Override run() to notify Connection of task-specific data, so it has a
        chance to know e.g. the Python interpreter in use.
        """
        self._connection.on_action_run(
            task_vars=task_vars,
            delegate_to_hostname=self._task.delegate_to,
            loader_basedir=self._loader.get_basedir(),
        )
        return super(ActionModuleMixin, self).run(tmp, task_vars)

    COMMAND_RESULT = {
        'rc': 0,
        'stdout': '',
        'stdout_lines': [],
        'stderr': ''
    }

    def fake_shell(self, func, stdout=False):
        """
        Execute a function and decorate its return value in the style of
        _low_level_execute_command(). This produces a return value that looks
        like some shell command was run, when really func() was implemented
        entirely in Python.

        If the function raises :py:class:`mitogen.core.CallError`, this will be
        translated into a failed shell command with a non-zero exit status.

        :param func:
            Function invoked as `func()`.
        :returns:
            See :py:attr:`COMMAND_RESULT`.
        """
        dct = self.COMMAND_RESULT.copy()
        try:
            rc = func()
            if stdout:
                dct['stdout'] = repr(rc)
        except mitogen.core.CallError:
            LOG.exception('While emulating a shell command')
            dct['rc'] = 1
            dct['stderr'] = traceback.format_exc()

        return dct

    def _remote_file_exists(self, path):
        """
        Determine if `path` exists by directly invoking os.path.exists() in the
        target user account.
        """
        LOG.debug('_remote_file_exists(%r)', path)
        return self._connection.get_chain().call(
            os.path.exists,
            mitogen.utils.cast(path)
        )

    def _configure_module(self, module_name, module_args, task_vars=None):
        """
        Mitogen does not use the Ansiballz framework. This call should never
        happen when ActionMixin is active, so crash if it does.
        """
        assert False, "_configure_module() should never be called."

    def _is_pipelining_enabled(self, module_style, wrap_async=False):
        """
        Mitogen does not use SSH pipelining. This call should never happen when
        ActionMixin is active, so crash if it does.
        """
        assert False, "_is_pipelining_enabled() should never be called."

    def _make_tmp_path(self, remote_user=None):
        """
        Return the directory created by the Connection instance during
        connection.
        """
        LOG.debug('_make_tmp_path(remote_user=%r)', remote_user)
        return self._connection._make_tmp_path()

    def _remove_tmp_path(self, tmp_path):
        """
        Stub out the base implementation's invocation of rm -rf, replacing it
        with nothing, as the persistent interpreter automatically cleans up
        after itself without introducing roundtrips.
        """
        # The actual removal is pipelined by Connection.close().
        LOG.debug('_remove_tmp_path(%r)', tmp_path)
        # Upstream _remove_tmp_path resets shell.tmpdir here, however
        # connection.py uses that as the sole location of the temporary
        # directory, if one exists.
        # self._connection._shell.tmpdir = None

    def _transfer_data(self, remote_path, data):
        """
        Used by the base _execute_module(), and in <2.4 also by the template
        action module, and probably others.
        """
        if isinstance(data, dict):
            data = jsonify(data)
        if not isinstance(data, bytes):
            data = to_bytes(data, errors='surrogate_or_strict')

        LOG.debug('_transfer_data(%r, %s ..%d bytes)',
                  remote_path, type(data), len(data))
        self._connection.put_data(remote_path, data)
        return remote_path

    #: Actions listed here cause :func:`_fixup_perms2` to avoid a needless
    #: roundtrip, as they modify file modes separately afterwards. This is due
    #: to the method prototype having a default of `execute=True`.
    FIXUP_PERMS_RED_HERRING = set(['copy'])

    def _fixup_perms2(self, remote_paths, remote_user=None, execute=True):
        """
        Mitogen always executes ActionBase helper methods in the context of the
        target user account, so it is never necessary to modify permissions
        except to ensure the execute bit is set if requested.
        """
        LOG.debug('_fixup_perms2(%r, remote_user=%r, execute=%r)',
                  remote_paths, remote_user, execute)
        if execute and self._load_name not in self.FIXUP_PERMS_RED_HERRING:
            return self._remote_chmod(remote_paths, mode='u+x')
        return self.COMMAND_RESULT.copy()

    def _remote_chmod(self, paths, mode, sudoable=False):
        """
        Issue an asynchronous set_file_mode() call for every path in `paths`,
        then format the resulting return value list with fake_shell().
        """
        LOG.debug('_remote_chmod(%r, mode=%r, sudoable=%r)',
                  paths, mode, sudoable)
        return self.fake_shell(lambda: mitogen.select.Select.all(
            self._connection.get_chain().call_async(
                ansible_mitogen.target.set_file_mode, path, mode
            )
            for path in paths
        ))

    def _remote_chown(self, paths, user, sudoable=False):
        """
        Issue an asynchronous os.chown() call for every path in `paths`, then
        format the resulting return value list with fake_shell().
        """
        LOG.debug('_remote_chown(%r, user=%r, sudoable=%r)',
                  paths, user, sudoable)
        ent = self._connection.get_chain().call(pwd.getpwnam, user)
        return self.fake_shell(lambda: mitogen.select.Select.all(
            self._connection.get_chain().call_async(
                os.chown, path, ent.pw_uid, ent.pw_gid
            )
            for path in paths
        ))

    def _remote_expand_user(self, path, sudoable=True):
        """
        Replace the base implementation's attempt to emulate
        os.path.expanduser() with an actual call to os.path.expanduser().

        :param bool sudoable:
            If :data:`True`, indicate unqualified tilde ("~" with no username)
            should be evaluated in the context of the login account, not any
            become_user.
        """
        LOG.debug('_remote_expand_user(%r, sudoable=%r)', path, sudoable)
        if not path.startswith('~'):
            # /home/foo -> /home/foo
            return path
        if sudoable or not self._play_context.become:
            if path == '~':
                # ~ -> /home/dmw
                return self._connection.homedir
            if path.startswith('~/'):
                # ~/.ansible -> /home/dmw/.ansible
                return os.path.join(self._connection.homedir, path[2:])
        # ~root/.ansible -> /root/.ansible
        return self._connection.get_chain(use_login=(not sudoable)).call(
            os.path.expanduser,
            mitogen.utils.cast(path),
        )

    def get_task_timeout_secs(self):
        """
        Return the task "async:" value, portable across 2.4-2.5.
        """
        try:
            return self._task.async_val
        except AttributeError:
            return getattr(self._task, 'async')

    def _temp_file_gibberish(self, module_args, wrap_async):
        # Ansible>2.5 module_utils reuses the action's temporary directory if
        # one exists. Older versions error if this key is present.
        if ansible.__version__ > '2.5':
            if wrap_async:
                # Sharing is not possible with async tasks, as in that case,
                # the directory must outlive the action plug-in.
                module_args['_ansible_tmpdir'] = None
            else:
                module_args['_ansible_tmpdir'] = self._connection._shell.tmpdir

        # If _ansible_tmpdir is unset, Ansible>2.6 module_utils will use
        # _ansible_remote_tmp as the location to create the module's temporary
        # directory. Older versions error if this key is present.
        if ansible.__version__ > '2.6':
            module_args['_ansible_remote_tmp'] = (
                self._connection.get_good_temp_dir()
            )

    def _execute_module(self, module_name=None, module_args=None, tmp=None,
                        task_vars=None, persist_files=False,
                        delete_remote_tmp=True, wrap_async=False):
        """
        Collect up a module's execution environment then use it to invoke
        target.run_module() or helpers.run_module_async() in the target
        context.
        """
        if module_name is None:
            module_name = self._task.action
        if module_args is None:
            module_args = self._task.args
        if task_vars is None:
            task_vars = {}

        self._update_module_args(module_name, module_args, task_vars)
        env = {}
        self._compute_environment_string(env)
        self._temp_file_gibberish(module_args, wrap_async)

        self._connection._connect()
        return ansible_mitogen.planner.invoke(
            ansible_mitogen.planner.Invocation(
                action=self,
                connection=self._connection,
                module_name=mitogen.core.to_text(module_name),
                module_args=mitogen.utils.cast(module_args),
                task_vars=task_vars,
                templar=self._templar,
                env=mitogen.utils.cast(env),
                wrap_async=wrap_async,
                timeout_secs=self.get_task_timeout_secs(),
            )
        )

    def _postprocess_response(self, result):
        """
        Apply fixups mimicking ActionBase._execute_module(); this is copied
        verbatim from action/__init__.py, the guts of _parse_returned_data are
        garbage and should be removed or reimplemented once tests exist.

        :param dict result:
            Dictionary with format::

                {
                    "rc": int,
                    "stdout": "stdout data",
                    "stderr": "stderr data"
                }
        """
        data = self._parse_returned_data(result)

        # Cutpasted from the base implementation.
        if 'stdout' in data and 'stdout_lines' not in data:
            data['stdout_lines'] = (data['stdout'] or u'').splitlines()
        if 'stderr' in data and 'stderr_lines' not in data:
            data['stderr_lines'] = (data['stderr'] or u'').splitlines()

        return data

    def _low_level_execute_command(self, cmd, sudoable=True, in_data=None,
                                   executable=None,
                                   encoding_errors='surrogate_then_replace',
                                   chdir=None):
        """
        Override the base implementation by simply calling
        target.exec_command() in the target context.
        """
        LOG.debug('_low_level_execute_command(%r, in_data=%r, exe=%r, dir=%r)',
                  cmd, type(in_data), executable, chdir)
        if executable is None:  # executable defaults to False
            executable = self._play_context.executable
        if executable:
            cmd = executable + ' -c ' + shlex_quote(cmd)

        rc, stdout, stderr = self._connection.exec_command(
            cmd=cmd,
            in_data=in_data,
            sudoable=sudoable,
            mitogen_chdir=chdir,
        )
        stdout_text = to_text(stdout, errors=encoding_errors)

        return {
            'rc': rc,
            'stdout': stdout_text,
            'stdout_lines': stdout_text.splitlines(),
            'stderr': stderr,
        }
