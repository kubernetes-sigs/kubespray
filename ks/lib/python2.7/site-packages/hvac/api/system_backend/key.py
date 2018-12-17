from hvac.api.system_backend.system_backend_mixin import SystemBackendMixin
from hvac.exceptions import ParamValidationError


class Key(SystemBackendMixin):

    def read_root_generation_progress(self):
        """Read the configuration and process of the current root generation attempt.

        Supported methods:
            GET: /sys/generate-root/attempt. Produces: 200 application/json

        :return: The JSON response of the request.
        :rtype: dict
        """
        api_path = '/v1/sys/generate-root/attempt'
        response = self._adapter.get(
            url=api_path,
        )
        return response.json()

    def start_root_token_generation(self, otp=None, pgp_key=None):
        """Initialize a new root generation attempt.

        Only a single root generation attempt can take place at a time. One (and only one) of otp or pgp_key are
        required.

        Supported methods:
            PUT: /sys/generate-root/attempt. Produces: 200 application/json

        :param otp: Specifies a base64-encoded 16-byte value. The raw bytes of the token will be XOR'd with this value
            before being returned to the final unseal key provider.
        :type otp: str | unicode
        :param pgp_key: Specifies a base64-encoded PGP public key. The raw bytes of the token will be encrypted with
            this value before being returned to the final unseal key provider.
        :type pgp_key: str | unicode
        :return: The JSON response of the request.
        :rtype: dict
        """
        params = {}
        if otp is not None and pgp_key is not None:
            raise ParamValidationError('one (and only one) of otp or pgp_key arguments are required')
        if otp is not None:
            params['otp'] = otp
        if pgp_key is not None:
            params['pgp_key'] = pgp_key

        api_path = '/v1/sys/generate-root/attempt'
        response = self._adapter.put(
            url=api_path,
            json=params
        )
        return response.json()

    def generate_root(self, key, nonce):
        """Enter a single master key share to progress the root generation attempt.

        If the threshold number of master key shares is reached, Vault will complete the root generation and issue the
        new token. Otherwise, this API must be called multiple times until that threshold is met. The attempt nonce must
        be provided with each call.

        Supported methods:
            PUT: /sys/generate-root/update. Produces: 200 application/json

        :param key: Specifies a single master key share.
        :type key: str | unicode
        :param nonce: The nonce of the attempt.
        :type nonce: str | unicode
        :return: The JSON response of the request.
        :rtype: dict
        """
        params = {
            'key': key,
            'nonce': nonce,
        }
        api_path = '/v1/sys/generate-root/update'
        response = self._adapter.put(
            url=api_path,
            json=params,
        )
        return response.json()

    def cancel_root_generation(self):
        """Cancel any in-progress root generation attempt.

        This clears any progress made. This must be called to change the OTP or PGP key being used.

        Supported methods:
            DELETE: /sys/generate-root/attempt. Produces: 204 (empty body)

        :return: The response of the request.
        :rtype: request.Response
        """
        api_path = '/v1/sys/generate-root/attempt'
        response = self._adapter.delete(
            url=api_path,
        )
        return response

    def get_encryption_key_status(self):
        """Read information about the current encryption key used by Vault.

        Supported methods:
            GET: /sys/key-status. Produces: 200 application/json

        :return: JSON response with information regarding the current encryption key used by Vault.
        :rtype: dict
        """
        api_path = '/v1/sys/key-status'
        response = self._adapter.get(
            url=api_path,
        )
        return response.json()

    def rotate_encryption_key(self):
        """Trigger a rotation of the backend encryption key.

        This is the key that is used to encrypt data written to the storage backend, and is not provided to operators.
        This operation is done online. Future values are encrypted with the new key, while old values are decrypted with
        previous encryption keys.

        This path requires sudo capability in addition to update.

        Supported methods:
            PUT: /sys/rorate. Produces: 204 (empty body)

        :return: The response of the request.
        :rtype: requests.Response
        """
        api_path = '/v1/sys/rotate'
        response = self._adapter.put(
            url=api_path,
        )
        return response

    def read_rekey_progress(self, recovery_key=False):
        """Read the configuration and progress of the current rekey attempt.

        Supported methods:
            GET: /sys/rekey-recovery-key/init. Produces: 200 application/json
            GET: /sys/rekey/init. Produces: 200 application/json

        :param recovery_key: If true, send requests to "rekey-recovery-key" instead of "rekey" api path.
        :type recovery_key: bool
        :return: The JSON response of the request.
        :rtype: requests.Response
        """
        api_path = '/v1/sys/rekey/init'
        if recovery_key:
            api_path = '/v1/sys/rekey-recovery-key/init'
        response = self._adapter.get(
            url=api_path,
        )
        return response.json()

    def start_rekey(self, secret_shares=5, secret_threshold=3, pgp_keys=None, backup=False, require_verification=False, recovery_key=False):
        """Initializes a new rekey attempt.

        Only a single recovery key rekeyattempt can take place at a time, and changing the parameters of a rekey
        requires canceling and starting a new rekey, which will also provide a new nonce.

        Supported methods:
            PUT: /sys/rekey/init. Produces: 204 (empty body)
            PUT: /sys/rekey-recovery-key/init. Produces: 204 (empty body)

        :param secret_shares: Specifies the number of shares to split the master key into.
        :type secret_shares: int
        :param secret_threshold: Specifies the number of shares required to reconstruct the master key. This must be
            less than or equal to secret_shares.
        :type secret_threshold: int
        :param pgp_keys: Specifies an array of PGP public keys used to encrypt the output unseal keys. Ordering is
            preserved. The keys must be base64-encoded from their original binary representation. The size of this array
            must be the same as secret_shares.
        :type pgp_keys: list
        :param backup: Specifies if using PGP-encrypted keys, whether Vault should also store a plaintext backup of the
            PGP-encrypted keys at core/unseal-keys-backup in the physical storage backend. These can then be retrieved
            and removed via the sys/rekey/backup endpoint.
        :type backup: bool
        :param require_verification: This turns on verification functionality. When verification is turned on, after
            successful authorization with the current unseal keys, the new unseal keys are returned but the master key
            is not actually rotated. The new keys must be provided to authorize the actual rotation of the master key.
            This ensures that the new keys have been successfully saved and protects against a risk of the keys being
            lost after rotation but before they can be persisted. This can be used with without pgp_keys, and when used
            with it, it allows ensuring that the returned keys can be successfully decrypted before committing to the
            new shares, which the backup functionality does not provide.
        :param recovery_key: If true, send requests to "rekey-recovery-key" instead of "rekey" api path.
        :type recovery_key: bool
        :type require_verification: bool
        :return: The JSON dict of the response.
        :rtype: dict | request.Response
        """
        params = {
            'secret_shares': secret_shares,
            'secret_threshold': secret_threshold,
            'require_verification': require_verification,
        }

        if pgp_keys:
            if len(pgp_keys) != secret_shares:
                raise ParamValidationError('length of pgp_keys argument must equal secret shares value')

            params['pgp_keys'] = pgp_keys
            params['backup'] = backup

        api_path = '/v1/sys/rekey/init'
        if recovery_key:
            api_path = '/v1/sys/rekey-recovery-key/init'
        response = self._adapter.put(
            url=api_path,
            json=params,
        )

        return response.json()

    def cancel_rekey(self, recovery_key=False):
        """Cancel any in-progress rekey.

        This clears the rekey settings as well as any progress made. This must be called to change the parameters of the
        rekey.

        Note: Verification is still a part of a rekey. If rekeying is canceled during the verification flow, the current
        unseal keys remain valid.

        Supported methods:
            DELETE: /sys/rekey/init. Produces: 204 (empty body)
            DELETE: /sys/rekey-recovery-key/init. Produces: 204 (empty body)

        :param recovery_key: If true, send requests to "rekey-recovery-key" instead of "rekey" api path.
        :type recovery_key: bool
        :return: The response of the request.
        :rtype: requests.Response
        """
        api_path = '/v1/sys/rekey/init'
        if recovery_key:
            api_path = '/v1/sys/rekey-recovery-key/init'
        response = self._adapter.delete(
            url=api_path,
        )
        return response

    def rekey(self, key, nonce=None, recovery_key=False):
        """Enter a single recovery key share to progress the rekey of the Vault.

        If the threshold number of recovery key shares is reached, Vault will complete the rekey. Otherwise, this API
        must be called multiple times until that threshold is met. The rekey nonce operation must be provided with each
        call.

        Supported methods:
            PUT: /sys/rekey/update. Produces: 200 application/json
            PUT: /sys/rekey-recovery-key/update. Produces: 200 application/json

        :param key: Specifies a single recovery share key.
        :type key: str | unicode
        :param nonce: Specifies the nonce of the rekey operation.
        :type nonce: str | unicode
        :param recovery_key: If true, send requests to "rekey-recovery-key" instead of "rekey" api path.
        :type recovery_key: bool
        :return: The JSON response of the request.
        :rtype: dict
        """
        params = {
            'key': key,
        }

        if nonce is not None:
            params['nonce'] = nonce

        api_path = '/v1/sys/rekey/update'
        if recovery_key:
            api_path = '/v1/sys/rekey-recovery-key/update'
        response = self._adapter.put(
            url=api_path,
            json=params,
        )
        return response.json()

    def rekey_multi(self, keys, nonce=None, recovery_key=False):
        """Enter multiple recovery key shares to progress the rekey of the Vault.

        If the threshold number of recovery key shares is reached, Vault will complete the rekey.

        :param keys: Specifies multiple recovery share keys.
        :type keys: list
        :param nonce: Specifies the nonce of the rekey operation.
        :type nonce: str | unicode
        :param recovery_key: If true, send requests to "rekey-recovery-key" instead of "rekey" api path.
        :type recovery_key: bool
        :return: The last response of the rekey request.
        :rtype: response.Request
        """
        result = None

        for key in keys:
            result = self.rekey(
                key=key,
                nonce=nonce,
                recovery_key=recovery_key,
            )
            if result.get('complete'):
                break

        return result

    def read_backup_keys(self, recovery_key=False):
        """Retrieve the backup copy of PGP-encrypted unseal keys.

        The returned value is the nonce of the rekey operation and a map of PGP key fingerprint to hex-encoded
        PGP-encrypted key.

        Supported methods:
            PUT: /sys/rekey/backup. Produces: 200 application/json
            PUT: /sys/rekey-recovery-key/backup. Produces: 200 application/json

        :param recovery_key: If true, send requests to "rekey-recovery-key" instead of "rekey" api path.
        :type recovery_key: bool
        :return: The JSON response of the request.
        :rtype: dict
        """
        api_path = '/v1/sys/rekey/backup'
        if recovery_key:
            api_path = '/v1/sys/rekey-recovery-key/backup'
        response = self._adapter.get(
            url=api_path,
        )
        return response.json()
