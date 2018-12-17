import logging
from unittest import TestCase
from unittest import skipIf

import requests_mock
from parameterized import parameterized

from hvac.adapters import Request
from hvac.api.secrets_engines.azure import Azure, DEFAULT_MOUNT_POINT
from hvac.tests import utils


@skipIf(utils.skip_if_vault_version_lt('0.11.0'), "Azure secret engine not available before Vault version 0.11.0")
class TestAzure(TestCase):
    @parameterized.expand([
        ('create role', None),
    ])
    @requests_mock.Mocker()
    def test_create_or_update_role(self, test_label, azure_roles, requests_mocker):
        expected_status_code = 204
        role_name = 'hvac'
        if azure_roles is None:
            azure_roles = [
                {
                    'role_name': "Contributor",
                    'scope': "/subscriptions/95e675fa-307a-455e-8cdf-0a66aeaa35ae",
                },
            ]

        mock_url = 'http://localhost:8200/v1/{mount_point}/roles/{name}'.format(
            mount_point=DEFAULT_MOUNT_POINT,
            name=role_name,
        )
        requests_mocker.register_uri(
            method='POST',
            url=mock_url,
            status_code=expected_status_code,
            # json=mock_response,
        )
        azure = Azure(adapter=Request())
        create_or_update_role_response = azure.create_or_update_role(
            name=role_name,
            azure_roles=azure_roles,
            mount_point=DEFAULT_MOUNT_POINT
        )
        logging.debug('create_or_update_role_response: %s' % create_or_update_role_response)

        self.assertEqual(
            first=expected_status_code,
            second=create_or_update_role_response.status_code,
        )

    @parameterized.expand([
        ('some_test',),
    ])
    @requests_mock.Mocker()
    def test_list_roles(self, test_label, requests_mocker):
        expected_status_code = 200
        role_names = ['hvac']
        mock_response = {
            'data': {
                'roles': role_names,
            },
        }

        mock_url = 'http://localhost:8200/v1/{mount_point}/roles'.format(
            mount_point=DEFAULT_MOUNT_POINT,
        )
        requests_mocker.register_uri(
            method='LIST',
            url=mock_url,
            status_code=expected_status_code,
            json=mock_response,
        )
        azure = Azure(adapter=Request())
        list_roles_response = azure.list_roles(
            mount_point=DEFAULT_MOUNT_POINT
        )
        logging.debug('list_roles_response: %s' % list_roles_response)

        self.assertEqual(
            first=mock_response['data'],
            second=list_roles_response,
        )

    @parameterized.expand([
        ('some_test',),
    ])
    @requests_mock.Mocker()
    def test_generate_credentials(self, test_label, requests_mocker):
        expected_status_code = 200
        role_name = 'hvac'
        mock_response = {
            'data': {
                'client_id': 'some_client_id',
                'client_secret': 'some_client_secret',
            },
        }

        mock_url = 'http://localhost:8200/v1/{mount_point}/creds/{name}'.format(
            mount_point=DEFAULT_MOUNT_POINT,
            name=role_name,
        )
        requests_mocker.register_uri(
            method='GET',
            url=mock_url,
            status_code=expected_status_code,
            json=mock_response,
        )
        azure = Azure(adapter=Request())
        generate_credentials_response = azure.generate_credentials(
            name=role_name,
            mount_point=DEFAULT_MOUNT_POINT
        )
        logging.debug('generate_credentials_response: %s' % generate_credentials_response)

        self.assertEqual(
            first=mock_response['data'],
            second=generate_credentials_response,
        )
