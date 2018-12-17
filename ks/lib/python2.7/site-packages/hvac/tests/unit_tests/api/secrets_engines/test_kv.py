from unittest import TestCase

from mock import MagicMock
from parameterized import parameterized

from hvac.api.secrets_engines.kv import Kv
from hvac.api.secrets_engines.kv_v1 import KvV1
from hvac.api.secrets_engines.kv_v2 import KvV2
from hvac.tests import utils


class TestKv(utils.HvacIntegrationTestCase, TestCase):

    def test_v1_property(self):
        mock_adapter = MagicMock()
        kv = Kv(adapter=mock_adapter)
        self.assertIsInstance(
            obj=kv.v1,
            cls=KvV1,
        )

    def test_v2_property(self):
        mock_adapter = MagicMock()
        kv = Kv(adapter=mock_adapter)
        self.assertIsInstance(
            obj=kv.v2,
            cls=KvV2,
        )

    @parameterized.expand([
        ('v1', '1'),
        ('v2', '2'),
        ('v3', '3', ValueError),
        ('invalid version', '12345', ValueError),
    ])
    def test_default_kv_version_setter(self, test_label, version, raises=False):
        version_class_map = {
            '1': KvV1,
            '2': KvV2,
        }
        mock_adapter = MagicMock()
        kv = Kv(adapter=mock_adapter)

        if raises:
            with self.assertRaises(raises):
                kv.default_kv_version = version
        else:
            kv.default_kv_version = version
            self.assertIsInstance(
                obj=getattr(kv, 'v%s' % version),
                cls=version_class_map.get(version),
            )

    def test_getattr(self):
        mock_adapter = MagicMock()
        kv = Kv(adapter=mock_adapter, default_kv_version='1')
        self.assertEqual(
            first=kv.read_secret,
            second=kv.v1.read_secret,
        )
        kv = Kv(adapter=mock_adapter, default_kv_version='2')
        self.assertEqual(
            first=kv.read_secret_version,
            second=kv.v2.read_secret_version,
        )

        kv._default_kv_version = 0
        with self.assertRaises(AttributeError):
            assert kv.read_secret
