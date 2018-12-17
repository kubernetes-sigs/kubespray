"""Collection of Vault API endpoint classes."""
from hvac.api.auth_methods import AuthMethods
from hvac.api.secrets_engines import SecretsEngines
from hvac.api.system_backend import SystemBackend
from hvac.api.vault_api_base import VaultApiBase
from hvac.api.vault_api_category import VaultApiCategory

__all__ = (
    'AuthMethods',
    'SecretsEngines',
    'SystemBackend',
    'VaultApiBase',
    'VaultApiCategory',
)
