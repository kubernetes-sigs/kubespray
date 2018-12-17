import logging
from unittest import TestCase

from parameterized import parameterized, param

from hvac import exceptions
from hvac.tests import utils


class TestApprole(utils.HvacIntegrationTestCase, TestCase):
    TEST_MOUNT_POINT = 'approle'

    def setUp(self):
        super(TestApprole, self).setUp()
        self.client.enable_auth_backend(
            backend_type='approle',
            mount_point=self.TEST_MOUNT_POINT,
        )

    def tearDown(self):
        self.client.token = self.manager.root_token
        self.client.disable_auth_backend(mount_point=self.TEST_MOUNT_POINT)
        super(TestApprole, self).tearDown()

    @parameterized.expand([
        param(
            'no secret ids',
            num_secrets_to_create=0,
            raises=exceptions.InvalidPath,
        ),
        param(
            'one secret id',
            num_secrets_to_create=1,
        ),
        param(
            'two secret ids',
            num_secrets_to_create=2,
        ),
    ])
    def test_list_role_secrets(self, label, num_secrets_to_create=0, raises=None):
        test_role_name = 'testrole'
        self.client.create_role(
            role_name=test_role_name,
            mount_point=self.TEST_MOUNT_POINT,
        )
        for _ in range(0, num_secrets_to_create):
            self.client.create_role_secret_id(
                role_name=test_role_name,
                mount_point=self.TEST_MOUNT_POINT,
            )

        if raises:
            with self.assertRaises(raises):
                self.client.list_role_secrets(
                    role_name=test_role_name,
                    mount_point=self.TEST_MOUNT_POINT,
                )
        else:
            list_role_secrets_response = self.client.list_role_secrets(
                role_name=test_role_name,
                mount_point=self.TEST_MOUNT_POINT,
            )
            logging.debug('list_role_secrets_response: %s' % list_role_secrets_response)
            self.assertEqual(
                first=num_secrets_to_create,
                second=len(list_role_secrets_response['data']['keys'])
            )

    def test_create_role(self):
        self.client.create_role('testrole')

        result = self.client.read('auth/approle/role/testrole')
        lib_result = self.client.get_role('testrole')
        del result['request_id']
        del lib_result['request_id']

        self.assertEqual(result, lib_result)

    def test_delete_role(self):
        test_role_name = 'test-role'

        self.client.create_role(test_role_name)
        # We add a second dummy test role so we can still hit the /role?list=true route after deleting the first role
        self.client.create_role('test-role-2')

        # Ensure our created role shows up when calling list_roles as expected
        result = self.client.list_roles()
        actual_list_role_keys = result['data']['keys']
        self.assertIn(
            member=test_role_name,
            container=actual_list_role_keys,
        )

        # Now delete the role and verify its absence when calling list_roles
        self.client.delete_role(test_role_name)
        result = self.client.list_roles()
        actual_list_role_keys = result['data']['keys']
        self.assertNotIn(
            member=test_role_name,
            container=actual_list_role_keys,
        )

    def test_create_delete_role_secret_id(self):
        self.client.create_role('testrole')
        create_result = self.client.create_role_secret_id('testrole', {'foo': 'bar'})
        secret_id = create_result['data']['secret_id']
        result = self.client.get_role_secret_id('testrole', secret_id)
        self.assertEqual(result['data']['metadata']['foo'], 'bar')
        self.client.delete_role_secret_id('testrole', secret_id)
        with self.assertRaises(ValueError):
            self.client.get_role_secret_id('testrole', secret_id)

    def test_auth_approle(self):
        self.client.create_role('testrole')
        create_result = self.client.create_role_secret_id('testrole', {'foo': 'bar'})
        secret_id = create_result['data']['secret_id']
        role_id = self.client.get_role_id('testrole')
        result = self.client.auth_approle(role_id, secret_id)
        self.assertEqual(result['auth']['metadata']['foo'], 'bar')
        self.assertEqual(self.client.token, result['auth']['client_token'])
        self.assertTrue(self.client.is_authenticated())

    def test_auth_approle_dont_use_token(self):
        self.client.create_role('testrole')
        create_result = self.client.create_role_secret_id('testrole', {'foo': 'bar'})
        secret_id = create_result['data']['secret_id']
        role_id = self.client.get_role_id('testrole')
        result = self.client.auth_approle(role_id, secret_id, use_token=False)
        self.assertEqual(result['auth']['metadata']['foo'], 'bar')
        self.assertNotEqual(self.client.token, result['auth']['client_token'])
