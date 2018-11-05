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
from __future__ import unicode_literals

import logging
import os
import random
import stat
import time

import jinja2.runtime
import ansible.constants as C
import ansible.errors
import ansible.plugins.connection
import ansible.utils.shlex

import mitogen.unix
import mitogen.utils

import ansible_mitogen.parsing
import ansible_mitogen.process
import ansible_mitogen.services
import ansible_mitogen.target


LOG = logging.getLogger(__name__)


def optional_secret(value):
    """
    Wrap `value` in :class:`mitogen.core.Secret` if it is not :data:`None`,
    otherwise return :data:`None`.
    """
    if value is not None:
        return mitogen.core.Secret(value)


def parse_python_path(s):
    """
    Given the string set for ansible_python_interpeter, parse it using shell
    syntax and return an appropriate argument vector.
    """
    if s:
        return ansible.utils.shlex.shlex_split(s)


def _connect_local(spec):
    """
    Return ContextService arguments for a local connection.
    """
    return {
        'method': 'local',
        'kwargs': {
            'python_path': spec['python_path'],
        }
    }


def _connect_ssh(spec):
    """
    Return ContextService arguments for an SSH connection.
    """
    if C.HOST_KEY_CHECKING:
        check_host_keys = 'enforce'
    else:
        check_host_keys = 'ignore'

    # #334: tilde-expand private_key_file to avoid implementation difference
    # between Python and OpenSSH.
    private_key_file = spec['private_key_file']
    if private_key_file is not None:
        private_key_file = os.path.expanduser(private_key_file)

    return {
        'method': 'ssh',
        'kwargs': {
            'check_host_keys': check_host_keys,
            'hostname': spec['remote_addr'],
            'username': spec['remote_user'],
            'password': optional_secret(spec['password']),
            'port': spec['port'],
            'python_path': spec['python_path'],
            'identity_file': private_key_file,
            'identities_only': False,
            'ssh_path': spec['ssh_executable'],
            'connect_timeout': spec['ansible_ssh_timeout'],
            'ssh_args': spec['ssh_args'],
            'ssh_debug_level': spec['mitogen_ssh_debug_level'],
        }
    }


def _connect_docker(spec):
    """
    Return ContextService arguments for a Docker connection.
    """
    return {
        'method': 'docker',
        'kwargs': {
            'username': spec['remote_user'],
            'container': spec['remote_addr'],
            'python_path': spec['python_path'],
            'connect_timeout': spec['ansible_ssh_timeout'] or spec['timeout'],
        }
    }


def _connect_kubectl(spec):
    """
    Return ContextService arguments for a Kubernetes connection.
    """
    return {
        'method': 'kubectl',
        'kwargs': {
            'pod': spec['remote_addr'],
            'python_path': spec['python_path'],
            'connect_timeout': spec['ansible_ssh_timeout'] or spec['timeout'],
            'kubectl_args': spec['extra_args'],
        }
    }


def _connect_jail(spec):
    """
    Return ContextService arguments for a FreeBSD jail connection.
    """
    return {
        'method': 'jail',
        'kwargs': {
            'username': spec['remote_user'],
            'container': spec['remote_addr'],
            'python_path': spec['python_path'],
            'connect_timeout': spec['ansible_ssh_timeout'] or spec['timeout'],
        }
    }


def _connect_lxc(spec):
    """
    Return ContextService arguments for an LXC Classic container connection.
    """
    return {
        'method': 'lxc',
        'kwargs': {
            'container': spec['remote_addr'],
            'python_path': spec['python_path'],
            'connect_timeout': spec['ansible_ssh_timeout'] or spec['timeout'],
        }
    }


def _connect_lxd(spec):
    """
    Return ContextService arguments for an LXD container connection.
    """
    return {
        'method': 'lxd',
        'kwargs': {
            'container': spec['remote_addr'],
            'python_path': spec['python_path'],
            'connect_timeout': spec['ansible_ssh_timeout'] or spec['timeout'],
        }
    }


def _connect_machinectl(spec):
    """
    Return ContextService arguments for a machinectl connection.
    """
    return _connect_setns(dict(spec, mitogen_kind='machinectl'))


