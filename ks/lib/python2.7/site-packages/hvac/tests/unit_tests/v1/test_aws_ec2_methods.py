from unittest import TestCase

import requests_mock
from parameterized import parameterized

from hvac import Client


class TestAwsEc2Methods(TestCase):
    """Unit tests providing coverage for AWS (EC2) auth backend-related methods/routes."""

    @parameterized.expand([
        ("default mount point", None),
        ("custom mount point", 'aws-ec2'),
    ])
    @requests_mock.Mocker()
    def test_auth_ec2(self, test_label, mount_point, requests_mocker):
        mock_response = {
            'auth': {
                'accessor': 'accessor-1234-5678-9012-345678901234',
                'client_token': 'cltoken-1234-5678-9012-345678901234',
                'lease_duration': 10000,
                'metadata': {
                    'account_id': '12345678912',
                    'ami_id': 'ami-someami',
                    'instance_id': 'i-instanceid',
                    'nonce': 'thenonce-1234-5678-9012-345678901234',
                    'region': 'us-east-1',
                    'role': 'custom_role',
                    'role_tag_max_ttl': '0s'
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
            'aws-ec2' if mount_point is None else mount_point
        )
        requests_mocker.register_uri(
            method='POST',
            url=mock_url,
            json=mock_response
        )
        client = Client()

        if mount_point is None:
            actual_response = client.auth_ec2(
                pkcs7='mock_pcks7'
            )
        else:
            actual_response = client.auth_ec2(
                pkcs7='mock_pcks7',
                mount_point=mount_point
            )

        # ensure we received our mock response data back successfully
        self.assertEqual(mock_response, actual_response)

    @parameterized.expand([
        ("default mount point", None),
        ("custom mount point", 'aws-ec2'),
    ])
    @requests_mock.Mocker()
    def test_create_vault_ec2_client_configuration(self, test_label, mount_point, requests_mocker):
        test_access_key = 'AKIAABCDEFGUE1234567'
        test_secret_key = 'thisisasecretyall'
        expected_status_code = 204
        mock_url = 'http://localhost:8200/v1/auth/{0}/config/client'.format(
            'aws-ec2' if mount_point is None else mount_point
        )
        requests_mocker.register_uri(
            method='POST',
            url=mock_url,
            status_code=expected_status_code,
        )
        client = Client()

        if mount_point is None:
            actual_response = client.create_vault_ec2_client_configuration(
                access_key=test_access_key,
                secret_key=test_secret_key,
            )
        else:
            actual_response = client.create_vault_ec2_client_configuration(
                access_key=test_access_key,
                secret_key=test_secret_key,
                mount_point=mount_point
            )

        self.assertEqual(
            first=expected_status_code,
            second=actual_response.status_code
        )

    @parameterized.expand([
        ("default mount point", None),
        ("custom mount point", 'aws-ec2'),
    ])
    @requests_mock.Mocker()
    def test_get_vault_ec2_client_configuration(self, test_label, mount_point, requests_mocker):
        mock_response = {
          "data": {
            "secret_key": "vCtSM8ZUEQ3mOFVlYPBQkf2sO6F/W7a5TVzrl3Oj",
            "access_key": "VKIAJBRHKH6EVTTNXDHA",
            "endpoint": "",
            "iam_endpoint": "",
            "sts_endpoint": "",
            "iam_server_id_header_value": ""
          }
        }
        expected_status_code = 200
        mock_url = 'http://localhost:8200/v1/auth/{0}/config/client'.format(
            'aws-ec2' if mount_point is None else mount_point
        )
        requests_mocker.register_uri(
            method='GET',
            url=mock_url,
            json=mock_response,
            status_code=expected_status_code,
        )
        client = Client()

        if mount_point is None:
            actual_response = client.get_vault_ec2_client_configuration()
        else:
            actual_response = client.get_vault_ec2_client_configuration(
                mount_point=mount_point
            )

        self.assertEqual(
            first=mock_response,
            second=actual_response,
        )

    @parameterized.expand([
        ("default mount point", None),
        ("custom mount point", 'aws-ec2'),
    ])
    @requests_mock.Mocker()
    def test_delete_vault_ec2_client_configuration(self, test_label, mount_point, requests_mocker):
        expected_status_code = 204
        mock_url = 'http://localhost:8200/v1/auth/{0}/config/client'.format(
            'aws-ec2' if mount_point is None else mount_point
        )
        requests_mocker.register_uri(
            method='DELETE',
            url=mock_url,
            status_code=expected_status_code,
        )
        client = Client()

        if mount_point is None:
            actual_response = client.delete_vault_ec2_client_configuration()
        else:
            actual_response = client.delete_vault_ec2_client_configuration(
                mount_point=mount_point
            )

        self.assertEqual(
            first=expected_status_code,
            second=actual_response.status_code,
        )

    @parameterized.expand([
        ("default mount point", None, 'my-cool-cert-1'),
        ("custom mount point", 'aws-ec2', 'my-cool-cert-2'),
    ])
    @requests_mock.Mocker()
    def test_create_vault_ec2_certificate_configuration(self, test_label, mount_point, cert_name, requests_mocker):
        test_cert_info = 'this is some test cert info'
        expected_status_code = 204
        mock_url = 'http://localhost:8200/v1/auth/{0}/config/certificate/{1}'.format(
            'aws-ec2' if mount_point is None else mount_point,
            cert_name,
        )
        requests_mocker.register_uri(
            method='POST',
            url=mock_url,
            status_code=expected_status_code,
        )
        client = Client()

        if mount_point is None:
            actual_response = client.create_vault_ec2_certificate_configuration(
                cert_name=cert_name,
                aws_public_cert=test_cert_info,
            )
        else:
            actual_response = client.create_vault_ec2_certificate_configuration(
                cert_name=cert_name,
                aws_public_cert=test_cert_info,
                mount_point=mount_point
            )

        self.assertEqual(
            first=expected_status_code,
            second=actual_response.status_code,
        )

    @parameterized.expand([
        ("default mount point", None, 'my-cool-cert-1'),
        ("custom mount point", 'aws-ec2', 'my-cool-cert-2'),
    ])
    @requests_mock.Mocker()
    def test_get_vault_ec2_certificate_configuration(self, test_label, mount_point, cert_name, requests_mocker):
        mock_response = {
            "data": {
                "aws_public_cert": "-----BEGIN CERTIFICATE-----\nblah blah9K\n-----END CERTIFICATE-----\n",
                "type": "pkcs7"
            }
        }
        expected_status_code = 200
        mock_url = 'http://localhost:8200/v1/auth/{0}/config/certificate/{1}'.format(
            'aws-ec2' if mount_point is None else mount_point,
            cert_name,
        )
        requests_mocker.register_uri(
            method='GET',
            url=mock_url,
            json=mock_response,
            status_code=expected_status_code,
        )
        client = Client()

        if mount_point is None:
            actual_response = client.get_vault_ec2_certificate_configuration(
                cert_name=cert_name,
            )
        else:
            actual_response = client.get_vault_ec2_certificate_configuration(
                cert_name=cert_name,
                mount_point=mount_point
            )

        self.assertEqual(
            first=mock_response,
            second=actual_response,
        )

    @parameterized.expand([
        ("default mount point", None),
        ("custom mount point", 'aws-ec2'),
    ])
    @requests_mock.Mocker()
    def test_list_vault_ec2_certificate_configurations(self, test_label, mount_point, requests_mocker):
        mock_response = {
            "data": {
                "keys": [
                    "cert1"
                ]
            }
        }

        expected_status_code = 200
        mock_url = 'http://localhost:8200/v1/auth/{0}/config/certificates?list=true'.format(
            'aws-ec2' if mount_point is None else mount_point,
        )
        requests_mocker.register_uri(
            method='GET',
            url=mock_url,
            json=mock_response,
            status_code=expected_status_code,
        )
        client = Client()

        if mount_point is None:
            actual_response = client.list_vault_ec2_certificate_configurations()
        else:
            actual_response = client.list_vault_ec2_certificate_configurations(
                mount_point=mount_point
            )

        self.assertEqual(
            first=mock_response,
            second=actual_response,
        )

    @parameterized.expand([
        ("default mount point", None, 'my-role-1'),
        ("custom mount point", 'aws-ec2', 'my-role-2'),
    ])
    @requests_mock.Mocker()
    def test_create_ec2_role(self, test_label, mount_point, role_name, requests_mocker):
        expected_status_code = 204
        mock_url = 'http://localhost:8200/v1/auth/{0}/role/{1}'.format(
            'aws-ec2' if mount_point is None else mount_point,
            role_name,
        )
        requests_mocker.register_uri(
            method='POST',
            url=mock_url,
            status_code=expected_status_code,
        )
        client = Client()

        if mount_point is None:
            actual_response = client.create_ec2_role(
                role=role_name
            )
        else:
            actual_response = client.create_ec2_role(
                role=role_name,
                mount_point=mount_point
            )

        self.assertEqual(
            first=expected_status_code,
            second=actual_response.status_code,
        )

    @parameterized.expand([
        ("default mount point", None, 'my-role-1'),
        ("custom mount point", 'aws-ec2', 'my-role-2'),
    ])
    @requests_mock.Mocker()
    def test_get_ec2_role(self, test_label, mount_point, role_name, requests_mocker):
        mock_response = {
            "data": {
                "bound_ami_id": ["ami-fce36987"],
                "role_tag": "",
                "policies": [
                    "default",
                    "dev",
                    "prod"
                ],
                "max_ttl": 1800000,
                "disallow_reauthentication": False,
                "allow_instance_migration": False
            }
        }
        expected_status_code = 200
        mock_url = 'http://localhost:8200/v1/auth/{0}/role/{1}'.format(
            'aws-ec2' if mount_point is None else mount_point,
            role_name,
        )
        requests_mocker.register_uri(
            method='GET',
            url=mock_url,
            json=mock_response,
            status_code=expected_status_code,
        )
        client = Client()

        if mount_point is None:
            actual_response = client.get_ec2_role(
                role=role_name
            )
        else:
            actual_response = client.get_ec2_role(
                role=role_name,
                mount_point=mount_point
            )

        self.assertEqual(
            first=mock_response,
            second=actual_response,
        )

    @parameterized.expand([
        ("default mount point", None, 'my-role-1'),
        ("custom mount point", 'aws-ec2', 'my-role-2'),
    ])
    @requests_mock.Mocker()
    def test_delete_ec2_role(self, test_label, mount_point, role_name, requests_mocker):
        expected_status_code = 204
        mock_url = 'http://localhost:8200/v1/auth/{0}/role/{1}'.format(
            'aws-ec2' if mount_point is None else mount_point,
            role_name,
        )
        requests_mocker.register_uri(
            method='DELETE',
            url=mock_url,
            status_code=expected_status_code,
        )
        client = Client()

        if mount_point is None:
            actual_response = client.delete_ec2_role(
                role=role_name
            )
        else:
            actual_response = client.delete_ec2_role(
                role=role_name,
                mount_point=mount_point
            )

        self.assertEqual(
            first=expected_status_code,
            second=actual_response.status_code,
        )

    @parameterized.expand([
        ("default mount point", None),
        ("custom mount point", 'aws-ec2'),
    ])
    @requests_mock.Mocker()
    def test_list_ec2_roles(self, test_label, mount_point, requests_mocker):
        mock_response = {
            "data": {
                "keys": [
                    "dev-role",
                    "prod-role"
                ]
            }
        }
        expected_status_code = 200
        mock_url = 'http://localhost:8200/v1/auth/{0}/roles?list=true'.format(
            'aws-ec2' if mount_point is None else mount_point,
        )
        requests_mocker.register_uri(
            method='GET',
            url=mock_url,
            json=mock_response,
            status_code=expected_status_code,
        )
        client = Client()

        if mount_point is None:
            actual_response = client.list_ec2_roles()
        else:
            actual_response = client.list_ec2_roles(
                mount_point=mount_point
            )

        self.assertEqual(
            first=mock_response,
            second=actual_response,
        )

    @parameterized.expand([
        ("default mount point", None, 'my-role-1'),
        ("custom mount point", 'aws-ec2', 'my-role-2'),
    ])
    @requests_mock.Mocker()
    def test_create_ec2_role_tag(self, test_label, mount_point, role_name, requests_mocker):
        mock_response = {
            "data": {
                "tag_value": "v1:09Vp0qGuyB8=:r=dev-role:p=default,dev-api:d=false:t=300h0m0s:uPLKCQxqsefRhrp1qmVa1wsQVUXXJG8UZP/pJIdVyOI=",
                "tag_key": "VaultRole"
            }
        }
        expected_status_code = 200
        mock_url = 'http://localhost:8200/v1/auth/{0}/role/{1}/tag'.format(
            'aws-ec2' if mount_point is None else mount_point,
            role_name
        )
        requests_mocker.register_uri(
            method='POST',
            url=mock_url,
            json=mock_response,
            status_code=expected_status_code,
        )
        client = Client()

        if mount_point is None:
            actual_response = client.create_ec2_role_tag(
                role=role_name,
            )
        else:
            actual_response = client.create_ec2_role_tag(
                role=role_name,
                mount_point=mount_point
            )

        self.assertEqual(
            first=mock_response,
            second=actual_response.json(),
        )
