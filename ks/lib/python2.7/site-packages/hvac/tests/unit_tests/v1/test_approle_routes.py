from unittest import TestCase

import requests_mock
from parameterized import parameterized

from hvac import Client


class TestApproleRoutes(TestCase):
    """Unit tests providing coverage for approle auth backend-related methods/routes."""

    @parameterized.expand([
        ("default mount point", None, "application1"),
        ("custom mount point", "my-approle-path", "application2"),
    ])
    @requests_mock.Mocker()
    def test_create_role(self, test_label, mount_point, role_name, requests_mocker):
        expected_status_code = 204
        mock_url = 'http://localhost:8200/v1/auth/{0}/role/{1}'.format(
            'approle' if mount_point is None else mount_point,
            role_name,
        )
        requests_mocker.register_uri(
            method='POST',
            url=mock_url,
            status_code=expected_status_code,
        )
        client = Client()
        if mount_point is None:
            actual_response = client.create_role(
                role_name=role_name,
            )
        else:
            actual_response = client.create_role(
                role_name=role_name,
                mount_point=mount_point,
            )

        self.assertEquals(
            first=expected_status_code,
            second=actual_response.status_code,
        )

    @parameterized.expand([
        ("default mount point", None, "application1"),
        ("custom mount point", "my-approle-path", "application2"),
    ])
    @requests_mock.Mocker()
    def test_list_roles(self, test_label, mount_point, role_name, requests_mocker):
        expected_status_code = 200
        mock_response = {
            "auth": None,
            "data": {
                "keys": [
                    role_name,
                ]
            },
            "lease_duration": 0,
            "lease_id": "",
            "renewable": False,
            "request_id": "e4c219fb-0a78-2be2-8d3c-b3715dccb920",
            "warnings": None,
            "wrap_info": None
        }
        mock_url = 'http://localhost:8200/v1/auth/{0}/role?list=true'.format(
            'approle' if mount_point is None else mount_point,
        )
        requests_mocker.register_uri(
            method='GET',
            url=mock_url,
            status_code=expected_status_code,
            json=mock_response,
        )
        client = Client()
        if mount_point is None:
            actual_response = client.list_roles()
        else:
            actual_response = client.list_roles(
                mount_point=mount_point,
            )

        # ensure we received our mock response data back successfully
        self.assertEqual(mock_response, actual_response)

    @parameterized.expand([
        ("default mount point", None, "application1", "40b3c82d-12a6-838c-9e74-1f1133867e06"),
        ("custom mount point", "my-approle-path", "application2", "5fs3c82d-12a6-838c-9e74-1f1133867esf"),
    ])
    @requests_mock.Mocker()
    def test_get_role_id(self, test_label, mount_point, role_name, role_id, requests_mocker):
        expected_status_code = 200
        mock_response = {
            "auth": None,
            "data": {
                "role_id": role_id
            },
            "lease_duration": 0,
            "lease_id": "",
            "renewable": False,
            "request_id": "85590a1a-6dd7-de79-01b0-1c285d505bf2",
            "warnings": None,
            "wrap_info": None
        }
        mock_url = 'http://localhost:8200/v1/auth/{0}/role/{1}/role-id'.format(
            'approle' if mount_point is None else mount_point,
            role_name,
        )
        requests_mocker.register_uri(
            method='GET',
            url=mock_url,
            status_code=expected_status_code,
            json=mock_response,
        )
        client = Client()
        if mount_point is None:
            actual_response = client.get_role_id(
                role_name=role_name
            )
        else:
            actual_response = client.get_role_id(
                role_name=role_name,
                mount_point=mount_point
            )

        # ensure we received our mock response data back successfully
        self.assertEqual(
            first=role_id,
            second=actual_response
        )

    @parameterized.expand([
        ("default mount point", None, "application1", "custom-role-id-1"),
        ("custom mount point", "my-approle-path", "application2", "custom-role-id-2"),
    ])
    @requests_mock.Mocker()
    def test_set_role_id(self, test_label, mount_point, role_name, role_id, requests_mocker):
        expected_status_code = 204
        mock_url = 'http://localhost:8200/v1/auth/{0}/role/{1}/role-id'.format(
            'approle' if mount_point is None else mount_point,
            role_name,
        )
        requests_mocker.register_uri(
            method='POST',
            url=mock_url,
            status_code=expected_status_code,
        )
        client = Client()
        if mount_point is None:
            actual_response = client.set_role_id(
                role_name=role_name,
                role_id=role_id
            )
        else:
            actual_response = client.set_role_id(
                role_name=role_name,
                role_id=role_id,
                mount_point=mount_point,
            )

        self.assertEquals(
            first=expected_status_code,
            second=actual_response.status_code,
        )

    @parameterized.expand([
        ("default mount point", None, "application1"),
        ("custom mount point", "my-approle-path", "application2"),
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
            'approle' if mount_point is None else mount_point,
            role_name,
        )
        requests_mocker.register_uri(
            method='GET',
            url=mock_url,
            status_code=expected_status_code,
            json=mock_response,
        )
        client = Client()
        if mount_point is None:
            actual_response = client.get_role(
                role_name=role_name,
            )
        else:
            actual_response = client.get_role(
                role_name=role_name,
                mount_point=mount_point,
            )

        self.assertEquals(
            first=mock_response,
            second=actual_response,
        )

    @parameterized.expand([
        ("default mount point", None, "application1"),
        ("custom mount point", "my-approle-path", "application2"),
    ])
    @requests_mock.Mocker()
    def test_create_role_secret_id(self, test_label, mount_point, role_name, requests_mocker):
        expected_status_code = 200
        mock_response = {
            "auth": None,
            "data": {
                "secret_id": "be78e3ca-f644-b099-3291-e8a6f5985cfe",
                "secret_id_accessor": "b58fd0ee-130c-33bb-5f69-6d4fd1731e5f"
            },
            "lease_duration": 0,
            "lease_id": "",
            "renewable": False,
            "request_id": "2310dc21-0fea-a2de-2d94-bb4edd59f1e9",
            "warnings": None,
            "wrap_info": None
        }

        mock_url = 'http://localhost:8200/v1/auth/{0}/role/{1}/secret-id'.format(
            'approle' if mount_point is None else mount_point,
            role_name,
        )
        requests_mocker.register_uri(
            method='POST',
            url=mock_url,
            status_code=expected_status_code,
            json=mock_response,
        )
        client = Client()
        if mount_point is None:
            actual_response = client.create_role_secret_id(
                role_name=role_name,
            )
        else:
            actual_response = client.create_role_secret_id(
                role_name=role_name,
                mount_point=mount_point,
            )

        self.assertEquals(
            first=mock_response,
            second=actual_response,
        )

    @parameterized.expand([
        ("default mount point", None, "application1", "be78e3ca-f644-b099-3291-e8a6f5985cfe"),
        ("custom mount point", "my-approle-path", "application2", "ce78e3ca-f644-b099-3291-e8a6f5985cfe"),
    ])
    @requests_mock.Mocker()
    def test_get_role_secret_id(self, test_label, mount_point, role_name, secret_id, requests_mocker):
        expected_status_code = 200
        mock_response = {
            "auth": None,
            "data": {
                "SecretIDNumUses": 0,
                "cidr_list": [],
                "creation_time": "2018-06-11T07:33:57.771908-05:00",
                "expiration_time": "0001-01-01T00:00:00Z",
                "last_updated_time": "2018-06-11T07:33:57.771908-05:00",
                "metadata": {},
                "secret_id_accessor": "b58fd0ee-130c-33bb-5f69-6d4fd1731e5f",
                "secret_id_num_uses": 0,
                "secret_id_ttl": 0
            },
            "lease_duration": 0,
            "lease_id": "",
            "renewable": False,
            "request_id": "718a00fa-e76f-f1fc-9b9e-f9c4baa766b3",
            "wrap_info": None
        }

        mock_url = 'http://localhost:8200/v1/auth/{0}/role/{1}/secret-id/lookup'.format(
            'approle' if mount_point is None else mount_point,
            role_name,
        )
        requests_mocker.register_uri(
            method='POST',
            url=mock_url,
            status_code=expected_status_code,
            json=mock_response,
        )
        client = Client()
        if mount_point is None:
            actual_response = client.get_role_secret_id(
                role_name=role_name,
                secret_id=secret_id,
            )
        else:
            actual_response = client.get_role_secret_id(
                role_name=role_name,
                secret_id=secret_id,
                mount_point=mount_point,
            )

        self.assertEquals(
            first=mock_response,
            second=actual_response,
        )

    @parameterized.expand([
        ("default mount point", None, "application1", "be78e3ca-f644-b099-3291-e8a6f5985cfe"),
        ("custom mount point", "my-approle-path", "application2", "ce78e3ca-f644-b099-3291-e8a6f5985cfe"),
    ])
    @requests_mock.Mocker()
    def test_list_role_secrets(self, test_label, mount_point, role_name, secret_id, requests_mocker):
        expected_status_code = 200
        mock_response = {
            "auth": None,
            "data": {
                "keys": [
                    secret_id
                ]
            },
            "lease_duration": 0,
            "lease_id": "",
            "renewable": False,
            "request_id": "eb805845-f6ce-a514-9238-6914664dd601",
            "warnings": None,
            "wrap_info": None
        }

        mock_url = 'http://localhost:8200/v1/auth/{0}/role/{1}/secret-id'.format(
            'approle' if mount_point is None else mount_point,
            role_name,
        )
        requests_mocker.register_uri(
            method='LIST',
            url=mock_url,
            status_code=expected_status_code,
            json=mock_response,
        )
        client = Client()
        if mount_point is None:
            actual_response = client.list_role_secrets(
                role_name=role_name,
            )
        else:
            actual_response = client.list_role_secrets(
                role_name=role_name,
                mount_point=mount_point,
            )

        self.assertEquals(
            first=mock_response,
            second=actual_response,
        )

    @parameterized.expand([
        ("default mount point", None, "application1", "be78e3ca-f644-b099-3291-e8a6f5985cfe"),
        ("custom mount point", "my-approle-path", "application2", "ce78e3ca-f644-b099-3291-e8a6f5985cfe"),
    ])
    @requests_mock.Mocker()
    def test_get_role_secret_id_accessor(self, test_label, mount_point, role_name, secret_id_accessor, requests_mocker):
        expected_status_code = 200
        mock_response = {
            "auth": None,
            "data": {
                "SecretIDNumUses": 0,
                "cidr_list": [],
                "creation_time": "2018-06-11T07:33:57.771908-05:00",
                "expiration_time": "0001-01-01T00:00:00Z",
                "last_updated_time": "2018-06-11T07:33:57.771908-05:00",
                "metadata": {},
                "secret_id_accessor": secret_id_accessor,
                "secret_id_num_uses": 0,
                "secret_id_ttl": 0
            },
            "lease_duration": 0,
            "lease_id": "",
            "renewable": False,
            "request_id": "2c9fcba6-425d-e4c0-45fa-ee90450a3c00",
            "wrap_info": None
        }

        mock_url = 'http://localhost:8200/v1/auth/{0}/role/{1}/secret-id-accessor/lookup'.format(
            'approle' if mount_point is None else mount_point,
            role_name,
        )
        requests_mocker.register_uri(
            method='POST',
            url=mock_url,
            status_code=expected_status_code,
            json=mock_response,
        )
        client = Client()
        if mount_point is None:
            actual_response = client.get_role_secret_id_accessor(
                role_name=role_name,
                secret_id_accessor=secret_id_accessor,
            )
        else:
            actual_response = client.get_role_secret_id_accessor(
                role_name=role_name,
                secret_id_accessor=secret_id_accessor,
                mount_point=mount_point,
            )

        self.assertEquals(
            first=mock_response,
            second=actual_response,
        )

    @parameterized.expand([
        ("default mount point", None, "application1", "be78e3ca-f644-b099-3291-e8a6f5985cfe"),
        ("custom mount point", "my-approle-path", "application2", "ce78e3ca-f644-b099-3291-e8a6f5985cfe"),
    ])
    @requests_mock.Mocker()
    def test_delete_role_secret_id(self, test_label, mount_point, role_name, secret_id, requests_mocker):
        expected_status_code = 204

        mock_url = 'http://localhost:8200/v1/auth/{0}/role/{1}/secret-id/destroy'.format(
            'approle' if mount_point is None else mount_point,
            role_name,
        )
        requests_mocker.register_uri(
            method='POST',
            url=mock_url,
            status_code=expected_status_code,
        )
        client = Client()
        if mount_point is None:
            actual_response = client.delete_role_secret_id(
                role_name=role_name,
                secret_id=secret_id,
            )
        else:
            actual_response = client.delete_role_secret_id(
                role_name=role_name,
                secret_id=secret_id,
                mount_point=mount_point,
            )

        self.assertEquals(
            first=expected_status_code,
            second=actual_response.status_code,
        )

    @parameterized.expand([
        ("default mount point", None, "application1", "be78e3ca-f644-b099-3291-e8a6f5985cfe"),
        ("custom mount point", "my-approle-path", "application2", "ce78e3ca-f644-b099-3291-e8a6f5985cfe"),
    ])
    @requests_mock.Mocker()
    def test_delete_role_secret_id_accessor(self, test_label, mount_point, role_name, secret_id_accessor, requests_mocker):
        expected_status_code = 204

        mock_url = 'http://localhost:8200/v1/auth/{0}/role/{1}/secret-id-accessor/{2}'.format(
            'approle' if mount_point is None else mount_point,
            role_name,
            secret_id_accessor,
        )
        requests_mocker.register_uri(
            method='DELETE',
            url=mock_url,
            status_code=expected_status_code,
        )
        client = Client()
        if mount_point is None:
            actual_response = client.delete_role_secret_id_accessor(
                role_name=role_name,
                secret_id_accessor=secret_id_accessor,
            )
        else:
            actual_response = client.delete_role_secret_id_accessor(
                role_name=role_name,
                secret_id_accessor=secret_id_accessor,
                mount_point=mount_point,
            )

        self.assertEquals(
            first=expected_status_code,
            second=actual_response.status_code,
        )

    @parameterized.expand([
        ("default mount point", None, "application1", "be78e3ca-f644-b099-3291-e8a6f5985cfe"),
        ("custom mount point", "my-approle-path", "application2", "ce78e3ca-f644-b099-3291-e8a6f5985cfe"),
    ])
    @requests_mock.Mocker()
    def test_create_role_custom_secret_id(self, test_label, mount_point, role_name, secret_id, requests_mocker):
        expected_status_code = 200
        mock_response = {
            "auth": None,
            "data": {
                "secret_id": secret_id,
                "secret_id_accessor": "f5cb4b7d-9111-320e-6f24-73bf45d3845d"
            },
            "lease_duration": 0,
            "lease_id": "",
            "renewable": False,
            "request_id": "e7c8b2e1-95e8-cb17-e98a-6c428201f1d5",
            "warnings": None,
            "wrap_info": None
        }
        mock_url = 'http://localhost:8200/v1/auth/{0}/role/{1}/custom-secret-id'.format(
            'approle' if mount_point is None else mount_point,
            role_name,
        )
        requests_mocker.register_uri(
            method='POST',
            url=mock_url,
            status_code=expected_status_code,
            json=mock_response,
        )
        client = Client()
        if mount_point is None:
            actual_response = client.create_role_custom_secret_id(
                role_name=role_name,
                secret_id=secret_id,
            )
        else:
            actual_response = client.create_role_custom_secret_id(
                role_name=role_name,
                secret_id=secret_id,
                mount_point=mount_point,
            )

        self.assertEquals(
            first=mock_response,
            second=actual_response,
        )

    @parameterized.expand([
        ("default mount point", None, "c7f93182-c6b1-4b6a-9dfb-03bdb6df0026", "26089502-b7d3-412a-b3e6-3d44300f9bd1"),
        ("custom mount point", "my-approle-path", "cf6b7c2e-3866-48f8-a764-3bcb5782a85a", "7156c666-0491-4c49-af40-7a97300fbaff"),
    ])
    @requests_mock.Mocker()
    def test_auth_approle(self, test_label, mount_point, role_id, secret_id, requests_mocker):
        expected_status_code = 200
        mock_response = {
            "auth": {
                "accessor": "f8b576f9-9146-4173-e174-40257d58015a",
                "client_token": "3db3d089-7d3c-f531-cd3e-bfe44696a92c",
                "lease_duration": 600,
                "metadata": {
                    "role_name": "application1"
                },
                "policies": [
                    "default"
                ],
                "renewable": True
            },
            "data": None,
            "lease_duration": 0,
            "lease_id": "",
            "renewable": False,
            "request_id": "2eb635ad-a763-926a-9815-4cb4d14a40f9",
            "warnings": None,
            "wrap_info": None
        }
        mock_url = 'http://localhost:8200/v1/auth/{0}/login'.format(
            'approle' if mount_point is None else mount_point,
        )
        requests_mocker.register_uri(
            method='POST',
            url=mock_url,
            status_code=expected_status_code,
            json=mock_response,
        )
        client = Client()
        if mount_point is None:
            actual_response = client.auth_approle(
                role_id=role_id,
                secret_id=secret_id,
            )
        else:
            actual_response = client.auth_approle(
                role_id=role_id,
                secret_id=secret_id,
                mount_point=mount_point,
            )

        self.assertEquals(
            first=mock_response,
            second=actual_response,
        )
