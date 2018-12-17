import logging
from unittest import TestCase

from ldap_test import LdapServer
from parameterized import parameterized, param

from hvac import exceptions
from hvac.tests import utils

LDAP_URL = 'ldap://ldap.hvac.network'
LDAP_GROUP_NAME = 'vault-users'
LDAP_USER_NAME = 'somedude'
LDAP_USER_PASSWORD = 'hvacrox'
LDAP_BASE_DC = 'hvac'
LDAP_BASE_DN = 'dc={dc},dc=network'.format(dc=LDAP_BASE_DC)
LDAP_BIND_DN = 'cn=admin,{base_dn}'.format(base_dn=LDAP_BASE_DN)
LDAP_BIND_PASSWORD = 'notaverygoodpassword'
LDAP_USERS_DN = 'dc=users,{base_dn}'.format(base_dn=LDAP_BASE_DN)
LDAP_GROUPS_OU = 'groups'
LDAP_GROUPS_DN = 'ou={ou},{base_dn}'.format(ou=LDAP_GROUPS_OU, base_dn=LDAP_BASE_DN)
LDAP_LOGIN_USER_DN = 'uid={username},{users_dn}'.format(username=LDAP_USER_NAME, users_dn=LDAP_USERS_DN)
LDAP_ENTRIES = [
    {
        'objectclass': 'domain',
        'dn': LDAP_USERS_DN,
        'attributes': {
            'dc': 'users'
        }
    },
    {
        'objectclass': ['inetOrgPerson', 'posixGroup', 'top'],
        'dn': LDAP_LOGIN_USER_DN,
        'attributes': {
            'uid': LDAP_USER_NAME,
            'userPassword': LDAP_USER_PASSWORD
        }
    },
    {
        'objectclass': 'organizationalUnit',
        'dn': LDAP_GROUPS_DN,
        'attributes': {
            'ou': 'groups',
        }
    },
    {
        'objectclass': 'groupOfNames',
        'dn': 'cn={cn},{groups_dn}'.format(cn=LDAP_GROUP_NAME, groups_dn=LDAP_GROUPS_DN),
        'attributes': {
            'cn': LDAP_GROUP_NAME,
            'member': LDAP_LOGIN_USER_DN,
        }
    },
]


