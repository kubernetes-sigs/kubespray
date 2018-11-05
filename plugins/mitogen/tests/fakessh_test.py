
import os
import shutil

import timeoutcontext
import unittest2

import mitogen.fakessh

import testlib


class RsyncTest(testlib.DockerMixin, unittest2.TestCase):
    @timeoutcontext.timeout(5)
    @unittest2.skip('broken')
    def test_rsync_from_master(self):
        context = self.docker_ssh_any()

        if context.call(os.path.exists, '/tmp/data'):
            context.call(shutil.rmtree, '/tmp/data')

        return_code = mitogen.fakessh.run(context, self.router, [
            'rsync', '--progress', '-vvva',
            testlib.data_path('.'), 'target:/tmp/data'
        ])

        self.assertEqual(return_code, 0)
        self.assertTrue(context.call(os.path.exists, '/tmp/data'))
        self.assertTrue(context.call(os.path.exists, '/tmp/data/simple_pkg/a.py'))

    @timeoutcontext.timeout(5)
    @unittest2.skip('broken')
    def test_rsync_between_direct_children(self):
        # master -> SSH -> mitogen__has_sudo_pubkey -> rsync(.ssh) -> master ->
        # mitogen__has_sudo -> rsync

        pubkey_acct = self.docker_ssh(
            username='mitogen__has_sudo_pubkey',
            identity_file=testlib.data_path('docker/mitogen__has_sudo_pubkey.key'),
        )

        nopw_acct = self.docker_ssh(
            username='mitogen__has_sudo_nopw',
            password='has_sudo_nopw_password',
        )

        webapp_acct = self.router.sudo(
            via=nopw_acct,
            username='webapp',
        )

        dest_path = webapp_acct.call(os.path.expanduser, '~/.ssh')
        if webapp_acct.call(os.path.exists, dest_path):
            webapp_acct.call(shutil.rmtree, dest_path)

        return_code = pubkey_acct.call(mitogen.fakessh.run, webapp_acct, args=[
            'rsync', '--progress', '-vvva', '.ssh/', 'target:' + dest_path
        ])

        self.assertEqual(return_code, 0)
        self.assertEqual(
            pubkey_acct.call(os.path.getsize, '.ssh/authorized_keys'),
            webapp_acct.call(os.path.getsize, dest_path + '/authorized_keys'),
        )


if __name__ == '__main__':
    unittest2.main()
