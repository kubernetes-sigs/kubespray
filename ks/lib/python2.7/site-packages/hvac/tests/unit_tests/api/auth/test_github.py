from unittest import TestCase

import requests_mock
from parameterized import parameterized

from hvac.adapters import Request
from hvac.api.auth_methods import Github
from hvac.api.auth_methods.github import DEFAULT_MOUNT_POINT


class TestGithub(TestCase):

    @parameterized.expand([
        ("default mount point", DEFAULT_MOUNT_POINT),
        ("custom mount point", 'cathub'),
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
        github = Github(adapter=Request())
        response = github.configure(
            organization='hvac',
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
            'auth': None,
            'data': {
                'base_url': '',
                'max_ttl': 0,
                'organization': '',
                'ttl': 0
            },
            'lease_duration': 0,
            'lease_id': '',
            'renewable': False,
            'request_id': '860a11a8-b835-cbab-7fce-de4edc4cf533',
            'warnings': None,
            'wrap_info': None
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
        github = Github(adapter=Request())
        response = github.read_configuration(
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
    def test_map_team(self, test_label, mount_point, requests_mocker):
        expected_status_code = 204
        team_name = 'hvac'
        mock_url = 'http://localhost:8200/v1/auth/{mount_point}/map/teams/{team_name}'.format(
            mount_point=mount_point,
            team_name=team_name,
        )
        requests_mocker.register_uri(
            method='POST',
            url=mock_url,
            status_code=expected_status_code,
        )
        github = Github(adapter=Request())
        response = github.map_team(
            team_name=team_name,
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
    def test_read_team_mapping(self, test_label, mount_point, requests_mocker):
        expected_status_code = 200
        team_name = 'hvac'
        mock_response = {
            'auth': None,
            'data': {
                'key': 'SOME_TEAM',
                'value': 'some-team-policy'
            },
            'lease_duration': 0,
            'lease_id': '',
            'renewable': False,
            'request_id': '50346cc8-34e7-f2ea-f36a-fcb9d45c1676',
            'warnings': None,
            'wrap_info': None
        }
        mock_url = 'http://localhost:8200/v1/auth/{mount_point}/map/teams/{team_name}'.format(
            mount_point=mount_point,
            team_name=team_name,
        )
        requests_mocker.register_uri(
            method='GET',
            url=mock_url,
            status_code=expected_status_code,
            json=mock_response,
        )
        github = Github(adapter=Request())
        response = github.read_team_mapping(
            team_name=team_name,
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
    def test_map_user(self, test_label, mount_point, requests_mocker):
        expected_status_code = 204
        user_name = 'hvac'
        mock_url = 'http://localhost:8200/v1/auth/{mount_point}/map/users/{user_name}'.format(
            mount_point=mount_point,
            user_name=user_name,
        )
        requests_mocker.register_uri(
            method='POST',
            url=mock_url,
            status_code=expected_status_code,
        )
        github = Github(adapter=Request())
        response = github.map_user(
            user_name=user_name,
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
    def test_read_user_mapping(self, test_label, mount_point, requests_mocker):
        expected_status_code = 200
        user_name = 'hvac'
        mock_response = {
            'auth': None,
            'data': None,
            'lease_duration': 0,
            'lease_id': '',
            'renewable': False,
            'request_id': '71ec6e1b-6d4e-6374-ddc2-ff1cdd860e60',
            'warnings': None,
            'wrap_info': None
        }
        mock_url = 'http://localhost:8200/v1/auth/{mount_point}/map/users/{user_name}'.format(
            mount_point=mount_point,
            user_name=user_name,
        )
        requests_mocker.register_uri(
            method='GET',
            url=mock_url,
            status_code=expected_status_code,
            json=mock_response,
        )
        github = Github(adapter=Request())
        response = github.read_user_mapping(
            user_name=user_name,
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
    def test_login(self, test_label, mount_point, requests_mocker):
        mock_response = {
            'auth': {
                'accessor': 'f578d442-94ec-11e8-afe4-0af6a65f93f6',
                'client_token': 'edf5c2c0-94ec-11e8-afe4-0af6a65f93f6',
                'entity_id': 'f9268760-94ec-11e8-afe4-0af6a65f93f6',
                'lease_duration': 3600,
                'metadata': {'org': 'hvac', 'username': 'hvacbot'},
                'policies': ['default', ],
                'renewable': True,
                'token_policies': ['default']
            },
            'data': None,
            'lease_duration': 0,
            'lease_id': '',
            'renewable': False,
            'request_id': '488cf309-2f81-cc04-51bf-c43063d309eb',
            'warnings': None,
            'wrap_info': None
        }
        mock_url = 'http://localhost:8200/v1/auth/{mount_point}/login'.format(
            mount_point=mount_point,
        )
        requests_mocker.register_uri(
            method='POST',
            url=mock_url,
            json=mock_response,
        )
        github = Github(adapter=Request())
        response = github.login(
            token='valid-token',
            mount_point=mount_point,
        )
        self.assertEqual(
            first=mock_response,
            second=response,
        )
        self.assertEqual(
            first=mock_response['auth']['client_token'],
            second=github._adapter.token,
        )
