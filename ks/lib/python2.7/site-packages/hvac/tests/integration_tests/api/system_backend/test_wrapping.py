import logging
from unittest import TestCase

from hvac.tests import utils


class TestWrapping(utils.HvacIntegrationTestCase, TestCase):
    TEST_AUTH_METHOD_TYPE = 'approle'
    TEST_AUTH_METHOD_PATH = 'test-approle'

    def setUp(self):
        super(TestWrapping, self).setUp()
        self.client.sys.enable_auth_method(
            method_type=self.TEST_AUTH_METHOD_TYPE,
            path=self.TEST_AUTH_METHOD_PATH,
        )

    def test_unwrap(self):
        self.client.write(
            path="auth/{path}/role/testrole".format(path=self.TEST_AUTH_METHOD_PATH),
        )
        result = self.client.write(
            path='auth/{path}/role/testrole/secret-id'.format(
                path=self.TEST_AUTH_METHOD_PATH
            ),
            wrap_ttl="10s",
        )
        self.assertIn('token', result['wrap_info'])

        unwrap_response = self.client.sys.unwrap(result['wrap_info']['token'])
        logging.debug('unwrap_response: %s' % unwrap_response)
        self.assertIn(
            member='secret_id_accessor',
            container=unwrap_response['data']
        )
        self.assertIn(
            member='secret_id',
            container=unwrap_response['data']
        )
