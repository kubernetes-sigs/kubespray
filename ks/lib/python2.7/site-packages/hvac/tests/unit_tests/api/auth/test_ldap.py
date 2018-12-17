from unittest import TestCase

import requests_mock
from parameterized import parameterized

from hvac.adapters import Request
from hvac.api.auth_methods import Ldap
from hvac.api.auth_methods.ldap import DEFAULT_MOUNT_POINT


class TestLdap(TestCase):

    @parameterized.expand([
        ("default mount point", DEFAULT_MOUNT_POINT),
        ("custom mount point", 'other-ldap-tree'),
    ])
    @requests_mock.Mocker()
    def test_configure(self, test_label, mount_point, requests_mocker):
        expected_status_code = 204
        mock_url = 'http://localhost:8200/v1/auth/{mount_point}/config'.format(
            mount_point=mount_point,
        )
        requests_mocker.register_uri(
            method='POST',
            url=mock_url,
            status_code=expected_status_code,
        )
        ldap = Ldap(adapter=Request())
        response = ldap.configure(
            user_dn='dc=users,cn=hvac,cn=network',
            group_dn='ou=groups,cn=hvac,cn=network',
            url='ldaps://ldap.hvac.network',
            mount_point=mount_point,
        )
        self.assertEqual(
            first=expected_status_code,
            second=response.status_code,
        )

    @parameterized.expand([
        ("default mount point", DEFAULT_MOUNT_POINT),
        ("custom mount point", 'other-ldap-tree'),
    ])
    @requests_mock.Mocker()
    def test_read_configuration(self, test_label, mount_point, requests_mocker):
        expected_status_code = 200
        mock_response = {
            'lease_id': '',
            'warnings': None,
            'wrap_info': None,
            'auth': None,
            'lease_duration': 0,

            'request_id': 'dd7c3635-8e1c-d454-7381-bf11970fe8de',
            'data': {
                'binddn': '',
                'certificate': '',
                'deny_null_bind': True,
                'starttls': False,
                'case_sensitive_names': False,
                'userattr': '',
                'insecure_tls': False,
                'userdn': '',
                'url': 'ldap://ldap.hvac.network',
                'groupfilter': '',
                'tls_max_version': 'tls12',
                'tls_min_version': 'tls12',
                'groupdn': '',
                'groupattr': '',
                'upndomain': '',
                'discoverdn': False
            },
            'renewable': False
        }
        mock_url = 'http://localhost:8200/v1/auth/{mount_point}/config'.format(
            mount_point=mount_point,
        )
        requests_mocker.register_uri(
            method='GET',
            url=mock_url,
            status_code=expected_status_code,
            json=mock_response,
        )
        ldap = Ldap(adapter=Request())
        response = ldap.read_configuration(
            mount_point=mount_point,
        )
        self.assertEqual(
            first=mock_response,
            second=response,
        )

    @parameterized.expand([
        ("default mount point", DEFAULT_MOUNT_POINT),
        ("custom mount point", 'other-ldap-tree'),
    ])
    @requests_mock.Mocker()
    def test_create_or_update_group(self, test_label, mount_point, requests_mocker):
        expected_status_code = 204
        group_name = 'hvac'
        mock_url = 'http://localhost:8200/v1/auth/{mount_point}/groups/{group_name}'.format(
            mount_point=mount_point,
            group_name=group_name,
        )
        requests_mocker.register_uri(
            method='POST',
            url=mock_url,
            status_code=expected_status_code,
        )
        ldap = Ldap(adapter=Request())
        response = ldap.create_or_update_group(
            name=group_name,
            mount_point=mount_point,
        )
        self.assertEqual(
            first=expected_status_code,
            second=response.status_code,
        )

    @parameterized.expand([
        ("default mount point", DEFAULT_MOUNT_POINT),
        ("custom mount point", 'other-ldap-tree'),
    ])
    @requests_mock.Mocker()
    def test_list_groups(self, test_label, mount_point, requests_mocker):
        expected_status_code = 200
        mock_response = {
            'lease_id': '',
            'warnings': None,
            'wrap_info': None,
            'auth': None,
            'lease_duration': 0,
            'request_id': '89144def-b675-4c8a-590c-4f2ad4f1fae7',
            'data': {
                'keys': ['cats']
            },
            'renewable': False
        }
        mock_url = 'http://localhost:8200/v1/auth/{mount_point}/groups'.format(
            mount_point=mount_point,
        )
        requests_mocker.register_uri(
            method='LIST',
            url=mock_url,
            status_code=expected_status_code,
            json=mock_response,
        )
        ldap = Ldap(adapter=Request())
        response = ldap.list_groups(
            mount_point=mount_point,
        )
        self.assertEqual(
            first=mock_response,
            second=response,
        )

    @parameterized.expand([
        ("default mount point", DEFAULT_MOUNT_POINT),
        ("custom mount point", 'other-ldap-tree'),
    ])
    @requests_mock.Mocker()
    def test_read_group(self, test_label, mount_point, requests_mocker):
        expected_status_code = 200
        group_name = 'hvac'
        mock_response = {
            'lease_id': '',
            'warnings': None,
            'wrap_info': None,
            'auth': None,
            'lease_duration': 0,
            'request_id': '448bc87c-e948-ac5f-907c-9b01fb9d26c6',
            'data': {
                'policies': []
            },
            'renewable': False
        }
        mock_url = 'http://localhost:8200/v1/auth/{mount_point}/groups/{name}'.format(
            mount_point=mount_point,
            name=group_name,
        )
        requests_mocker.register_uri(
            method='GET',
            url=mock_url,
            status_code=expected_status_code,
            json=mock_response,
        )
        ldap = Ldap(adapter=Request())
        response = ldap.read_group(
            name=group_name,
            mount_point=mount_point,
        )
        self.assertEqual(
            first=mock_response,
            second=response,
        )

    @parameterized.expand([
        ("default mount point", DEFAULT_MOUNT_POINT),
        ("custom mount point", 'other-ldap-tree'),
    ])
    @requests_mock.Mocker()
    def test_delete_group(self, test_label, mount_point, requests_mocker):
        expected_status_code = 204
        group_name = 'hvac'
        mock_url = 'http://localhost:8200/v1/auth/{mount_point}/groups/{name}'.format(
            mount_point=mount_point,
            name=group_name,
        )
        requests_mocker.register_uri(
            method='DELETE',
            url=mock_url,
            status_code=expected_status_code,
        )
        ldap = Ldap(adapter=Request())
        response = ldap.delete_group(
            name=group_name,
            mount_point=mount_point,
        )
        self.assertEqual(
            first=expected_status_code,
            second=response.status_code,
        )

    @parameterized.expand([
        ("default mount point", DEFAULT_MOUNT_POINT),
        ("custom mount point", 'other-ldap-tree'),
    ])
    @requests_mock.Mocker()
    def test_create_or_update_user(self, test_label, mount_point, requests_mocker):
        expected_status_code = 204
        username = 'somedude'
        mock_url = 'http://localhost:8200/v1/auth/{mount_point}/users/{name}'.format(
            mount_point=mount_point,
            name=username,
        )
        requests_mocker.register_uri(
            method='POST',
            url=mock_url,
            status_code=expected_status_code,
        )
        ldap = Ldap(adapter=Request())
        response = ldap.create_or_update_user(
            username=username,
            mount_point=mount_point,
        )
        self.assertEqual(
            first=expected_status_code,
            second=response.status_code,
        )

    @parameterized.expand([
        ("default mount point", DEFAULT_MOUNT_POINT),
        ("custom mount point", 'other-ldap-tree'),
    ])
    @requests_mock.Mocker()
    def test_list_users(self, test_label, mount_point, requests_mocker):
        expected_status_code = 200
        mock_response = {
            'lease_id': '',
            'warnings': None,
            'wrap_info': None,
            'auth': None,
            'lease_duration': 0,
            'request_id': '0c34cc02-2f75-7deb-a531-33cf7434a729',
            'data': {
                'keys': ['somedude']
            },
            'renewable': False
        }
        mock_url = 'http://localhost:8200/v1/auth/{mount_point}/users'.format(
            mount_point=mount_point,
        )
        requests_mocker.register_uri(
            method='LIST',
            url=mock_url,
            status_code=expected_status_code,
            json=mock_response,
        )
        ldap = Ldap(adapter=Request())
        response = ldap.list_users(
            mount_point=mount_point,
        )
        self.assertEqual(
            first=mock_response,
            second=response,
        )

    @parameterized.expand([
        ("default mount point", DEFAULT_MOUNT_POINT),
        ("custom mount point", 'other-ldap-tree'),
    ])
    @requests_mock.Mocker()
    def test_read_user(self, test_label, mount_point, requests_mocker):
        expected_status_code = 200
        username = 'somedude'
        mock_response = {
            'lease_id': '',
            'warnings': None,
            'wrap_info': None,
            'auth': None,
            'lease_duration': 0,
            'request_id': 'c39914d5-70c1-b585-c6bd-ac8f0dcdf997',
            'data': {
                'policies': [],
                'groups': ''
            },
            'renewable': False
        }
        mock_url = 'http://localhost:8200/v1/auth/{mount_point}/users/{username}'.format(
            mount_point=mount_point,
            username=username,
        )
        requests_mocker.register_uri(
            method='GET',
            url=mock_url,
            status_code=expected_status_code,
            json=mock_response,
        )
        ldap = Ldap(adapter=Request())
        response = ldap.read_user(
            mount_point=mount_point,
            username=username,
        )
        self.assertEqual(
            first=mock_response,
            second=response,
        )

    @parameterized.expand([
        ("default mount point", DEFAULT_MOUNT_POINT),
        ("custom mount point", 'other-ldap-tree'),
    ])
    @requests_mock.Mocker()
    def test_delete_user(self, test_label, mount_point, requests_mocker):
        expected_status_code = 204
        username = 'somedude'
        mock_url = 'http://localhost:8200/v1/auth/{mount_point}/users/{username}'.format(
            mount_point=mount_point,
            username=username,
        )
        requests_mocker.register_uri(
            method='DELETE',
            url=mock_url,
            status_code=expected_status_code,
        )
        ldap = Ldap(adapter=Request())
        response = ldap.delete_user(
            username=username,
            mount_point=mount_point,
        )
        self.assertEqual(
            first=expected_status_code,
            second=response.status_code,
        )

    @parameterized.expand([
        ("default mount point", DEFAULT_MOUNT_POINT),
        ("custom mount point", 'other-ldap-tree'),
    ])
    @requests_mock.Mocker()
    def test_login(self, test_label, mount_point, requests_mocker):
        expected_status_code = 200
        username = 'somedude'
        mock_response = {
            'lease_id': '',
            'warnings': None,
            'wrap_info': None,
            'auth': {
                'entity_id': '5bc030bc-2000-1176-aafb-82747ae9c874',
                'lease_duration': 2764800,
                'policies': [
                    'default',
                    'test-ldap-policy'
                ],
                'client_token': '5a01125e-d823-578e-86c8-049bea022b9e',
                'accessor': '71f512de-18ab-af6e-02f7-e37b3aa48780',
                'renewable': True,
                'metadata': {'username': 'somedude'}
            },
            'lease_duration': 0,
            'request_id': 'c7a85e6c-fb1f-1d97-83a1-63746cb65551',
            'data': {},
            'renewable': False
        }
        mock_url = 'http://localhost:8200/v1/auth/{mount_point}/login/{username}'.format(
            mount_point=mount_point,
            username=username,
        )
        requests_mocker.register_uri(
            method='POST',
            url=mock_url,
            status_code=expected_status_code,
            json=mock_response,
        )
        ldap = Ldap(adapter=Request())
        response = ldap.login(
            mount_point=mount_point,
            username=username,
            password='averynicepassword'
        )
        self.assertEqual(
            first=mock_response,
            second=response,
        )
