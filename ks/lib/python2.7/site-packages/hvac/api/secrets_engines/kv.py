"""Kv secret backend methods module."""

import logging

from hvac.api.secrets_engines import kv_v1, kv_v2
from hvac.api.vault_api_base import VaultApiBase

logger = logging.getLogger(__name__)


class Kv(VaultApiBase):
    """Class containing methods for the key/value secrets_engines backend API routes.
    Reference: https://www.vaultproject.io/docs/secrets/kv/index.html

    """
    allowed_kv_versions = ['1', '2']

    def __init__(self, adapter, default_kv_version='2'):
        """Create a new Kv instance.

        :param adapter: Instance of :py:class:`hvac.adapters.Adapter`; used for performing HTTP requests.
        :type adapter: hvac.adapters.Adapter
        :param default_kv_version: KV version number (e.g., '1') to use as the default when accessing attributes/methods
            under this class.
        :type default_kv_version: str | unicode
        """
        super(Kv, self).__init__(adapter=adapter)
        self._default_kv_version = default_kv_version

        self._kv_v1 = kv_v1.KvV1(adapter=self._adapter)
        self._kv_v2 = kv_v2.KvV2(adapter=self._adapter)

    @property
    def v1(self):
        """Accessor for kv version 1 class / method. Provided via the :py:class:`hvac.api.secrets_engines.kv_v1.KvV1` class.

        :return: This Kv instance's associated KvV1 instance.
        :rtype: hvac.api.secrets_engines.kv_v1.KvV1
        """
        return self._kv_v1

    @property
    def v2(self):
        """Accessor for kv version 2 class / method. Provided via the :py:class:`hvac.api.secrets_engines.kv_v2.KvV2` class.

        :return: This Kv instance's associated KvV2 instance.
        :rtype: hvac.api.secrets_engines.kv_v2.KvV2
        """
        return self._kv_v2

    @property
    def default_kv_version(self):
        return self._default_kv_version

    @default_kv_version.setter
    def default_kv_version(self, default_kv_version):
        if default_kv_version not in self.allowed_kv_versions:
            error_message = 'Invalid "default_kv_version"; "{allowed}" allowed, "{provided}" provided'.format(
                allowed=','.join(self.allowed_kv_versions),
                provided=default_kv_version
            )
            raise ValueError(error_message)
        self._default_kv_version = default_kv_version

    def __getattr__(self, item):
        """Overridden magic method used to direct method calls to the appropriate KV version's hvac class.

        :param item: Name of the attribute/method being accessed
        :type item: str | unicode
        :return: The selected secrets_engines class corresponding to this instance's default_kv_version setting
        :rtype: hvac.api.vault_api_base.VaultApiBase
        """
        if self.default_kv_version == '1':
            return getattr(self._kv_v1, item)
        elif self.default_kv_version == '2':
            return getattr(self._kv_v2, item)

        raise AttributeError
