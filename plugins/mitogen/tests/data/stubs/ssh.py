#!/usr/bin/env python

import optparse
import os
import shlex
import subprocess
import sys


HOST_KEY_ASK_MSG = """
The authenticity of host '[91.121.165.123]:9122 ([91.121.165.123]:9122)' can't be established.
ECDSA key fingerprint is SHA256:JvfPvazZzQ9/CUdKN7tiYlNZtDRdEgDsYVIzOgPrsR4.
Are you sure you want to continue connecting (yes/no)?
""".strip('\n')

HOST_KEY_STRICT_MSG = """Host key verification failed.\n"""

PERMDENIED_CLASSIC_MSG = 'Permission denied (publickey,password)\n'
PERMDENIED_75_MSG = 'chicken@nandos.com: permission denied (publickey,password)\n'


def tty(msg):
    fp = open('/dev/tty', 'wb', 0)
    fp.write(msg.encode())
    fp.close()


def stderr(msg):
    fp = open('/dev/stderr', 'wb', 0)
    fp.write(msg.encode())
    fp.close()


def confirm(msg):
    tty(msg)
    fp = open('/dev/tty', 'rb', 0)
    try:
        return fp.readline().decode()
    finally:
        fp.close()


mode = os.getenv('STUBSSH_MODE')

if mode == 'ask':
    assert 'yes\n' == confirm(HOST_KEY_ASK_MSG)

elif mode == 'strict':
    stderr(HOST_KEY_STRICT_MSG)
    sys.exit(255)

elif mode == 'permdenied_classic':
    stderr(PERMDENIED_CLASSIC_MSG)
    sys.exit(255)

elif mode == 'permdenied_75':
    stderr(PERMDENIED_75_MSG)
    sys.exit(255)


#
# Set an env var if stderr was a TTY to make ssh_test tests easier to write.
#
if os.isatty(2):
    os.environ['STDERR_WAS_TTY'] = '1'


parser = optparse.OptionParser()
parser.add_option('--user', '-l', action='store')
parser.add_option('-o', dest='options', action='append')
parser.disable_interspersed_args()

opts, args = parser.parse_args(sys.argv[1:])
args.pop(0)  # hostname

# On Linux the TTY layer appears to begin tearing down a PTY after the last FD
# for it is closed, causing SIGHUP to be sent to its foreground group. Since
# the bootstrap overwrites the last such fd (stderr), we can't just exec it
# directly, we must hold it open just like real SSH would. So use
# subprocess.call() rather than os.execve() here.
args = [''.join(shlex.split(s)) for s in args]
sys.exit(subprocess.call(args))
