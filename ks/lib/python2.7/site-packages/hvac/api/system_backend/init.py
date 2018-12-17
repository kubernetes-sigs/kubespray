from hvac.api.system_backend.system_backend_mixin import SystemBackendMixin
from hvac.exceptions import ParamValidationError


class Init(SystemBackendMixin):

    def read_init_status(self):
        """Read the initialization status of Vault.

        Supported methods:
            GET: /sys/init. Produces: 200 application/json

        :return: The JSON response of the request.
        :rtype: dict
        """
        api_path = '/v1/sys/init'
        response = self._adapter.get(
            url=api_path,
        )
        return response.json()

    def is_initialized(self):
        """Determine is Vault is initialized or not.

        :return: True if Vault is initialized, False otherwise.
        :rtype: bool
        """
        status = self.read_init_status()
        return status['initialized']

    def initialize(self, secret_shares=5, secret_threshold=3, pgp_keys=None, root_token_pgp_key=None,
                   stored_shares=None, recovery_shares=None, recovery_threshold=None, recovery_pgp_keys=None):
        """Initialize a new Vault.

        The Vault must not have been previously initialized. The recovery options, as well as the stored shares option,
        are only available when using Vault HSM.

        Supported methods:
            PUT: /sys/init. Produces: 200 application/json

        :param secret_shares: The number of shares to split the master key into.
        :type secret_shares: int
        :param secret_threshold: Specifies the number of shares required to reconstruct the master key. This must be
            less than or equal secret_shares. If using Vault HSM with auto-unsealing, this value must be the same as
            secret_shares.
        :type secret_threshold: int
        :param pgp_keys: List of PGP public keys used to encrypt the output unseal keys.
            Ordering is preserved. The keys must be base64-encoded from their original binary representation.
            The size of this array must be the same as secret_shares.
        :type pgp_keys: list
        :param root_token_pgp_key: Specifies a PGP public key used to encrypt the initial root token. The
            key must be base64-encoded from its original binary representation.
        :type root_token_pgp_key: str | unicode
        :param stored_shares: <enterprise only> Specifies the number of shares that should be encrypted by the HSM and
            stored for auto-unsealing. Currently must be the same as secret_shares.
        :type stored_shares: int
        :param recovery_shares: <enterprise only> Specifies the number of shares to split the recovery key into.
        :type recovery_shares: int
        :param recovery_threshold: <enterprise only> Specifies the number of shares required to reconstruct the recovery
            key. This must be less than or equal to recovery_shares.
        :type recovery_threshold: int
        :param recovery_pgp_keys: <enterprise only> Specifies an array of PGP public keys used to encrypt the output
            recovery keys. Ordering is preserved. The keys must be base64-encoded from their original binary
            representation. The size of this array must be the same as recovery_shares.
        :type recovery_pgp_keys: list
        :return: The JSON response of the request.
        :rtype: dict
        """
        params = {
            'secret_shares': secret_shares,
            'secret_threshold': secret_threshold,
            'root_token_pgp_key': root_token_pgp_key,
        }

        if pgp_keys is not None:
            if len(pgp_keys) != secret_shares:
                raise ParamValidationError('length of pgp_keys list argument must equal secret_shares value')
            params['pgp_keys'] = pgp_keys

        if stored_shares is not None:
            if stored_shares != secret_shares:
                raise ParamValidationError('value for stored_shares argument must equal secret_shares argument')
            params['stored_shares'] = stored_shares

        if recovery_shares is not None:
            params['recovery_shares'] = recovery_shares

        if recovery_threshold is not None:
            if recovery_threshold <= recovery_shares:
                error_msg = 'value for recovery_threshold argument be less than or equal to recovery_shares argument'
                raise ParamValidationError(error_msg)
            params['recovery_threshold'] = recovery_threshold

        if recovery_pgp_keys is not None:
            if len(recovery_pgp_keys) != recovery_shares:
                raise ParamValidationError('length of recovery_pgp_keys list argument must equal recovery_shares value')
            params['recovery_pgp_keys'] = recovery_pgp_keys

        api_path = '/v1/sys/init'
        response = self._adapter.put(
            url=api_path,
            json=params,
        )
        return response.json()
