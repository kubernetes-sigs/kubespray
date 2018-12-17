import logging
from unittest import TestCase

from parameterized import parameterized, param

from hvac.tests import utils


class TestHealth(utils.HvacIntegrationTestCase, TestCase):

    @parameterized.expand([
        param(
            'default params',
        ),
        param(
            'GET method',
            method='GET'
        ),
    ])
    def test_read_health_status(self, label, method='HEAD'):
        read_status_response = self.client.sys.read_health_status(
            method=method,
        )
        logging.debug('read_status_response: %s' % read_status_response)
        if method == 'HEAD':
            self.assertEqual(
                first=read_status_response.status_code,
                second=200
            )
        else:
            self.assertTrue(
                expr=read_status_response['initialized']
            )