def _connect_setns(spec):
    """
    Return ContextService arguments for a mitogen_setns connection.
    """
    return {
        'method': 'setns',
        'kwargs': {
            'container': spec['remote_addr'],
            'username': spec['remote_user'],
            'python_path': spec['python_path'],
            'kind': spec['mitogen_kind'],
            'docker_path': spec['mitogen_docker_path'],
            'kubectl_path': spec['mitogen_kubectl_path'],
            'lxc_info_path': spec['mitogen_lxc_info_path'],
            'machinectl_path': spec['mitogen_machinectl_path'],
        }
    }


def _connect_su(spec):
    """
    Return ContextService arguments for su as a become method.
    """
    return {
        'method': 'su',
        'enable_lru': True,
        'kwargs': {
            'username': spec['become_user'],
            'password': optional_secret(spec['become_pass']),
            'python_path': spec['python_path'],
            'su_path': spec['become_exe'],
            'connect_timeout': spec['timeout'],
        }
    }


def _connect_sudo(spec):
    """
    Return ContextService arguments for sudo as a become method.
    """
    return {
        'method': 'sudo',
        'enable_lru': True,
        'kwargs': {
            'username': spec['become_user'],
            'password': optional_secret(spec['become_pass']),
            'python_path': spec['python_path'],
            'sudo_path': spec['become_exe'],
            'connect_timeout': spec['timeout'],
            'sudo_args': spec['sudo_args'],
        }
    }


def _connect_doas(spec):
    """
    Return ContextService arguments for doas as a become method.
    """
    return {
        'method': 'doas',
        'enable_lru': True,
        'kwargs': {
            'username': spec['become_user'],
            'password': optional_secret(spec['become_pass']),
            'python_path': spec['python_path'],
            'doas_path': spec['become_exe'],
            'connect_timeout': spec['timeout'],
        }
    }


def _connect_mitogen_su(spec):
    """
    Return ContextService arguments for su as a first class connection.
    """
    return {
        'method': 'su',
        'kwargs': {
            'username': spec['remote_user'],
            'password': optional_secret(spec['password']),
            'python_path': spec['python_path'],
            'su_path': spec['become_exe'],
            'connect_timeout': spec['timeout'],
        }
    }


def _connect_mitogen_sudo(spec):
    """
    Return ContextService arguments for sudo as a first class connection.
    """
    return {
        'method': 'sudo',
        'kwargs': {
            'username': spec['remote_user'],
            'password': optional_secret(spec['password']),
            'python_path': spec['python_path'],
            'sudo_path': spec['become_exe'],
            'connect_timeout': spec['timeout'],
            'sudo_args': spec['sudo_args'],
        }
    }


def _connect_mitogen_doas(spec):
    """
    Return ContextService arguments for doas as a first class connection.
    """
    return {
        'method': 'doas',
        'kwargs': {
            'username': spec['remote_user'],
            'password': optional_secret(spec['password']),
            'python_path': spec['python_path'],
            'doas_path': spec['become_exe'],
            'connect_timeout': spec['timeout'],
        }
    }


#: Mapping of connection method names to functions invoked as `func(spec)`
#: generating ContextService keyword arguments matching a connection
#: specification.
CONNECTION_METHOD = {
    'docker': _connect_docker,
    'kubectl': _connect_kubectl,
    'jail': _connect_jail,
    'local': _connect_local,
    'lxc': _connect_lxc,
    'lxd': _connect_lxd,
    'machinectl': _connect_machinectl,
    'setns': _connect_setns,
    'ssh': _connect_ssh,
    'su': _connect_su,
    'sudo': _connect_sudo,
    'doas': _connect_doas,
    'mitogen_su': _connect_mitogen_su,
    'mitogen_sudo': _connect_mitogen_sudo,
    'mitogen_doas': _connect_mitogen_doas,
}


