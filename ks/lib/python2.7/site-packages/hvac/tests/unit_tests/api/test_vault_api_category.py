from unittest import TestCase

from mock import create_autospec

from hvac.adapters import Adapter
from hvac.api.vault_api_base import VaultApiBase
from hvac.api.vault_api_category import VaultApiCategory

UNIMPLEMENTED_CLASSES = [
    'not_implemented'
]


class ImplementedVaultApiBase(VaultApiBase):
    pass


class ImplementedVaultApiCategory(VaultApiCategory):

    @property
    def implemented_classes(self):
        return [ImplementedVaultApiBase]

    @property
    def unimplemented_classes(self):
        return UNIMPLEMENTED_CLASSES


class TestVaultApiCategory(TestCase):
    mock_vault_api_category = None
    mock_adapter = None

    def setUp(self):
        self.mock_adapter = create_autospec(Adapter)
        self.mock_vault_api_category = ImplementedVaultApiCategory(
            adapter=self.mock_adapter,
        )

    def tearDown(self):
        self.mock_vault_api_category = None
        self.mock_adapter = None

    def test_getattr(self):
        assert self.mock_vault_api_category.implementedvaultapibase

        with self.assertRaises(AttributeError):
            assert self.mock_vault_api_category.not_an_attribute

        with self.assertRaises(AttributeError):
            assert self.mock_vault_api_category.not_an_attribute.on_not_an_attribute

        with self.assertRaises(NotImplementedError):
            assert self.mock_vault_api_category.not_implemented

    def test_unimplemented_classes(self):
        self.assertEqual(
            first=self.mock_vault_api_category.unimplemented_classes,
            second=UNIMPLEMENTED_CLASSES,
        )

    def test_adapter_property(self):
        self.assertIsInstance(
            obj=self.mock_vault_api_category.adapter,
            cls=Adapter,
        )

        new_adapter = 'this is my new adapter'
        self.mock_vault_api_category.adapter = new_adapter

        self.assertEqual(
            first=self.mock_vault_api_category._implementedvaultapibase.adapter,
            second=new_adapter,
        )
