from unittest import TestCase

from hvac.tests import utils


class TestMount(utils.HvacIntegrationTestCase, TestCase):

    def test_secret_backend_manipulation(self):
        self.assertNotIn(
            member='test/',
            container=self.client.sys.list_mounted_secrets_engines()['data'],
        )

        self.client.sys.enable_secrets_engine(
            backend_type='generic',
            path='test',
        )
        self.assertIn(
            member='test/',
            container=self.client.sys.list_mounted_secrets_engines()['data'],
        )

        secret_backend_tuning = self.client.sys.read_mount_configuration(path='test')
        self.assertEqual(secret_backend_tuning['data']['max_lease_ttl'], 2764800)
        self.assertEqual(secret_backend_tuning['data']['default_lease_ttl'], 2764800)

        self.client.sys.tune_mount_configuration(
            path='test',
            default_lease_ttl='3600s',
            max_lease_ttl='8600s',
        )
        secret_backend_tuning = self.client.sys.read_mount_configuration(path='test')

        self.assertIn('max_lease_ttl', secret_backend_tuning['data'])
        self.assertEqual(secret_backend_tuning['data']['max_lease_ttl'], 8600)
        self.assertIn('default_lease_ttl', secret_backend_tuning['data'])
        self.assertEqual(secret_backend_tuning['data']['default_lease_ttl'], 3600)

        self.client.sys.move_backend(
            from_path='test',
            to_path='foobar',
        )
        self.assertNotIn(
            member='test/',
            container=self.client.sys.list_mounted_secrets_engines()['data'],
        )
        self.assertIn(
            member='foobar/',
            container=self.client.sys.list_mounted_secrets_engines()['data'],
        )

        self.client.token = self.manager.root_token
        self.client.sys.disable_secrets_engine(
            path='foobar'
        )
        self.assertNotIn(
            member='foobar/',
            container=self.client.sys.list_mounted_secrets_engines()['data'],
        )

    def test_get_secret_backend_tuning(self):
        secret_backend_tuning = self.client.sys.read_mount_configuration(path='secret')
        self.assertIn(
            member='default_lease_ttl',
            container=secret_backend_tuning['data'],
        )
