from unittest import TestCase

import requests_mock
from parameterized import parameterized

from hvac.adapters import Request
from hvac.api.auth_methods import Mfa
from hvac.api.auth_methods.github import DEFAULT_MOUNT_POINT


class TestMfa(TestCase):

    @parameterized.expand([
        ("default mount point", DEFAULT_MOUNT_POINT),
        ("custom mount point", 'cathub'),
    ])
    @requests_mock.Mocker()
    def test_configure(self, test_label, mount_point, requests_mocker):
        expected_status_code = 204
        mock_url = 'http://localhost:8200/v1/auth/{mount_point}/mfa_config'.format(
            mount_point=mount_point,
        )
        requests_mocker.register_uri(
            method='POST',
            url=mock_url,
            status_code=expected_status_code,
        )
        mfa = Mfa(adapter=Request())
        response = mfa.configure(
            mount_point=mount_point,
        )
        self.assertEqual(
            first=expected_status_code,
            second=response.status_code,
        )

    @parameterized.expand([
        ("default mount point", DEFAULT_MOUNT_POINT),
        ("custom mount point", 'cathub'),
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
            'request_id': '18ecf194-aba2-ba99-ebb5-1b90e5e231c7',
            'data': {'type': 'duo'},
            'renewable': False
        }

        mock_url = 'http://localhost:8200/v1/auth/{mount_point}/mfa_config'.format(
            mount_point=mount_point,
        )
        requests_mocker.register_uri(
            method='GET',
            url=mock_url,
            status_code=expected_status_code,
            json=mock_response,
        )
        mfa = Mfa(adapter=Request())
        response = mfa.read_configuration(
            mount_point=mount_point,
        )
        self.assertEqual(
            first=mock_response,
            second=response,
        )

    @parameterized.expand([
        ("default mount point", DEFAULT_MOUNT_POINT),
        ("custom mount point", 'cathub'),
    ])
    @requests_mock.Mocker()
    def test_configure_duo_access(self, test_label, mount_point, requests_mocker):
        expected_status_code = 204
        mock_url = 'http://localhost:8200/v1/auth/{mount_point}/duo/access'.format(
            mount_point=mount_point,
        )
        requests_mocker.register_uri(
            method='POST',
            url=mock_url,
            status_code=expected_status_code,
        )
        mfa = Mfa(adapter=Request())
        response = mfa.configure_duo_access(
            mount_point=mount_point,
            host='someapisubdomain.hvac.network',
            integration_key='ikey',
            secret_key='supersecret',
        )
        self.assertEqual(
            first=expected_status_code,
            second=response.status_code,
        )

    @parameterized.expand([
        ("default mount point", DEFAULT_MOUNT_POINT),
        ("custom mount point", 'cathub'),
    ])
    @requests_mock.Mocker()
    def test_configure_duo_behavior(self, test_label, mount_point, requests_mocker):
        expected_status_code = 204
        mock_url = 'http://localhost:8200/v1/auth/{mount_point}/duo/config'.format(
            mount_point=mount_point,
        )
        requests_mocker.register_uri(
            method='POST',
            url=mock_url,
            status_code=expected_status_code,
        )
        mfa = Mfa(adapter=Request())
        response = mfa.configure_duo_behavior(
            mount_point=mount_point,
            push_info='howdy'
        )
        self.assertEqual(
            first=expected_status_code,
            second=response.status_code,
        )

    @parameterized.expand([
        ("default mount point", DEFAULT_MOUNT_POINT),
        ("custom mount point", 'cathub'),
    ])
    @requests_mock.Mocker()
    def test_read_duo_behvaior_configuration(self, test_label, mount_point, requests_mocker):
        expected_status_code = 200
        mock_response = {
            'lease_id': '',
            'warnings': None,
            'wrap_info': None,
            'auth': None,
            'lease_duration': 0,
            'request_id': '7ea734e8-bbc4-e2de-2769-d052d6a320c6',
            'data': {
                'username_format': '%s',
                'push_info': '',
                'user_agent': ''
            },
            'renewable': False
        }

        mock_url = 'http://localhost:8200/v1/auth/{mount_point}/duo/config'.format(
            mount_point=mount_point,
        )
        requests_mocker.register_uri(
            method='GET',
            url=mock_url,
            status_code=expected_status_code,
            json=mock_response,
        )
        mfa = Mfa(adapter=Request())
        response = mfa.read_duo_behavior_configuration(
            mount_point=mount_point,
        )
        self.assertEqual(
            first=mock_response,
            second=response,
        )
