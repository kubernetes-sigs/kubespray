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

import ctypes
import grp
import logging
import os
import pwd
import subprocess
import sys

import mitogen.core
import mitogen.parent


LOG = logging.getLogger(__name__)
LIBC = ctypes.CDLL(None, use_errno=True)
LIBC__strerror = LIBC.strerror
LIBC__strerror.restype = ctypes.c_char_p


class Error(mitogen.core.StreamError):
    pass


def setns(kind, fd):
    if LIBC.setns(int(fd), 0) == -1:
        errno = ctypes.get_errno()
        msg = 'setns(%s, %s): %s' % (fd, kind, LIBC__strerror(errno))
        raise OSError(errno, msg)


def _run_command(args):
    argv = mitogen.parent.Argv(args)
    try:
        proc = subprocess.Popen(
            args=args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
    except OSError:
        e = sys.exc_info()[1]
        raise Error('could not execute %s: %s', argv, e)

    output, _ = proc.communicate()
    if not proc.returncode:
        return output

    raise Error("%s exitted with status %d: %s",
                mitogen.parent.Argv(args), proc.returncode, output)


def get_docker_pid(path, name):
    args = [path, 'inspect', '--format={{.State.Pid}}', name]
    output = _run_command(args)
    try:
        return int(output)
    except ValueError:
        raise Error("could not find PID from docker output.\n%s", output)


def get_lxc_pid(path, name):
    output = _run_command([path, '-n', name])
    for line in output.splitlines():
        bits = line.split()
        if bits and bits[0] == 'PID:':
            return int(bits[1])

    raise Error("could not find PID from lxc-info output.\n%s", output)


def get_lxd_pid(path, name):
    output = _run_command([path, 'info', name])
    for line in output.splitlines():
        bits = line.split()
        if bits and bits[0] == 'Pid:':
            return int(bits[1])

    raise Error("could not find PID from lxc output.\n%s", output)


def get_machinectl_pid(path, name):
    output = _run_command([path, 'status', name])
    for line in output.splitlines():
        bits = line.split()
        if bits and bits[0] == 'Leader:':
            return int(bits[1])

    raise Error("could not find PID from machinectl output.\n%s", output)


class Stream(mitogen.parent.Stream):
    child_is_immediate_subprocess = False

    container = None
    username = 'root'
    kind = None
    python_path = 'python'
    docker_path = 'docker'
    lxc_path = 'lxc'
    lxc_info_path = 'lxc-info'
    machinectl_path = 'machinectl'

    GET_LEADER_BY_KIND = {
        'docker': ('docker_path', get_docker_pid),
        'lxc': ('lxc_info_path', get_lxc_pid),
        'lxd': ('lxc_path', get_lxd_pid),
        'machinectl': ('machinectl_path', get_machinectl_pid),
    }

    def construct(self, container, kind, username=None, docker_path=None,
                  lxc_path=None, lxc_info_path=None, machinectl_path=None,
                  **kwargs):
        super(Stream, self).construct(**kwargs)
        if kind not in self.GET_LEADER_BY_KIND:
            raise Error('unsupported container kind: %r', kind)

        self.container = container
        self.kind = kind
        if username:
            self.username = username
        if docker_path:
            self.docker_path = docker_path
        if lxc_path:
            self.lxc_path = lxc_path
        if lxc_info_path:
            self.lxc_info_path = lxc_info_path
        if machinectl_path:
            self.machinectl_path = machinectl_path

    # Order matters. https://github.com/karelzak/util-linux/commit/854d0fe/
    NS_ORDER = ('ipc', 'uts', 'net', 'pid', 'mnt', 'user')

    def preexec_fn(self):
        nspath = '/proc/%d/ns/' % (self.leader_pid,)
        selfpath = '/proc/self/ns/'
        try:
            ns_fps = [
                open(nspath + name)
                for name in self.NS_ORDER
                if os.path.exists(nspath + name) and (
                    os.readlink(nspath + name) != os.readlink(selfpath + name)
                )
            ]
        except Exception:
            e = sys.exc_info()[1]
            raise Error(str(e))

        os.chdir('/proc/%s/root' % (self.leader_pid,))
        os.chroot('.')
        os.chdir('/')
        for fp in ns_fps:
            setns(fp.name, fp.fileno())
            fp.close()

        for sym in 'endpwent', 'endgrent', 'endspent', 'endsgent':
            try:
                getattr(LIBC, sym)()
            except AttributeError:
                pass

        try:
            os.setgroups([grent.gr_gid
                          for grent in grp.getgrall()
                          if self.username in grent.gr_mem])
            pwent = pwd.getpwnam(self.username)
            os.setreuid(pwent.pw_uid, pwent.pw_uid)
            # shadow-4.4/libmisc/setupenv.c. Not done: MAIL, PATH
            os.environ.update({
                'HOME': pwent.pw_dir,
                'SHELL': pwent.pw_shell or '/bin/sh',
                'LOGNAME': self.username,
                'USER': self.username,
            })
            if ((os.path.exists(pwent.pw_dir) and
                 os.access(pwent.pw_dir, os.X_OK))):
                os.chdir(pwent.pw_dir)
        except Exception:
            e = sys.exc_info()[1]
            raise Error(self.username_msg, self.username, self.container,
                        type(e).__name__, e)

    username_msg = 'while transitioning to user %r in container %r: %s: %s'

    def get_boot_command(self):
        # With setns(CLONE_NEWPID), new children of the caller receive a new
        # PID namespace, however the caller's namespace won't change. That
        # causes subsequent calls to clone() specifying CLONE_THREAD to fail
        # with EINVAL, as threads in the same process can't have varying PID
        # namespaces, meaning starting new threads in the exec'd program will
        # fail. The solution is forking, so inject a /bin/sh call to achieve
        # this.
        argv = super(Stream, self).get_boot_command()
        # bash will exec() if a single command was specified and the shell has
        # nothing left to do, so "; exit $?" gives bash a reason to live.
        return ['/bin/sh', '-c', '%s; exit $?' % (mitogen.parent.Argv(argv),)]

    def create_child(self, args):
        return mitogen.parent.create_child(args, preexec_fn=self.preexec_fn)

    def connect(self):
        attr, func = self.GET_LEADER_BY_KIND[self.kind]
        tool_path = getattr(self, attr)
        self.leader_pid = func(tool_path, self.container)
        LOG.debug('Leader PID for %s container %r: %d',
                  self.kind, self.container, self.leader_pid)
        super(Stream, self).connect()
        self.name = u'setns.' + self.container
