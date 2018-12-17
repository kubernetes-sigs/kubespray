from unittest import TestCase

import requests_mock
from parameterized import parameterized

from hvac import adapters


class TestRequest(TestCase):
    """Unit tests providing coverage for requests-related methods in the hvac Client class."""

    @parameterized.expand([
        ("standard Vault address", 'https://localhost:8200'),
        ("Vault address with route", 'https://example.com/vault'),
    ])
    @requests_mock.Mocker()
    def test_get(self, test_label, test_url, requests_mocker):
        test_path = 'v1/sys/health'
        expected_status_code = 200
        mock_url = '{0}/{1}'.format(test_url, test_path)
        requests_mocker.register_uri(
            method='GET',
            url=mock_url,
        )
        adapter = adapters.Request(base_uri=test_url)
        response = adapter.get(
            url='v1/sys/health',
        )
        self.assertEqual(
            first=expected_status_code,
            second=response.status_code,
        )

    @parameterized.expand([
        ("kv secret lookup", 'v1/secret/some-secret'),
    ])
    @requests_mock.Mocker()
    def test_list(self, test_label, test_path, requests_mocker):
        mock_response = {
            'auth': None,
            'data': {
                'keys': ['things1', 'things2']
            },
            'lease_duration': 0,
            'lease_id': '',
            'renewable': False,
            'request_id': 'ba933afe-84d4-410f-161b-592a5c016009',
            'warnings': None,
            'wrap_info': None
        }
        expected_status_code = 200
        mock_url = '{0}/{1}'.format(adapters.DEFAULT_BASE_URI, test_path)
        requests_mocker.register_uri(
            method='LIST',
            url=mock_url,
            json=mock_response
        )
        adapter = adapters.Request()
        response = adapter.list(
            url=test_path,
        )
        self.assertEqual(
            first=expected_status_code,
            second=response.status_code,
        )
        self.assertEqual(
            first=mock_response,
            second=response.json()
        )
