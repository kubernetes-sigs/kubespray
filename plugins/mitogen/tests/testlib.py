
import logging
import os
import random
import re
import socket
import subprocess
import sys
import time

import unittest2

import mitogen.core
import mitogen.master
import mitogen.utils

try:
    import faulthandler
except ImportError:
    pass

try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO


LOG = logging.getLogger(__name__)
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
sys.path.append(DATA_DIR)

if mitogen.is_master:
    mitogen.utils.log_to_file()

if faulthandler is not None:
    faulthandler.enable()


def data_path(suffix):
    path = os.path.join(DATA_DIR, suffix)
    if path.endswith('.key'):
        # SSH is funny about private key permissions.
        os.chmod(path, int('0600', 8))
    return path


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

if hasattr(subprocess, 'check_output'):
    subprocess__check_output = subprocess.check_output


def wait_for_port(
        host,
        port,
        pattern=None,
        connect_timeout=0.5,
        receive_timeout=0.5,
        overall_timeout=5.0,
        sleep=0.1,
        ):
    """Attempt to connect to host/port, for upto overall_timeout seconds.
    If a regex pattern is supplied try to find it in the initial data.
    Return None on success, or raise on error.
    """
    start = time.time()
    end = start + overall_timeout
    addr = (host, port)

    while time.time() < end:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(connect_timeout)
        try:
            sock.connect(addr)
        except socket.error:
            # Failed to connect. So wait then retry.
            time.sleep(sleep)
            continue

        if not pattern:
            # Success: We connected & there's no banner check to perform.
            sock.shutdown(socket.SHUTD_RDWR)
            sock.close()
            return

        sock.settimeout(receive_timeout)
        data = mitogen.core.b('')
        found = False
        while time.time() < end:
            try:
                resp = sock.recv(1024)
            except socket.timeout:
                # Server stayed up, but had no data. Retry the recv().
                continue

            if not resp:
                # Server went away. Wait then retry the connection.
                time.sleep(sleep)
                break

            data += resp
            if re.search(mitogen.core.b(pattern), data):
                found = True
                break

        try:
            sock.shutdown(socket.SHUT_RDWR)
        except socket.error:
            e = sys.exc_info()[1]
            # On Mac OS X - a BSD variant - the above code only succeeds if the
            # operating system thinks that the socket is still open when
            # shutdown() is invoked. If Python is too slow and the FIN packet
            # arrives before that statement can be reached, then OS X kills the
            # sock.shutdown() statement with:
            #
            #    socket.error: [Errno 57] Socket is not connected
            #
            # Protect shutdown() with a try...except that catches the
            # socket.error, test to make sure Errno is right, and ignore it if
            # Errno matches.
            if e.errno == 57:
                pass
            else:
                raise
        sock.close()

        if found:
            # Success: We received the banner & found the desired pattern
            return
    else:
        # Failure: The overall timeout expired
        if pattern:
            raise socket.timeout('Timed out while searching for %r from %s:%s'
                                 % (pattern, host, port))
        else:
            raise socket.timeout('Timed out while connecting to %s:%s'
                                 % (host, port))


def sync_with_broker(broker, timeout=10.0):
    """
    Insert a synchronization barrier between the calling thread and the Broker
    thread, ensuring it has completed at least one full IO loop before
    returning.

    Used to block while asynchronous stuff (like defer()) happens on the
    broker.
    """
    sem = mitogen.core.Latch()
    broker.defer(sem.put, None)
    sem.get(timeout=10.0)


class CaptureStreamHandler(logging.StreamHandler):
    def __init__(self, *args, **kwargs):
        logging.StreamHandler.__init__(self, *args, **kwargs)
        self.msgs = []

    def emit(self, msg):
        self.msgs.append(msg)
        logging.StreamHandler.emit(self, msg)


