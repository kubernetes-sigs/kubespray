from unittest import TestCase

from hvac.tests import utils


class TestSeal(utils.HvacIntegrationTestCase, TestCase):

    def test_unseal_multi(self):
        cls = type(self)

        self.client.sys.seal()

        keys = cls.manager.keys

        result = self.client.sys.submit_unseal_keys(keys[0:2])

        self.assertTrue(result['sealed'])
        self.assertEqual(result['progress'], 2)

        result = self.client.sys.submit_unseal_key(reset=True)
        self.assertEqual(result['progress'], 0)
        result = self.client.sys.submit_unseal_keys(keys[1:3])
        self.assertTrue(result['sealed'])
        self.assertEqual(result['progress'], 2)
        self.client.sys.submit_unseal_keys(keys[0:1])
        result = self.client.sys.submit_unseal_keys(keys[2:3])
        self.assertFalse(result['sealed'])

    def test_seal_unseal(self):
        cls = type(self)

        self.assertFalse(self.client.sys.is_sealed())

        self.client.sys.seal()

        self.assertTrue(self.client.sys.is_sealed())

        cls.manager.unseal()

        self.assertFalse(self.client.sys.is_sealed())
