from unittest import TestCase

import requests_mock
from parameterized import parameterized

from hvac import Client


class TestKubernetesMethods(TestCase):
    """Unit tests providing coverage for Kubernetes auth backend-related methods/routes."""

    @parameterized.expand([
        ("default mount point", None, '127.0.0.1:80', ['test_key']),
        ("custom mount point", "k8s", 'some_k8s_host.com', ['test_key']),
    ])
    @requests_mock.Mocker()
    def test_create_kubernetes_configuration(self, test_label, mount_point, kubernetes_host, pem_keys, requests_mocker):
        expected_status_code = 204
        mock_url = 'http://localhost:8200/v1/auth/{0}/config'.format(
            'kubernetes' if mount_point is None else mount_point,
        )
        requests_mocker.register_uri(
            method='POST',
            url=mock_url,
            status_code=expected_status_code,
        )
        client = Client()

        test_arguments = dict(
            kubernetes_host=kubernetes_host,
            pem_keys=pem_keys,
        )
        if mount_point:
            test_arguments['mount_point'] = mount_point

        actual_response = client.create_kubernetes_configuration(**test_arguments)

        self.assertEquals(
            first=expected_status_code,
            second=actual_response.status_code,
        )

    @parameterized.expand([
        ("default mount point", None),
        ("custom mount point", "k8s"),
    ])
    @requests_mock.Mocker()
    def test_get_kubernetes_configuration(self, test_label, mount_point, requests_mocker):
        expected_status_code = 200
        mock_response = {
            'auth': None,
            'data': {
                'kubernetes_ca_cert': '',
                'kubernetes_host': '127.0.0.1:80',
                'pem_keys': ['some key'],
                'token_reviewer_jwt': ''
            },
            'lease_duration': 0,
            'lease_id': '',
            'renewable': False,
            'request_id': '12687b5f-b4f5-2ba4-aae2-2a8d7e53ca55',
            'warnings': None,
            'wrap_info': None
        }
        mock_url = 'http://localhost:8200/v1/auth/{0}/config'.format(
            'kubernetes' if mount_point is None else mount_point,
        )
        requests_mocker.register_uri(
            method='GET',
            url=mock_url,
            status_code=expected_status_code,
            json=mock_response,
        )
        client = Client()

        test_arguments = dict()
        if mount_point:
            test_arguments['mount_point'] = mount_point

        actual_response = client.get_kubernetes_configuration(**test_arguments)

        self.assertEquals(
            first=mock_response,
            second=actual_response,
        )

    @parameterized.expand([
        ("default mount point", None, "application1", '*', 'some-namespace'),
        ("custom mount point", "k8s", "application2", 'some-service-account', '*'),
    ])
    @requests_mock.Mocker()
    def test_create_role(self, test_label, mount_point, role_name, bound_service_account_names, bound_service_account_namespaces, requests_mocker):
        expected_status_code = 204
        mock_url = 'http://localhost:8200/v1/auth/{0}/role/{1}'.format(
            'kubernetes' if mount_point is None else mount_point,
            role_name,
        )
        requests_mocker.register_uri(
            method='POST',
            url=mock_url,
            status_code=expected_status_code,
        )
        client = Client()

        test_arguments = dict(
            name=role_name,
            bound_service_account_names=bound_service_account_names,
            bound_service_account_namespaces=bound_service_account_namespaces,
        )
        if mount_point:
            test_arguments['mount_point'] = mount_point
        actual_response = client.create_kubernetes_role(**test_arguments)

        self.assertEquals(
            first=expected_status_code,
            second=actual_response.status_code,
        )

    @parameterized.expand([
        ("default mount point", None, "application1"),
        ("custom mount point", "k8s", "application2"),
    ])
    @requests_mock.Mocker()
    def test_get_role(self, test_label, mount_point, role_name, requests_mocker):
        expected_status_code = 200
        mock_response = {
            "auth": None,
            "data": {
                "bind_secret_id": True,
                "bound_cidr_list": "",
                "period": 0,
                "policies": [
                    "default"
                ],
                "secret_id_num_uses": 0,
                "secret_id_ttl": 0,
                "token_max_ttl": 900,
                "token_num_uses": 0,
                "token_ttl": 600
            },
            "lease_duration": 0,
            "lease_id": "",
            "renewable": False,
            "request_id": "0aab655f-ecd2-b3d4-3817-35b5bdfd3f28",
            "warnings": None,
            "wrap_info": None
        }
        mock_url = 'http://localhost:8200/v1/auth/{0}/role/{1}'.format(
            'kubernetes' if mount_point is None else mount_point,
            role_name,
        )
        requests_mocker.register_uri(
            method='GET',
            url=mock_url,
            status_code=expected_status_code,
            json=mock_response,
        )
        client = Client()

        test_arguments = dict(
            name=role_name,
        )
        if mount_point:
            test_arguments['mount_point'] = mount_point

        actual_response = client.get_kubernetes_role(**test_arguments)

        self.assertEquals(
            first=mock_response,
            second=actual_response,
        )

    @parameterized.expand([
        ("default mount point", None, ['test-role-1', 'test-role-2']),
        ("custom mount point", "k8s", ['test-role']),
    ])
    @requests_mock.Mocker()
    def test_list_kubernetes_roles(self, test_label, mount_point, role_names, requests_mocker):
        expected_status_code = 200
        mock_response = {
            "auth": None,
            "data": {
                "keys": role_names,
            },
            "lease_duration": 0,
            "lease_id": "",
            "renewable": False,
            "request_id": "e4c219fb-0a78-2be2-8d3c-b3715dccb920",
            "warnings": None,
            "wrap_info": None
        }
        mock_url = 'http://localhost:8200/v1/auth/{0}/role?list=true'.format(
            'kubernetes' if mount_point is None else mount_point,
        )
        requests_mocker.register_uri(
            method='GET',
            url=mock_url,
            status_code=expected_status_code,
            json=mock_response,
        )
        client = Client()

        test_arguments = dict()
        if mount_point:
            test_arguments['mount_point'] = mount_point
        actual_response = client.list_kubernetes_roles(**test_arguments)

        # ensure we received our mock response data back successfully
        self.assertEqual(mock_response, actual_response)

    @parameterized.expand([
        ("default mount point", None, "application1"),
        ("custom mount point", "k8s", "application2"),
    ])
    @requests_mock.Mocker()
    def test_delete_kubernetes_role(self, test_label, mount_point, role_name, requests_mocker):
        expected_status_code = 204
        mock_url = 'http://localhost:8200/v1/auth/{0}/role/{1}'.format(
            'kubernetes' if mount_point is None else mount_point,
            role_name,
        )
        requests_mocker.register_uri(
            method='DELETE',
            url=mock_url,
            status_code=expected_status_code,
        )
        client = Client()

        test_arguments = dict(
            role=role_name,
        )
        if mount_point:
            test_arguments['mount_point'] = mount_point

        actual_response = client.delete_kubernetes_role(**test_arguments)

        self.assertEquals(
            first=expected_status_code,
            second=actual_response.status_code,
        )

    @parameterized.expand([
        ("default mount point", "custom_role", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9", None),
        ("custom mount point", "custom_role", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9", "gcp-not-default")
    ])
    @requests_mock.Mocker()
    def test_auth_kubernetes(self, test_label, test_role, test_jwt, mount_point, requests_mocker):
        mock_response = {
            'auth': {
                'accessor': 'accessor-1234-5678-9012-345678901234',
                'client_token': 'cltoken-1234-5678-9012-345678901234',
                'lease_duration': 10000,
                'metadata': {
                    'role': 'custom_role',
                    'service_account_name': 'vault-auth',
                    'service_account_namespace': 'default',
                    'service_account_secret_name': 'vault-auth-token-pd21c',
                    'service_account_uid': 'aa9aa8ff-98d0-11e7-9bb7-0800276d99bf'
                },
                'policies': [
                    'default',
                    'custom_role'
                ],
                'renewable': True
            },
            'data': None,
            'lease_duration': 0,
            'lease_id': '',
            'renewable': False,
            'request_id': 'requesti-1234-5678-9012-345678901234',
            'warnings': [],
            'wrap_info': None
        }
        mock_url = 'http://localhost:8200/v1/auth/{0}/login'.format(
                'kubernetes' if mount_point is None else mount_point)
        requests_mocker.register_uri(
            method='POST',
            url=mock_url,
            json=mock_response
        )
        client = Client()
        test_arguments = dict(
            role=test_role,
            jwt=test_jwt,
        )
        if mount_point:
            test_arguments['mount_point'] = mount_point
        actual_response = client.auth_kubernetes(**test_arguments)

        # ensure we received our mock response data back successfully
        self.assertEqual(mock_response, actual_response)
