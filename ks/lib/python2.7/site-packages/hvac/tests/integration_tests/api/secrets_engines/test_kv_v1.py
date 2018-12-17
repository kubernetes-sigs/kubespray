from unittest import TestCase

from parameterized import parameterized

from hvac import exceptions
from hvac.tests import utils


class TestKvV1(utils.HvacIntegrationTestCase, TestCase):

    @parameterized.expand([
        ('nonexistent secret', 'no-secret-here', False, exceptions.InvalidPath),
        ('read secret', 'top-secret'),
    ])
    def test_read_secret(self, test_label, path, write_secret_before_test=True, raises=None, exception_message=''):
        test_secret = {
            'pssst': 'hi',
        }
        if write_secret_before_test:
            self.client.secrets.kv.v1.create_or_update_secret(
                path=path,
                secret=test_secret,
            )
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.secrets.kv.v1.read_secret(
                    path=path,
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:

            read_secret_result = self.client.secrets.kv.v1.read_secret(
                path=path,
            )
            self.assertDictEqual(
                d1=test_secret,
                d2=read_secret_result['data'],
            )

    @parameterized.expand([
        ('nonexistent secret', 'hvac/no-secret-here', False, exceptions.InvalidPath),
        ('list secret', 'hvac/top-secret'),
    ])
    def test_list_secrets(self, test_label, path, write_secret_before_test=True, raises=None, exception_message=''):
        test_secret = {
            'pssst': 'hi',
        }
        test_path_prefix, test_key = path.split('/')[:2]

        if write_secret_before_test:
            self.client.secrets.kv.v1.create_or_update_secret(
                path=path,
                secret=test_secret,
            )
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.secrets.kv.v1.list_secrets(
                    path=test_path_prefix,
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            list_secrets_result = self.client.secrets.kv.v1.list_secrets(
                path=test_path_prefix,
            )
            self.assertEqual(
                first=dict(keys=[test_key]),
                second=list_secrets_result['data'],
            )

    @parameterized.expand([
        ('create secret no method specified', 'hvac', None, False),
        ('create secret post method specified', 'hvac', 'POST', False),
        ('create secret invalid method specified', 'hvac', 'GET', False, exceptions.ParamValidationError, '"method" parameter provided invalid value'),
        ('update secret no method specified', 'hvac', None),
        ('update secret put method specified', 'hvac', 'PUT'),
        ('update secret invalid method specified', 'hvac', 'GET', True, exceptions.ParamValidationError, '"method" parameter provided invalid value'),
    ])
    def test_create_or_update_secret(self, test_label, path, method=None, write_secret_before_test=True, raises=None, exception_message=''):
        test_secret = {
            'pssst': 'hi',
        }

        if write_secret_before_test:
            self.client.secrets.kv.v1.create_or_update_secret(
                path=path,
                secret=test_secret,
            )
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.secrets.kv.v1.create_or_update_secret(
                    path=path,
                    secret=test_secret,
                    method=method,
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            create_or_update_secret_result = self.client.secrets.kv.v1.create_or_update_secret(
                path=path,
                secret=test_secret,
                method=method,
            )
            self.assertEqual(
                first=204,
                second=create_or_update_secret_result.status_code,
            )

    @parameterized.expand([
        ('nonexistent secret', 'hvac/no-secret-here'),
        ('delete secret', 'hvac/top-secret'),
    ])
    def test_delete_secret(self, test_label, path, write_secret_before_test=True, raises=None, exception_message=''):
        test_secret = {
            'pssst': 'hi',
        }

        if write_secret_before_test:
            self.client.secrets.kv.v1.create_or_update_secret(
                path=path,
                secret=test_secret,
            )
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.secrets.kv.v1.delete_secret(
                    path=path,
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            delete_secret_result = self.client.secrets.kv.v1.delete_secret(
                path=path,
            )
            self.assertEqual(
                first=204,
                second=delete_secret_result.status_code,
            )
