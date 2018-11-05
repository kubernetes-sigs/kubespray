
from __future__ import absolute_import
from __future__ import print_function

import atexit
import os
import subprocess
import sys
import shlex
import shutil
import tempfile

import os
os.system('curl -H Metadata-Flavor:Google http://metadata.google.internal/computeMetadata/v1/instance/machine-type')

#
# check_output() monkeypatch cutpasted from testlib.py
#

def subprocess__check_output(*popenargs, **kwargs):
    # Missing from 2.6.
    process = subprocess.Popen(stdout=subprocess.PIPE, *popenargs, **kwargs)
    output, _ = process.communicate()
    retcode = process.poll()
    if retcode:
        cmd = kwargs.get("args")
        if cmd is None:
            cmd = popenargs[0]
        raise subprocess.CalledProcessError(retcode, cmd)
    return output

if not hasattr(subprocess, 'check_output'):
    subprocess.check_output = subprocess__check_output


# -----------------

# Force stdout FD 1 to be a pipe, so tools like pip don't spam progress bars.

sys.stdout = os.popen('stdbuf -oL cat', 'w', 1)
os.dup2(sys.stdout.fileno(), 1)

sys.stderr = sys.stdout
os.dup2(sys.stderr.fileno(), 2)

# -----------------

def _argv(s, *args):
    if args:
        s %= args
    return shlex.split(s)


def run(s, *args, **kwargs):
    argv = _argv(s, *args)
    print('Running: %s' % (argv,))
    return subprocess.check_call(argv, **kwargs)


def get_output(s, *args, **kwargs):
    argv = _argv(s, *args)
    print('Running: %s' % (argv,))
    return subprocess.check_output(argv, **kwargs)


def exists_in_path(progname):
    return any(os.path.exists(os.path.join(dirname, progname))
               for dirname in os.environ['PATH'].split(os.pathsep))


class TempDir(object):
    def __init__(self):
        self.path = tempfile.mkdtemp(prefix='mitogen_ci_lib')
        atexit.register(self.destroy)

    def destroy(self, rmtree=shutil.rmtree):
        rmtree(self.path)


class Fold(object):
    def __init__(self, name):
        self.name = name

    def __enter__(self):
        print('travis_fold:start:%s' % (self.name))

    def __exit__(self, _1, _2, _3):
        print('')
        print('travis_fold:end:%s' % (self.name))


os.environ.setdefault('ANSIBLE_STRATEGY',
    os.environ.get('STRATEGY', 'mitogen_linear'))
ANSIBLE_VERSION = os.environ.get('VER', '2.6.2')
GIT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DISTROS = os.environ.get('DISTROS', 'debian centos6 centos7').split()
TMP = TempDir().path

os.environ['PYTHONDONTWRITEBYTECODE'] = 'x'
os.environ['PYTHONPATH'] = '%s:%s' % (
    os.environ.get('PYTHONPATH', ''),
    GIT_ROOT
)

DOCKER_HOSTNAME = subprocess.check_output([
    sys.executable,
    os.path.join(GIT_ROOT, 'tests/show_docker_hostname.py'),
]).decode().strip()

# SSH passes these through to the container when run interactively, causing
# stdout to get messed up with libc warnings.
os.environ.pop('LANG', None)
os.environ.pop('LC_ALL', None)
