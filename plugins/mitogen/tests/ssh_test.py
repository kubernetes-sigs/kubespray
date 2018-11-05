import os
import sys
import tempfile

import mitogen
import mitogen.ssh
import mitogen.utils

import unittest2

import testlib
import plain_old_module


class StubSshMixin(testlib.RouterMixin):
    """
    Mix-in that provides :meth:`stub_ssh` executing the stub 'ssh.py'.
    """
    def stub_ssh(self, STUBSSH_MODE=None, **kwargs):
        os.environ['STUBSSH_MODE'] = str(STUBSSH_MODE)
        try:
            return self.router.ssh(
                hostname='hostname',
                username='mitogen__has_sudo',
                ssh_path=testlib.data_path('stubs/ssh.py'),
                **kwargs
            )
        finally:
            del os.environ['STUBSSH_MODE']


class ConstructorTest(testlib.RouterMixin, unittest2.TestCase):
    def test_okay(self):
        context = self.router.ssh(
            hostname='hostname',
            username='mitogen__has_sudo',
            ssh_path=testlib.data_path('stubs/ssh.py'),
        )
        #context.call(mitogen.utils.log_to_file, '/tmp/log')
        #context.call(mitogen.utils.disable_site_packages)
        self.assertEquals(3, context.call(plain_old_module.add, 1, 2))


class SshTest(testlib.DockerMixin, testlib.TestCase):
    stream_class = mitogen.ssh.Stream

    def test_stream_name(self):
        context = self.docker_ssh(
            username='mitogen__has_sudo',
            password='has_sudo_password',
        )
        name = 'ssh.%s:%s' % (
            self.dockerized_ssh.get_host(),
            self.dockerized_ssh.port,
        )
        self.assertEquals(name, context.name)

    def test_via_stream_name(self):
        context = self.docker_ssh(
            username='mitogen__has_sudo_nopw',
            password='has_sudo_nopw_password',
        )
        sudo = self.router.sudo(via=context)

        name = 'ssh.%s:%s.sudo.root' % (
            self.dockerized_ssh.host,
            self.dockerized_ssh.port,
        )
        self.assertEquals(name, sudo.name)

    def test_password_required(self):
        try:
            context = self.docker_ssh(
                username='mitogen__has_sudo',
            )
            assert 0, 'exception not thrown'
        except mitogen.ssh.PasswordError:
            e = sys.exc_info()[1]

        self.assertEqual(e.args[0], self.stream_class.password_required_msg)

    def test_password_incorrect(self):
        try:
            context = self.docker_ssh(
                username='mitogen__has_sudo',
                password='badpw',
            )
            assert 0, 'exception not thrown'
        except mitogen.ssh.PasswordError:
            e = sys.exc_info()[1]

        self.assertEqual(e.args[0], self.stream_class.password_incorrect_msg)

    def test_password_specified(self):
        context = self.docker_ssh(
            username='mitogen__has_sudo',
            password='has_sudo_password',
        )

        self.assertEqual(
            'i-am-mitogen-test-docker-image\n',
            context.call(plain_old_module.get_sentinel_value),
        )

    def test_pubkey_required(self):
        try:
            context = self.docker_ssh(
                username='mitogen__has_sudo_pubkey',
            )
            assert 0, 'exception not thrown'
        except mitogen.ssh.PasswordError:
            e = sys.exc_info()[1]

        self.assertEqual(e.args[0], self.stream_class.password_required_msg)

    def test_pubkey_specified(self):
        context = self.docker_ssh(
            username='mitogen__has_sudo_pubkey',
            identity_file=testlib.data_path('docker/mitogen__has_sudo_pubkey.key'),
        )
        self.assertEqual(
            'i-am-mitogen-test-docker-image\n',
            context.call(plain_old_module.get_sentinel_value),
        )

    def test_enforce_unknown_host_key(self):
        fp = tempfile.NamedTemporaryFile()
        try:
            e = self.assertRaises(mitogen.ssh.HostKeyError,
                lambda: self.docker_ssh(
                    username='mitogen__has_sudo_pubkey',
                    password='has_sudo_password',
                    ssh_args=['-o', 'UserKnownHostsFile ' + fp.name],
                    check_host_keys='enforce',
                )
            )
            self.assertEquals(e.args[0], mitogen.ssh.Stream.hostkey_failed_msg)
        finally:
            fp.close()

    def test_accept_enforce_host_keys(self):
        fp = tempfile.NamedTemporaryFile()
        try:
            context = self.docker_ssh(
                username='mitogen__has_sudo',
                password='has_sudo_password',
                ssh_args=['-o', 'UserKnownHostsFile ' + fp.name],
                check_host_keys='accept',
            )
            context.shutdown(wait=True)

            fp.seek(0)
            # Lame test, but we're about to use enforce mode anyway, which
            # verifies the file contents.
            self.assertTrue(len(fp.read()) > 0)

            context = self.docker_ssh(
                username='mitogen__has_sudo',
                password='has_sudo_password',
                ssh_args=['-o', 'UserKnownHostsFile ' + fp.name],
                check_host_keys='enforce',
            )
            context.shutdown(wait=True)
        finally:
            fp.close()


class BannerTest(testlib.DockerMixin, unittest2.TestCase):
    # Verify the ability to disambiguate random spam appearing in the SSHd's
    # login banner from a legitimate password prompt.
    stream_class = mitogen.ssh.Stream

    def test_verbose_enabled(self):
        context = self.docker_ssh(
            username='mitogen__has_sudo',
            password='has_sudo_password',
            ssh_debug_level=3,
        )
        name = 'ssh.%s:%s' % (
            self.dockerized_ssh.get_host(),
            self.dockerized_ssh.port,
        )
        self.assertEquals(name, context.name)


class StubPermissionDeniedTest(StubSshMixin, testlib.TestCase):
    def test_classic_prompt(self):
        self.assertRaises(mitogen.ssh.PasswordError,
            lambda: self.stub_ssh(STUBSSH_MODE='permdenied_classic'))

    def test_openssh_75_prompt(self):
        self.assertRaises(mitogen.ssh.PasswordError,
            lambda: self.stub_ssh(STUBSSH_MODE='permdenied_75'))


class StubCheckHostKeysTest(StubSshMixin, testlib.TestCase):
    stream_class = mitogen.ssh.Stream

    def test_check_host_keys_accept(self):
        # required=true, host_key_checking=accept
        context = self.stub_ssh(STUBSSH_MODE='ask', check_host_keys='accept')
        self.assertEquals('1', context.call(os.getenv, 'STDERR_WAS_TTY'))

    def test_check_host_keys_enforce(self):
        # required=false, host_key_checking=enforce
        context = self.stub_ssh(check_host_keys='enforce')
        self.assertEquals(None, context.call(os.getenv, 'STDERR_WAS_TTY'))

    def test_check_host_keys_ignore(self):
        # required=false, host_key_checking=ignore
        context = self.stub_ssh(check_host_keys='ignore')
        self.assertEquals(None, context.call(os.getenv, 'STDERR_WAS_TTY'))

    def test_password_present(self):
        # required=true, password is not None
        context = self.stub_ssh(check_host_keys='ignore', password='willick')
        self.assertEquals('1', context.call(os.getenv, 'STDERR_WAS_TTY'))


if __name__ == '__main__':
    unittest2.main()
