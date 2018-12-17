from unittest import TestCase

from hvac.tests import utils


class TestLeader(utils.HvacIntegrationTestCase, TestCase):

    def test_read_health_status(self):
        self.assertIn(
            member='ha_enabled',
            container=self.client.sys.read_leader_status(),
        )