class TestLdap(utils.HvacIntegrationTestCase, TestCase):
    TEST_LDAP_PATH = 'test-ldap'
    ldap_server = None
    mock_server_port = None
    mock_ldap_url = None

    @classmethod
    def setUpClass(cls):
        super(TestLdap, cls).setUpClass()
        logging.getLogger('ldap_test').setLevel(logging.ERROR)

        cls.mock_server_port = utils.get_free_port()
        cls.mock_ldap_url = 'ldap://localhost:{port}'.format(port=cls.mock_server_port)
        cls.ldap_server = LdapServer({
            'port': cls.mock_server_port,
            'bind_dn': LDAP_BIND_DN,
            'password': LDAP_BIND_PASSWORD,
            'base': {
                'objectclass': ['domain'],
                'dn': LDAP_BASE_DN,
                'attributes': {'dc': LDAP_BASE_DC}
            },
            'entries': LDAP_ENTRIES,
        })
        cls.ldap_server.start()

    @classmethod
    def tearDownClass(cls):
        super(TestLdap, cls).tearDownClass()
        cls.ldap_server.stop()

    def setUp(self):
        super(TestLdap, self).setUp()
        if 'ldap/' not in self.client.list_auth_backends():
            self.client.sys.enable_auth_method(
                method_type='ldap',
                path=self.TEST_LDAP_PATH
            )

    def tearDown(self):
        super(TestLdap, self).tearDown()
        self.client.disable_auth_backend(
            mount_point=self.TEST_LDAP_PATH,
        )

    @parameterized.expand([
        ('update url', dict(url=LDAP_URL)),
        ('update binddn', dict(url=LDAP_URL, bind_dn='cn=vault,ou=Users,dc=hvac,dc=network')),
        ('update upn_domain', dict(url=LDAP_URL, upn_domain='hvac.network')),
        ('update certificate', dict(url=LDAP_URL, certificate=utils.load_test_data('server-cert.pem'))),
        ('incorrect tls version', dict(url=LDAP_URL, tls_min_version='cats'), exceptions.InvalidRequest,
         "invalid 'tls_min_version'"),
    ])
    def test_configure(self, test_label, parameters, raises=None, exception_message=''):
        parameters.update({
            'user_dn': LDAP_USERS_DN,
            'group_dn': LDAP_GROUPS_DN,
            'mount_point': self.TEST_LDAP_PATH,
        })
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.auth.ldap.configure(**parameters)
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            expected_status_code = 204
            configure_response = self.client.auth.ldap.configure(**parameters)
            self.assertEqual(
                first=expected_status_code,
                second=configure_response.status_code
            )

            read_config_response = self.client.auth.ldap.read_configuration(
                mount_point=self.TEST_LDAP_PATH,
            )
            for parameter, argument in parameters.items():
                if parameter == 'mount_point':
                    continue
                self.assertIn(
                    member=argument,
                    container=read_config_response['data'].values(),
                )

    def test_read_configuration(self):
        response = self.client.auth.ldap.read_configuration(
            mount_point=self.TEST_LDAP_PATH,
        )
        self.assertIn(
            member='data',
            container=response,
        )

    @parameterized.expand([
        ('no policies', 'cats'),
        ('policies as list', 'cats', ['purr-policy']),
        ('policies as invalid type', 'cats', 'purr-policy', exceptions.ParamValidationError, '"policies" argument must be an instance of list'),
    ])
    def test_create_or_update_group(self, test_label, name, policies=None, raises=None, exception_message=''):
        expected_status_code = 204
        if raises:
            with self.assertRaises(raises) as cm:
                create_response = self.client.auth.ldap.create_or_update_group(
                    name=name,
                    policies=policies,
                    mount_point=self.TEST_LDAP_PATH,
                )
            if exception_message is not None:
                self.assertIn(
                    member=exception_message,
                    container=str(cm.exception),
                )
        else:
            create_response = self.client.auth.ldap.create_or_update_group(
                name=name,
                policies=policies,
                mount_point=self.TEST_LDAP_PATH,
            )
            self.assertEqual(
                first=expected_status_code,
                second=create_response.status_code
            )

    @parameterized.expand([
        ('read configured groups', 'cats'),
        ('non-existent groups', 'cats', False, exceptions.InvalidPath),
    ])
    def test_list_groups(self, test_label, name, configure_first=True, raises=None, exception_message=None):
        if configure_first:
            self.client.auth.ldap.create_or_update_group(
                name=name,
                mount_point=self.TEST_LDAP_PATH,
            )
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.auth.ldap.list_groups(
                    mount_point=self.TEST_LDAP_PATH,
                )
            if exception_message is not None:
                self.assertIn(
                    member=exception_message,
                    container=str(cm.exception),
                )
        else:
            list_groups_response = self.client.auth.ldap.list_groups(
                mount_point=self.TEST_LDAP_PATH,
            )
            # raise Exception(list_groups_response)
            self.assertDictEqual(
                d1=dict(keys=[name]),
                d2=list_groups_response['data'],
            )

    @parameterized.expand([
        ('read configured group', 'cats'),
        ('non-existent group', 'cats', False, exceptions.InvalidPath),
    ])
    def test_read_group(self, test_label, name, configure_first=True, raises=None, exception_message=None):
        if configure_first:
            self.client.auth.ldap.create_or_update_group(
                name=name,
                mount_point=self.TEST_LDAP_PATH,
            )
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.auth.ldap.read_group(
                    name=name,
                    mount_point=self.TEST_LDAP_PATH,
                )
            if exception_message is not None:
                self.assertIn(
                    member=exception_message,
                    container=str(cm.exception),
                )
        else:
            read_group_response = self.client.auth.ldap.read_group(
                name=name,
                mount_point=self.TEST_LDAP_PATH,
            )
            self.assertIn(
                member='policies',
                container=read_group_response['data'],
            )

    @parameterized.expand([
        ('no policies or groups', 'cats'),
        ('policies as list', 'cats', ['purr-policy']),
        ('policies as invalid type', 'cats', 'purr-policy', None, exceptions.ParamValidationError, '"policies" argument must be an instance of list'),
        ('no groups', 'cats', ['purr-policy']),
        ('groups as list', 'cats', None, ['meow-group']),
        ('groups as invalid type', 'cats', None, 'meow-group', exceptions.ParamValidationError, '"groups" argument must be an instance of list'),
    ])
    def test_create_or_update_user(self, test_label, username, policies=None, groups=None, raises=None, exception_message=''):
        expected_status_code = 204
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.auth.ldap.create_or_update_user(
                    username=username,
                    policies=policies,
                    groups=groups,
                    mount_point=self.TEST_LDAP_PATH,
                )
            if exception_message is not None:
                self.assertIn(
                    member=exception_message,
                    container=str(cm.exception),
                )
        else:
            create_response = self.client.auth.ldap.create_or_update_user(
                username=username,
                policies=policies,
                groups=groups,
                mount_point=self.TEST_LDAP_PATH,
            )
            self.assertEqual(
                first=expected_status_code,
                second=create_response.status_code
            )

    @parameterized.expand([
        ('read configured group', 'cats'),
        ('non-existent group', 'cats', False, exceptions.InvalidPath),
    ])
    def test_delete_group(self, test_label, name, configure_first=True, raises=None, exception_message=None):
        if configure_first:
            self.client.auth.ldap.create_or_update_group(
                name=name,
                mount_point=self.TEST_LDAP_PATH,
            )
        expected_status_code = 204
        delete_group_response = self.client.auth.ldap.delete_group(
            name=name,
            mount_point=self.TEST_LDAP_PATH,
        )
        self.assertEqual(
            first=expected_status_code,
            second=delete_group_response.status_code
        )

    @parameterized.expand([
        ('read configured user', 'cats'),
        ('non-existent user', 'cats', False, exceptions.InvalidPath),
    ])
    def test_list_users(self, test_label, username, configure_first=True, raises=None, exception_message=None):
        if configure_first:
            self.client.auth.ldap.create_or_update_user(
                username=username,
                mount_point=self.TEST_LDAP_PATH,
            )
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.auth.ldap.list_users(
                    mount_point=self.TEST_LDAP_PATH,
                )
            if exception_message is not None:
                self.assertIn(
                    member=exception_message,
                    container=str(cm.exception),
                )
        else:
            list_users_response = self.client.auth.ldap.list_users(
                mount_point=self.TEST_LDAP_PATH,
            )
            self.assertDictEqual(
                d1=dict(keys=[username]),
                d2=list_users_response['data'],
            )

    @parameterized.expand([
        ('read configured user', 'cats'),
        ('non-existent user', 'cats', False, exceptions.InvalidPath),
    ])
    def test_read_user(self, test_label, username, configure_first=True, raises=None, exception_message=None):
        if configure_first:
            self.client.auth.ldap.create_or_update_user(
                username=username,
                mount_point=self.TEST_LDAP_PATH,
            )
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.auth.ldap.read_user(
                    username=username,
                    mount_point=self.TEST_LDAP_PATH,
                )
            if exception_message is not None:
                self.assertIn(
                    member=exception_message,
                    container=str(cm.exception),
                )
        else:
            read_user_response = self.client.auth.ldap.read_user(
                username=username,
                mount_point=self.TEST_LDAP_PATH,
            )
            self.assertIn(
                member='policies',
                container=read_user_response['data'],
            )

    @parameterized.expand([
        ('read configured user', 'cats'),
        ('non-existent user', 'cats', False, exceptions.InvalidPath),
    ])
    def test_delete_user(self, test_label, username, configure_first=True, raises=None, exception_message=None):
        if configure_first:
            self.client.auth.ldap.create_or_update_user(
                username=username,
                mount_point=self.TEST_LDAP_PATH,
            )
        expected_status_code = 204
        delete_user_response = self.client.auth.ldap.delete_user(
            username=username,
            mount_point=self.TEST_LDAP_PATH,
        )
        self.assertEqual(
            first=expected_status_code,
            second=delete_user_response.status_code
        )

    @parameterized.expand([
        param(
            label='working creds with policy'
        ),
        param(
            label='invalid creds',
            username='not_your_dude_pal',
            password='some other dudes password',
            attach_policy=False,
            raises=exceptions.InvalidRequest,
        ),
        # The following two test cases cover either side of the associated changelog entry for LDAP auth here:
        # https://github.com/hashicorp/vault/blob/master/CHANGELOG.md#0103-june-20th-2018
        param(
            label='working creds no membership with Vault version >= 0.10.3',
            attach_policy=False,
            skip_due_to_vault_version=utils.skip_if_vault_version_lt('0.10.3'),
        ),
        param(
            label='working creds no membership with Vault version < 0.10.3',
            attach_policy=False,
            raises=exceptions.InvalidRequest,
            exception_message='user is not a member of any authorized group',
            skip_due_to_vault_version=utils.skip_if_vault_version_ge('0.10.3'),
        ),
    ])
    def test_login(self, label, username=LDAP_USER_NAME, password=LDAP_USER_PASSWORD, attach_policy=True, raises=None,
                   exception_message='', skip_due_to_vault_version=False):
        if skip_due_to_vault_version:
            self.skipTest(reason='test case does not apply to Vault version under test')

        test_policy_name = 'test-ldap-policy'
        self.client.auth.ldap.configure(
            url=self.mock_ldap_url,
            bind_dn=self.ldap_server.config['bind_dn'],
            bind_pass=self.ldap_server.config['password'],
            user_dn=LDAP_USERS_DN,
            user_attr='uid',
            group_dn=LDAP_GROUPS_DN,
            group_attr='cn',
            insecure_tls=True,
            mount_point=self.TEST_LDAP_PATH,
        )

        if attach_policy:
            self.prep_policy(test_policy_name)
            self.client.auth.ldap.create_or_update_group(
                name=LDAP_GROUP_NAME,
                policies=[test_policy_name],
                mount_point=self.TEST_LDAP_PATH,
            )

        if raises:
            with self.assertRaises(raises) as cm:
                self.client.auth.ldap.login(
                    username=username,
                    password=password,
                    mount_point=self.TEST_LDAP_PATH,
                )
            if exception_message is not None:
                self.assertIn(
                    member=exception_message,
                    container=str(cm.exception),
                )
        else:
            login_response = self.client.auth.ldap.login(
                username=username,
                password=password,
                mount_point=self.TEST_LDAP_PATH,
            )
            self.assertDictEqual(
                d1=dict(username=username),
                d2=login_response['auth']['metadata'],
            )
            self.assertEqual(
                first=login_response['auth']['client_token'],
                second=self.client.token,
            )
            if attach_policy:
                expected_policies = ['default', test_policy_name]
            else:
                expected_policies = ['default']
            self.assertEqual(
                first=expected_policies,
                second=login_response['auth']['policies']
            )
