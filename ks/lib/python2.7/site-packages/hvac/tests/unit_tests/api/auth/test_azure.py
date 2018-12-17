import logging
from unittest import TestCase
from unittest import skipIf

import requests_mock
from parameterized import parameterized

from hvac.adapters import Request
from hvac.api.auth_methods import Azure
from hvac.tests import utils


@skipIf(utils.skip_if_vault_version_lt('0.10.0'), "Azure auth method not available before Vault version 0.10.0")
class TestAzure(TestCase):
    TEST_MOUNT_POINT = 'azure-test'

    @parameterized.expand([
        ('success', dict(), None,),
        ('with subscription_id', dict(subscription_id='my_subscription_id'), None,),
        ('with resource_group_name', dict(resource_group_name='my_resource_group_name'), None,),
        ('with vm_name', dict(vm_name='my_vm_name'), None,),
        ('with vmss_name', dict(vmss_name='my_vmss_name'), None,),
        ('with vm_name and vmss_name', dict(vm_name='my_vm_name', vmss_name='my_vmss_name'), None,),
    ])
    @requests_mock.Mocker()
    def test_login(self, label, test_params, raises, requests_mocker):
        role_name = 'hvac'
        test_policies = [
            "default",
            "dev",
            "prod",
        ]
        expected_status_code = 200
        mock_url = 'http://localhost:8200/v1/auth/{mount_point}/login'.format(
            mount_point=self.TEST_MOUNT_POINT,
        )
        mock_response = {
            "auth": {
                "client_token": "f33f8c72-924e-11f8-cb43-ac59d697597c",
                "accessor": "0e9e354a-520f-df04-6867-ee81cae3d42d",
                "policies": test_policies,
                "lease_duration": 2764800,
                "renewable": True,
            },
        }
        requests_mocker.register_uri(
            method='POST',
            url=mock_url,
            status_code=expected_status_code,
            json=mock_response,
        )
        azure = Azure(adapter=Request())
        if raises is not None:
            with self.assertRaises(raises):
                azure.login(
                    role=role_name,
                    jwt='my-jwt',
                    mount_point=self.TEST_MOUNT_POINT,
                    **test_params
                )
        else:
            login_response = azure.login(
                role=role_name,
                jwt='my-jwt',
                mount_point=self.TEST_MOUNT_POINT,
                **test_params
            )
            logging.debug('login_response: %s' % login_response)
            self.assertEqual(
                first=login_response['auth']['policies'],
                second=test_policies,
            )
