import logging
from unittest import TestCase
from unittest import skipIf

from parameterized import parameterized

from hvac import exceptions
from hvac.tests import utils


@skipIf(utils.skip_if_vault_version_lt('0.11.0'), "Azure secret engine not available before Vault version 0.11.0")
class TestAzure(utils.HvacIntegrationTestCase, TestCase):
    TENANT_ID = '00000000-0000-0000-0000-000000000000'
    SUBSCRIPTION_ID = '00000000-0000-0000-0000-000000000000'
    DEFAULT_MOUNT_POINT = 'azure-integration-test'

    def setUp(self):
        super(TestAzure, self).setUp()
        self.client.enable_secret_backend(
            backend_type='azure',
            mount_point=self.DEFAULT_MOUNT_POINT,
        )

    def tearDown(self):
        self.client.disable_secret_backend(mount_point=self.DEFAULT_MOUNT_POINT)
        super(TestAzure, self).tearDown()

    @parameterized.expand([
        ('no parameters',),
        ('valid environment argument', 'AzureUSGovernmentCloud'),
        ('invalid environment argument', 'AzureCityKity', exceptions.ParamValidationError, 'invalid environment argument provided'),
    ])
    def test_configure_and_read_configuration(self, test_label, environment=None, raises=False, exception_message=''):
        configure_arguments = {
            'subscription_id': self.SUBSCRIPTION_ID,
            'tenant_id': self.TENANT_ID,
            'mount_point': self.DEFAULT_MOUNT_POINT,
        }
        if environment is not None:
            configure_arguments['environment'] = environment
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.secrets.azure.configure(**configure_arguments)
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            configure_response = self.client.secrets.azure.configure(**configure_arguments)
            logging.debug('configure_response: %s' % configure_response)
            read_configuration_response = self.client.secrets.azure.read_config(
                mount_point=self.DEFAULT_MOUNT_POINT,
            )
            logging.debug('read_configuration_response: %s' % read_configuration_response)
            # raise Exception()
            self.assertEqual(
                first=self.SUBSCRIPTION_ID,
                second=read_configuration_response['subscription_id'],
            )
            self.assertEqual(
                first=self.TENANT_ID,
                second=read_configuration_response['tenant_id'],
            )
            if environment is not None:
                self.assertEqual(
                    first=environment,
                    second=read_configuration_response['environment'],
                )

    @parameterized.expand([
        ('create and then delete config',),
    ])
    def test_delete_config(self, test_label):
        configure_response = self.client.secrets.azure.configure(
            subscription_id=self.SUBSCRIPTION_ID,
            tenant_id=self.TENANT_ID,
            mount_point=self.DEFAULT_MOUNT_POINT
        )
        logging.debug('configure_response: %s' % configure_response)
        self.client.secrets.azure.delete_config(
            mount_point=self.DEFAULT_MOUNT_POINT,
        )
        read_configuration_response = self.client.secrets.azure.read_config(
            mount_point=self.DEFAULT_MOUNT_POINT,
        )
        logging.debug('read_configuration_response: %s' % read_configuration_response)
        for key in read_configuration_response.keys():
            self.assertEqual(
                first='',
                second=read_configuration_response[key],
            )