def config_from_play_context(transport, inventory_name, connection):
    """
    Return a dict representing all important connection configuration, allowing
    the same functions to work regardless of whether configuration came from
    play_context (direct connection) or host vars (mitogen_via=).
    """
    return {
        'transport': transport,
        'inventory_name': inventory_name,
        'remote_addr': connection._play_context.remote_addr,
        'remote_user': connection._play_context.remote_user,
        'become': connection._play_context.become,
        'become_method': connection._play_context.become_method,
        'become_user': connection._play_context.become_user,
        'become_pass': connection._play_context.become_pass,
        'password': connection._play_context.password,
        'port': connection._play_context.port,
        'python_path': parse_python_path(
            connection.get_task_var('ansible_python_interpreter',
                                    default='/usr/bin/python')
        ),
        'private_key_file': connection._play_context.private_key_file,
        'ssh_executable': connection._play_context.ssh_executable,
        'timeout': connection._play_context.timeout,
        'ansible_ssh_timeout':
            connection.get_task_var('ansible_ssh_timeout',
                                    default=C.DEFAULT_TIMEOUT),
        'ssh_args': [
            mitogen.core.to_text(term)
            for s in (
                getattr(connection._play_context, 'ssh_args', ''),
                getattr(connection._play_context, 'ssh_common_args', ''),
                getattr(connection._play_context, 'ssh_extra_args', '')
            )
            for term in ansible.utils.shlex.shlex_split(s or '')
        ],
        'become_exe': connection._play_context.become_exe,
        'sudo_args': [
            mitogen.core.to_text(term)
            for s in (
                connection._play_context.sudo_flags,
                connection._play_context.become_flags
            )
            for term in ansible.utils.shlex.shlex_split(s or '')
        ],
        'mitogen_via':
            connection.get_task_var('mitogen_via'),
        'mitogen_kind':
            connection.get_task_var('mitogen_kind'),
        'mitogen_docker_path':
            connection.get_task_var('mitogen_docker_path'),
        'mitogen_kubectl_path':
            connection.get_task_var('mitogen_kubectl_path'),
        'mitogen_lxc_info_path':
            connection.get_task_var('mitogen_lxc_info_path'),
        'mitogen_machinectl_path':
            connection.get_task_var('mitogen_machinectl_path'),
        'mitogen_ssh_debug_level':
            connection.get_task_var('mitogen_ssh_debug_level'),
        'extra_args':
            connection.get_extra_args(),
    }


def config_from_hostvars(transport, inventory_name, connection,
                         hostvars, become_user):
    """
    Override config_from_play_context() to take equivalent information from
    host vars.
    """
    config = config_from_play_context(transport, inventory_name, connection)
    hostvars = dict(hostvars)
    return dict(config, **{
        'remote_addr': hostvars.get('ansible_host', inventory_name),
        'become': bool(become_user),
        'become_user': become_user,
        'become_pass': None,
        'remote_user': hostvars.get('ansible_user'),  # TODO
        'password': (hostvars.get('ansible_ssh_pass') or
                     hostvars.get('ansible_password')),
        'port': hostvars.get('ansible_port'),
        'python_path': parse_python_path(hostvars.get('ansible_python_interpreter')),
        'private_key_file': (hostvars.get('ansible_ssh_private_key_file') or
                             hostvars.get('ansible_private_key_file')),
        'mitogen_via': hostvars.get('mitogen_via'),
        'mitogen_kind': hostvars.get('mitogen_kind'),
        'mitogen_docker_path': hostvars.get('mitogen_docker_path'),
        'mitogen_kubectl_path': hostvars.get('mitogen_kubectl_path'),
        'mitogen_lxc_info_path': hostvars.get('mitogen_lxc_info_path'),
        'mitogen_machinectl_path': hostvars.get('mitogen_machinctl_path'),
    })


