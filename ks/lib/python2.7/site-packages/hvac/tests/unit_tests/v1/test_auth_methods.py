from unittest import TestCase

import requests_mock

from hvac import Client


class TestAuthMethods(TestCase):
    """Tests for methods related to Vault sys/auth routes."""

    @requests_mock.Mocker()
    def test_tune_auth_backend(self, requests_mocker):
        expected_status_code = 204
        test_backend_type = 'approle'
        test_mount_point = 'approle-test'
        test_description = 'this is a test description'
        requests_mocker.register_uri(
            method='POST',
            url='http://localhost:8200/v1/sys/auth/{0}/tune'.format(test_mount_point),
            status_code=expected_status_code,
        )
        client = Client()
        actual_response = client.tune_auth_backend(
            backend_type=test_backend_type,
            mount_point=test_mount_point,
            description=test_description,
        )

        self.assertEqual(
            first=expected_status_code,
            second=actual_response.status_code,
        )

        actual_request_params = requests_mocker.request_history[0].json()

        # Ensure we sent through an optional tune parameter as expected
        self.assertEqual(
            first=test_description,
            second=actual_request_params['description'],
        )

    @requests_mock.Mocker()
    def test_get_auth_backend_tuning(self, requests_mocker):
        expected_status_code = 200
        test_backend_type = 'approle'
        test_mount_point = 'approle-test'
        mock_response = {
            'max_lease_ttl': 12345678,
            'lease_id': '',
            'force_no_cache': False,
            'warnings': None,
            'data': {
                'force_no_cache': False,
                'default_lease_ttl': 2764800,
                'max_lease_ttl': 12345678
            },
            'wrap_info': None,
            'auth': None,
            'lease_duration': 0,
            'request_id': '673f2336-3235-b988-2194-c68261a02bfe',
            'default_lease_ttl': 2764800,
            'renewable': False
        }
        requests_mocker.register_uri(
            method='GET',
            url='http://localhost:8200/v1/sys/auth/{0}/tune'.format(test_mount_point),
            status_code=expected_status_code,
            json=mock_response
        )
        client = Client()
        actual_response = client.get_auth_backend_tuning(
            backend_type=test_backend_type,
            mount_point=test_mount_point,
        )

        self.assertEqual(
            first=mock_response,
            second=actual_response,
        )
