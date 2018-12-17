from unittest import TestCase

from parameterized import parameterized

from hvac import exceptions
from hvac.tests import utils

TEST_AUTH_PATH = 'userpass-with-mfa'
UNSUPPORTED_AUTH_PATH = 'approle-that-can-not-have-mfa'


class TestMfa(utils.HvacIntegrationTestCase, TestCase):
    mock_server_port = None

    @classmethod
    def setUpClass(cls):
        super(TestMfa, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        super(TestMfa, cls).tearDownClass()

    def setUp(self):
        super(TestMfa, self).setUp()
        if '%s/' % TEST_AUTH_PATH not in self.client.list_auth_backends():
            self.client.enable_auth_backend(
                backend_type='userpass',
                mount_point=TEST_AUTH_PATH
            )
        if '%s/' % UNSUPPORTED_AUTH_PATH not in self.client.list_auth_backends():
            self.client.enable_auth_backend(
                backend_type='approle',
                mount_point=UNSUPPORTED_AUTH_PATH
            )

    def tearDown(self):
        super(TestMfa, self).tearDown()
        for path in [TEST_AUTH_PATH, UNSUPPORTED_AUTH_PATH]:
            self.client.disable_auth_backend(
                mount_point=path,
            )

    @parameterized.expand([
        ('enable mfa with supported auth method', TEST_AUTH_PATH),
        ('enable mfa with unsupported mfa type', TEST_AUTH_PATH, 'cats', False, exceptions.ParamValidationError, 'Unsupported mfa_type argument provided'),
        ('enable mfa with unconfigured auth method path', 'whats-all-this-then', 'duo', False, exceptions.InvalidPath, 'no handler for route'),
        ('enable mfa with unsupported auth method type', UNSUPPORTED_AUTH_PATH, 'duo', False, exceptions.InvalidPath, 'unsupported path'),
        ('enable mfa with unsupported auth method type forced', TEST_AUTH_PATH, 'cats', True),
    ])
    def test_configure(self, test_label, mount_point, mfa_type='duo', force=False, raises=None, exception_message=''):
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.auth.mfa.configure(
                    mount_point=mount_point,
                    mfa_type=mfa_type,
                    force=force,
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            expected_status_code = 204
            configure_response = self.client.auth.mfa.configure(
                mount_point=mount_point,
                mfa_type=mfa_type,
                force=force,
            )
            self.assertEqual(
                first=expected_status_code,
                second=configure_response.status_code
            )

            read_config_response = self.client.auth.mfa.read_configuration(
                mount_point=mount_point,
            )
            self.assertEqual(
                first=mfa_type,
                second=read_config_response['data']['type']
            )

    @parameterized.expand([
        ('read configured path', TEST_AUTH_PATH),
    ])
    def test_read_configuration(self, test_label, mount_point, add_configuration=True):
        if add_configuration:
            self.client.auth.mfa.configure(
                mount_point=mount_point,
            )

        response = self.client.auth.mfa.read_configuration(
            mount_point=mount_point,
        )
        self.assertIn(
            member='data',
            container=response,
        )

    @parameterized.expand([
        ('configure duo access success', TEST_AUTH_PATH),
    ])
    def test_configure_duo_access(self, test_label, mount_point, host='', integration_key='', secret_key='', raises=None, exception_message=''):
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.auth.mfa.configure_duo_access(
                    mount_point=mount_point,
                    host=host,
                    integration_key=integration_key,
                    secret_key=secret_key,
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            expected_status_code = 204
            configure_response = self.client.auth.mfa.configure_duo_access(
                mount_point=mount_point,
                host=host,
                integration_key=integration_key,
                secret_key=secret_key,
            )
            self.assertEqual(
                first=expected_status_code,
                second=configure_response.status_code
            )

    @parameterized.expand([
        ('enable mfa with supported auth method', TEST_AUTH_PATH),
    ])
    def test_configure_duo_behavior(self, test_label, mount_point, push_info='', user_agent='', username_format='%s', raises=None, exception_message=''):
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.auth.mfa.configure_duo_behavior(
                    mount_point=mount_point,
                    push_info=push_info,
                    user_agent=user_agent,
                    username_format=username_format,
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            expected_status_code = 204
            configure_response = self.client.auth.mfa.configure_duo_behavior(
                mount_point=mount_point,
                push_info=push_info,
                user_agent=user_agent,
                username_format=username_format,
            )
            self.assertEqual(
                first=expected_status_code,
                second=configure_response.status_code
            )

            read_config_response = self.client.auth.mfa.read_duo_behavior_configuration(
                mount_point=mount_point,
            )
            self.assertEqual(
                first=push_info,
                second=read_config_response['data']['push_info']
            )

    @parameterized.expand([
        ('read configured path', TEST_AUTH_PATH),
    ])
    def test_read_duo_behavior_configuration(self, test_label, mount_point, add_configuration=True):
        if add_configuration:
            self.client.auth.mfa.configure(
                mount_point=mount_point,
            )

        response = self.client.auth.mfa.read_duo_behavior_configuration(
            mount_point=mount_point,
        )
        self.assertIn(
            member='data',
            container=response,
        )

    @parameterized.expand([
        ('login without duo access configured', False, exceptions.InvalidRequest, "Duo access credentials haven't been configured."),
    ])
    def test_login_with_mfa(self, test_label, configure_access=True, raises=None, exception_message=''):
        username = 'somedude'
        password = 'myverygoodpassword'

        self.client.auth.mfa.configure(
            mount_point=TEST_AUTH_PATH,
        )
        if configure_access:
            self.client.auth.mfa.configure_duo_access(
                mount_point=TEST_AUTH_PATH,
                host='localhost:{port}'.format(port=self.mock_server_port),
                integration_key='an-integration-key',
                secret_key='valid-secret-key'
            )

        self.client.create_userpass(
            username=username,
            password=password,
            policies=['defaut'],
            mount_point=TEST_AUTH_PATH,
        )
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.auth_userpass(
                    username=username,
                    password=password,
                    mount_point=TEST_AUTH_PATH,
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            # TODO: Add full userpass + MFA integration test case should a mock Duo API server become available and/or
            # if a option for toggling the following SetInsecure func on the vendor code Vault itself uses is exposed:
            # https://github.com/duosecurity/duo_api_golang/blob/master/duoapi.go#L84-L89
            pass