class CallChain(mitogen.parent.CallChain):
    """
    Extend :class:`mitogen.parent.CallChain` to additionally cause the
    associated :class:`Connection` to be reset if a ChannelError occurs.

    This only catches failures that occur while a call is pnding, it is a
    stop-gap until a more general method is available to notice connection in
    every situation.
    """
    call_aborted_msg = (
        'Mitogen was disconnected from the remote environment while a call '
        'was in-progress. If you feel this is in error, please file a bug. '
        'Original error was: %s'
    )

    def __init__(self, connection, context, pipelined=False):
        super(CallChain, self).__init__(context, pipelined)
        #: The connection to reset on CallError.
        self._connection = connection

    def _rethrow(self, recv):
        try:
            return recv.get().unpickle()
        except mitogen.core.ChannelError as e:
            self._connection.reset()
            raise ansible.errors.AnsibleConnectionFailure(
                self.call_aborted_msg % (e,)
            )

    def call(self, func, *args, **kwargs):
        """
        Like :meth:`mitogen.parent.CallChain.call`, but log timings.
        """
        t0 = time.time()
        try:
            recv = self.call_async(func, *args, **kwargs)
            return self._rethrow(recv)
        finally:
            LOG.debug('Call took %d ms: %r', 1000 * (time.time() - t0),
                      mitogen.parent.CallSpec(func, args, kwargs))


