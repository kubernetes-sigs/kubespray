from unittest import TestCase

from hvac.tests import utils


class TestAuth(utils.HvacIntegrationTestCase, TestCase):
    TEST_AUTH_METHOD_TYPE = 'github'
    TEST_AUTH_METHOD_PATH = 'test-github'

    def tearDown(self):
        self.client.sys.disable_auth_method(
            path=self.TEST_AUTH_METHOD_PATH
        )
        super(TestAuth, self).tearDown()

    def test_auth_backend_manipulation(self):
        self.assertNotIn(
            member='%s/' % self.TEST_AUTH_METHOD_PATH,
            container=self.client.sys.list_auth_methods()['data'],
        )

        self.client.sys.enable_auth_method(
            method_type=self.TEST_AUTH_METHOD_TYPE,
            path=self.TEST_AUTH_METHOD_PATH,
        )
        self.assertIn(
            member='%s/' % self.TEST_AUTH_METHOD_PATH,
            container=self.client.sys.list_auth_methods()['data'],
        )

        self.client.sys.disable_auth_method(
            path=self.TEST_AUTH_METHOD_PATH,
        )
        self.assertNotIn(
            member='%s/' % self.TEST_AUTH_METHOD_PATH,
            container=self.client.sys.list_auth_methods()['data'],
        )

    def test_tune_auth_backend(self):
        test_description = 'this is a test auth backend'
        test_max_lease_ttl = 12345678
        self.client.sys.enable_auth_method(
            method_type='approle',
            path=self.TEST_AUTH_METHOD_PATH
        )

        expected_status_code = 204
        response = self.client.sys.tune_auth_method(
            path=self.TEST_AUTH_METHOD_PATH,
            description=test_description,
            max_lease_ttl=test_max_lease_ttl,
        )
        self.assertEqual(
            first=expected_status_code,
            second=response.status_code,
        )

        response = self.client.sys.read_auth_method_tuning(
            path=self.TEST_AUTH_METHOD_PATH
        )

        self.assertEqual(
            first=test_max_lease_ttl,
            second=response['data']['max_lease_ttl']
        )
