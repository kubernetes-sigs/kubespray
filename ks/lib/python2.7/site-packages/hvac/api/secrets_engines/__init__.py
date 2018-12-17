"""Vault secrets engines endpoints"""
from hvac.api.secrets_engines.azure import Azure
from hvac.api.secrets_engines.identity import Identity
from hvac.api.secrets_engines.kv import Kv
from hvac.api.secrets_engines.kv_v1 import KvV1
from hvac.api.secrets_engines.kv_v2 import KvV2
from hvac.api.secrets_engines.transit import Transit
from hvac.api.vault_api_category import VaultApiCategory

__all__ = (
    'Azure',
    'Identity',
    'Kv',
    'KvV1',
    'KvV2',
    'Transit',
    'SecretsEngines',
)


class SecretsEngines(VaultApiCategory):
    """Secrets Engines."""

    implemented_classes = [
        Azure,
        Identity,
        Kv,
        Transit,
    ]
    unimplemented_classes = [
        'Ad',
        'AliCloud',
        'AWS',
        'Azure',
        'Consul',
        'Database',
        'Gcp',
        'GcpKms',
        'Nomad',
        'Pki',
        'RabbitMq',
        'Ssh',
        'TOTP',
        'Cassandra',
        'MongoDb',
        'Mssql',
        'MySql',
        'PostgreSql',
    ]