class Connection(ansible.plugins.connection.ConnectionBase):
    #: mitogen.master.Broker for this worker.
    broker = None

    #: mitogen.master.Router for this worker.
    router = None

    #: mitogen.parent.Context representing the parent Context, which is
    #: presently always the connection multiplexer process.
    parent = None

    #: mitogen.parent.Context for the target account on the target, possibly
    #: reached via become.
    context = None

    #: Context for the login account on the target. This is always the login
    #: account, even when become=True.
    login_context = None

    #: Only sudo, su, and doas are supported for now.
    become_methods = ['sudo', 'su', 'doas']

    #: Dict containing init_child() return value as recorded at startup by
    #: ContextService. Contains:
    #:
    #:  fork_context:   Context connected to the fork parent : process in the
    #:                  target account.
    #:  home_dir:       Target context's home directory.
    #:  good_temp_dir:  A writeable directory where new temporary directories
    #:                  can be created.
    init_child_result = None

    #: A :class:`mitogen.parent.CallChain` for calls made to the target
    #: account, to ensure subsequent calls fail with the original exception if
    #: pipelined directory creation or file transfer fails.
    chain = None

    #
    # Note: any of the attributes below may be :data:`None` if the connection
    # plugin was constructed directly by a non-cooperative action, such as in
    # the case of the synchronize module.
    #

    #: Set to the host name as it appears in inventory by on_action_run().
    inventory_hostname = None

    #: Set to task_vars by on_action_run().
    _task_vars = None

    #: Set to 'hostvars' by on_action_run()
    host_vars = None

    #: Set by on_action_run()
    delegate_to_hostname = None

    #: Set to '_loader.get_basedir()' by on_action_run(). Used by mitogen_local
    #: to change the working directory to that of the current playbook,
    #: matching vanilla Ansible behaviour.
    loader_basedir = None

    def __init__(self, play_context, new_stdin, **kwargs):
        assert ansible_mitogen.process.MuxProcess.unix_listener_path, (
            'Mitogen connection types may only be instantiated '
            'while the "mitogen" strategy is active.'
        )
        super(Connection, self).__init__(play_context, new_stdin)

    def __del__(self):
        """
        Ansible cannot be trusted to always call close() e.g. the synchronize
        action constructs a local connection like this. So provide a destructor
        in the hopes of catching these cases.
        """
        # https://github.com/dw/mitogen/issues/140
        self.close()

    def on_action_run(self, task_vars, delegate_to_hostname, loader_basedir):
        """
        Invoked by ActionModuleMixin to indicate a new task is about to start
        executing. We use the opportunity to grab relevant bits from the
        task-specific data.

        :param dict task_vars:
            Task variable dictionary.
        :param str delegate_to_hostname:
            :data:`None`, or the template-expanded inventory hostname this task
            is being delegated to. A similar variable exists on PlayContext
            when ``delegate_to:`` is active, however it is unexpanded.
        :param str loader_basedir:
            Loader base directory; see :attr:`loader_basedir`.
        """
        self.inventory_hostname = task_vars['inventory_hostname']
        self._task_vars = task_vars
        self.host_vars = task_vars['hostvars']
        self.delegate_to_hostname = delegate_to_hostname
        self.loader_basedir = loader_basedir
        self._reset(mode='put')

    def get_task_var(self, key, default=None):
        if self._task_vars and key in self._task_vars:
            return self._task_vars[key]
        return default

    @property
    def homedir(self):
        self._connect()
        return self.init_child_result['home_dir']

    @property
    def connected(self):
        return self.context is not None

    def _config_from_via(self, via_spec):
        """
        Produce a dict connection specifiction given a string `via_spec`, of
        the form `[become_user@]inventory_hostname`.
        """
        become_user, _, inventory_name = via_spec.rpartition('@')
        via_vars = self.host_vars[inventory_name]
        if isinstance(via_vars, jinja2.runtime.Undefined):
            raise ansible.errors.AnsibleConnectionFailure(
                self.unknown_via_msg % (
                    via_spec,
                    inventory_name,
                )
            )

        return config_from_hostvars(
            transport=via_vars.get('ansible_connection', 'ssh'),
            inventory_name=inventory_name,
            connection=self,
            hostvars=via_vars,
            become_user=become_user or None,
        )

    unknown_via_msg = 'mitogen_via=%s of %s specifies an unknown hostname'
    via_cycle_msg = 'mitogen_via=%s of %s creates a cycle (%s)'

    def _stack_from_config(self, config, stack=(), seen_names=()):
        if config['inventory_name'] in seen_names:
            raise ansible.errors.AnsibleConnectionFailure(
                self.via_cycle_msg % (
                    config['mitogen_via'],
                    config['inventory_name'],
                    ' -> '.join(reversed(
                        seen_names + (config['inventory_name'],)
                    )),
                )
            )

        if config['mitogen_via']:
            stack, seen_names = self._stack_from_config(
                self._config_from_via(config['mitogen_via']),
                stack=stack,
                seen_names=seen_names + (config['inventory_name'],)
            )

        stack += (CONNECTION_METHOD[config['transport']](config),)
        if config['become']:
            stack += (CONNECTION_METHOD[config['become_method']](config),)

        return stack, seen_names

    def _connect_broker(self):
        """
        Establish a reference to the Broker, Router and parent context used for
        connections.
        """
        if not self.broker:
            self.broker = mitogen.master.Broker()
            self.router, self.parent = mitogen.unix.connect(
                path=ansible_mitogen.process.MuxProcess.unix_listener_path,
                broker=self.broker,
            )

    def _config_from_direct_connection(self):
        """
        """
        return config_from_play_context(
            transport=self.transport,
            inventory_name=self.inventory_hostname,
            connection=self
        )

    def _config_from_delegate_to(self):
        return config_from_hostvars(
            transport=self._play_context.connection,
            inventory_name=self.delegate_to_hostname,
            connection=self,
            hostvars=self.host_vars[self.delegate_to_hostname],
            become_user=(self._play_context.become_user
                         if self._play_context.become
                         else None),
        )

    def _build_stack(self):
        """
        Construct a list of dictionaries representing the connection
        configuration between the controller and the target. This is
        additionally used by the integration tests "mitogen_get_stack" action
        to fetch the would-be connection configuration.
        """
        if self.delegate_to_hostname is not None:
            target_config = self._config_from_delegate_to()
        else:
            target_config = self._config_from_direct_connection()

        stack, _ = self._stack_from_config(target_config)
        return stack

    def _connect_stack(self, stack):
        """
        Pass `stack` to ContextService, requesting a copy of the context object
        representing the target. If no connection exists yet, ContextService
        will establish it before returning it or throwing an error.
        """
        dct = self.parent.call_service(
            service_name='ansible_mitogen.services.ContextService',
            method_name='get',
            stack=mitogen.utils.cast(list(stack)),
        )

        if dct['msg']:
            if dct['method_name'] in self.become_methods:
                raise ansible.errors.AnsibleModuleError(dct['msg'])
            raise ansible.errors.AnsibleConnectionFailure(dct['msg'])

        self.context = dct['context']
        self.chain = CallChain(self, self.context, pipelined=True)
        if self._play_context.become:
            self.login_context = dct['via']
        else:
            self.login_context = self.context

        self.init_child_result = dct['init_child_result']

    def get_good_temp_dir(self):
        self._connect()
        return self.init_child_result['good_temp_dir']

    def _generate_tmp_path(self):
        return os.path.join(
            self.get_good_temp_dir(),
            'ansible_mitogen_action_%016x' % (
                random.getrandbits(8*8),
            )
        )

    def _make_tmp_path(self):
        assert getattr(self._shell, 'tmpdir', None) is None
        self._shell.tmpdir = self._generate_tmp_path()
        LOG.debug('Temporary directory: %r', self._shell.tmpdir)
        self.get_chain().call_no_reply(os.mkdir, self._shell.tmpdir)
        return self._shell.tmpdir

    def _reset_tmp_path(self):
        """
        Called by _reset(); ask the remote context to delete any temporary
        directory created for the action. CallChain is not used here to ensure
        exception is logged by the context on failure, since the CallChain
        itself is about to be destructed.
        """
        if getattr(self._shell, 'tmpdir', None) is not None:
            self.context.call_no_reply(
                ansible_mitogen.target.prune_tree,
                self._shell.tmpdir,
            )
            self._shell.tmpdir = None

    def _connect(self):
        """
        Establish a connection to the master process's UNIX listener socket,
        constructing a mitogen.master.Router to communicate with the master,
        and a mitogen.parent.Context to represent it.

        Depending on the original transport we should emulate, trigger one of
        the _connect_*() service calls defined above to cause the master
        process to establish the real connection on our behalf, or return a
        reference to the existing one.
        """
        if self.connected:
            return

        self._connect_broker()
        stack = self._build_stack()
        self._connect_stack(stack)

    def _reset(self, mode):
        """
        Forget everything we know about the connected context.

        :param str mode:
            Name of ContextService method to use to discard the context, either
            'put' or 'reset'.
        """
        if not self.context:
            return

        self._reset_tmp_path()
        self.chain.reset()
        self.parent.call_service(
            service_name='ansible_mitogen.services.ContextService',
            method_name=mode,
            context=self.context
        )

        self.context = None
        self.login_context = None
        self.init_child_result = None
        self.chain = None

    def close(self):
        """
        Arrange for the mitogen.master.Router running in the worker to
        gracefully shut down, and wait for shutdown to complete. Safe to call
        multiple times.
        """
        self._reset(mode='put')
        if self.broker:
            self.broker.shutdown()
            self.broker.join()
            self.broker = None
            self.router = None

    def reset(self):
        """
        Explicitly terminate the connection to the remote host. This discards
        any local state we hold for the connection, returns the Connection to
        the 'disconnected' state, and informs ContextService the connection is
        bad somehow, and should be shut down and discarded.
        """
        self._connect()
        self._reset(mode='reset')

    def get_chain(self, use_login=False, use_fork=False):
        """
        Return the :class:`mitogen.parent.CallChain` to use for executing
        function calls.

        :param bool use_login:
            If :data:`True`, always return the chain for the login account
            rather than any active become user.
        :param bool use_fork:
            If :data:`True`, return the chain for the fork parent.
        :returns mitogen.parent.CallChain:
        """
        self._connect()
        if use_login:
            return self.login_context.default_call_chain
        if use_fork:
            return self.init_child_result['fork_context'].default_call_chain
        return self.chain

    def create_fork_child(self):
        """
        Fork a new child off the target context. The actual fork occurs from
        the 'virginal fork parent', which does not any Ansible modules prior to
        fork, to avoid conflicts resulting from custom module_utils paths.

        :returns:
            mitogen.core.Context of the new child.
        """
        return self.get_chain(use_fork=True).call(
            ansible_mitogen.target.create_fork_child
        )

    def get_extra_args(self):
        """
        Overridden by connections/mitogen_kubectl.py to a list of additional
        arguments for the command.
        """
        # TODO: maybe use this for SSH too.
        return []

    def get_default_cwd(self):
        """
        Overridden by connections/mitogen_local.py to emulate behaviour of CWD
        being fixed to that of ActionBase._loader.get_basedir().
        """
        return None

    def get_default_env(self):
        """
        Overridden by connections/mitogen_local.py to emulate behaviour of
        WorkProcess environment inherited from WorkerProcess.
        """
        return None

    def exec_command(self, cmd, in_data='', sudoable=True, mitogen_chdir=None):
        """
        Implement exec_command() by calling the corresponding
        ansible_mitogen.target function in the target.

        :param str cmd:
            Shell command to execute.
        :param bytes in_data:
            Data to supply on ``stdin`` of the process.
        :returns:
            (return code, stdout bytes, stderr bytes)
        """
        emulate_tty = (not in_data and sudoable)
        rc, stdout, stderr = self.get_chain().call(
            ansible_mitogen.target.exec_command,
            cmd=mitogen.utils.cast(cmd),
            in_data=mitogen.utils.cast(in_data),
            chdir=mitogen_chdir or self.get_default_cwd(),
            emulate_tty=emulate_tty,
        )

        stderr += 'Shared connection to %s closed.%s' % (
            self._play_context.remote_addr,
            ('\r\n' if emulate_tty else '\n'),
        )
        return rc, stdout, stderr

    def fetch_file(self, in_path, out_path):
        """
        Implement fetch_file() by calling the corresponding
        ansible_mitogen.target function in the target.

        :param str in_path:
            Remote filesystem path to read.
        :param str out_path:
            Local filesystem path to write.
        """
        output = self.get_chain().call(
            ansible_mitogen.target.read_path,
            mitogen.utils.cast(in_path),
        )
        ansible_mitogen.target.write_path(out_path, output)

    def put_data(self, out_path, data, mode=None, utimes=None):
        """
        Implement put_file() by caling the corresponding ansible_mitogen.target
        function in the target, transferring small files inline. This is
        pipelined and will return immediately; failed transfers are reported as
        exceptions in subsequent functon calls.

        :param str out_path:
            Remote filesystem path to write.
        :param byte data:
            File contents to put.
        """
        self.get_chain().call_no_reply(
            ansible_mitogen.target.write_path,
            mitogen.utils.cast(out_path),
            mitogen.core.Blob(data),
            mode=mode,
            utimes=utimes,
        )

    #: Maximum size of a small file before switching to streaming
    #: transfer. This should really be the same as
    #: mitogen.services.FileService.IO_SIZE, however the message format has
    #: slightly more overhead, so just randomly subtract 4KiB.
    SMALL_FILE_LIMIT = mitogen.core.CHUNK_SIZE - 4096

    def put_file(self, in_path, out_path):
        """
        Implement put_file() by streamily transferring the file via
        FileService.

        :param str in_path:
            Local filesystem path to read.
        :param str out_path:
            Remote filesystem path to write.
        """
        st = os.stat(in_path)
        if not stat.S_ISREG(st.st_mode):
            raise IOError('%r is not a regular file.' % (in_path,))

        # If the file is sufficiently small, just ship it in the argument list
        # rather than introducing an extra RTT for the child to request it from
        # FileService.
        if st.st_size <= self.SMALL_FILE_LIMIT:
            fp = open(in_path, 'rb')
            try:
                s = fp.read(self.SMALL_FILE_LIMIT + 1)
            finally:
                fp.close()

            # Ensure did not grow during read.
            if len(s) == st.st_size:
                return self.put_data(out_path, s, mode=st.st_mode,
                                     utimes=(st.st_atime, st.st_mtime))

        self.parent.call_service(
            service_name='mitogen.service.FileService',
            method_name='register',
            path=mitogen.utils.cast(in_path)
        )

        # For now this must remain synchronous, as the action plug-in may have
        # passed us a temporary file to transfer. A future FileService could
        # maintain an LRU list of open file descriptors to keep the temporary
        # file alive, but that requires more work.
        self.get_chain().call(
            ansible_mitogen.target.transfer_file,
            context=self.parent,
            in_path=in_path,
            out_path=out_path
        )