class LogCapturer(object):
    def __init__(self, name=None):
        self.sio = StringIO()
        self.logger = logging.getLogger(name)
        self.handler = CaptureStreamHandler(self.sio)
        self.old_propagate = self.logger.propagate
        self.old_handlers = self.logger.handlers
        self.old_level = self.logger.level

    def start(self):
        self.logger.handlers = [self.handler]
        self.logger.propagate = False
        self.logger.level = logging.DEBUG

    def raw(self):
        return self.sio.getvalue()

    def msgs(self):
        return self.handler.msgs

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, _1, _2, _3):
        self.stop()

    def stop(self):
        self.logger.level = self.old_level
        self.logger.handlers = self.old_handlers
        self.logger.propagate = self.old_propagate
        return self.raw()


class TestCase(unittest2.TestCase):
    def assertRaises(self, exc, func, *args, **kwargs):
        """Like regular assertRaises, except return the exception that was
        raised. Can't use context manager because tests must run on Python2.4"""
        try:
            func(*args, **kwargs)
        except exc:
            e = sys.exc_info()[1]
            return e
        except BaseException:
            LOG.exception('Original exception')
            e = sys.exc_info()[1]
            assert 0, '%r raised %r, not %r' % (func, e, exc)
        assert 0, '%r did not raise %r' % (func, exc)


def get_docker_host():
    url = os.environ.get('DOCKER_HOST')
    if url in (None, 'http+docker://localunixsocket'):
        return 'localhost'

    parsed = urlparse.urlparse(url)
    return parsed.netloc.partition(':')[0]


class DockerizedSshDaemon(object):
    image = None

    def get_image(self):
        if not self.image:
            distro = os.environ.get('MITOGEN_TEST_DISTRO', 'debian')
            self.image = 'mitogen/%s-test' % (distro,)
        return self.image

    # 22/tcp -> 0.0.0.0:32771
    PORT_RE = re.compile(r'([^/]+)/([^ ]+) -> ([^:]+):(.*)')
    port = None

    def _get_container_port(self):
        s = subprocess__check_output(['docker', 'port', self.container_name])
        for line in s.decode().splitlines():
            dport, proto, baddr, bport = self.PORT_RE.match(line).groups()
            if dport == '22' and proto == 'tcp':
                self.port = int(bport)

        self.host = self.get_host()
        if self.port is None:
            raise ValueError('could not find SSH port in: %r' % (s,))

    def start_container(self):
        self.container_name = 'mitogen-test-%08x' % (random.getrandbits(64),)
        args = [
            'docker',
            'run',
            '--detach',
            '--privileged',
            '--publish-all',
            '--name', self.container_name,
            self.get_image()
        ]
        subprocess__check_output(args)
        self._get_container_port()

    def __init__(self):
        self.start_container()

    def get_host(self):
        return get_docker_host()

    def wait_for_sshd(self):
        wait_for_port(self.get_host(), self.port, pattern='OpenSSH')

    def close(self):
        args = ['docker', 'rm', '-f', self.container_name]
        subprocess__check_output(args)


class BrokerMixin(object):
    broker_class = mitogen.master.Broker

    def setUp(self):
        super(BrokerMixin, self).setUp()
        self.broker = self.broker_class()

    def tearDown(self):
        self.broker.shutdown()
        self.broker.join()
        super(BrokerMixin, self).tearDown()

    def sync_with_broker(self):
        sync_with_broker(self.broker)


class RouterMixin(BrokerMixin):
    router_class = mitogen.master.Router

    def setUp(self):
        super(RouterMixin, self).setUp()
        self.router = self.router_class(self.broker)


class DockerMixin(RouterMixin):
    @classmethod
    def setUpClass(cls):
        super(DockerMixin, cls).setUpClass()
        cls.dockerized_ssh = DockerizedSshDaemon()
        cls.dockerized_ssh.wait_for_sshd()

    @classmethod
    def tearDownClass(cls):
        cls.dockerized_ssh.close()
        super(DockerMixin, cls).tearDownClass()

    def docker_ssh(self, **kwargs):
        kwargs.setdefault('hostname', self.dockerized_ssh.host)
        kwargs.setdefault('port', self.dockerized_ssh.port)
        kwargs.setdefault('check_host_keys', 'ignore')
        kwargs.setdefault('ssh_debug_level', 3)
        return self.router.ssh(**kwargs)

    def docker_ssh_any(self, **kwargs):
        return self.docker_ssh(
            username='mitogen__has_sudo_nopw',
            password='has_sudo_nopw_password',
        )
