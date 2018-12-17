from hvac.api.system_backend.system_backend_mixin import SystemBackendMixin


class Seal(SystemBackendMixin):

    def is_sealed(self):
        """Determine if  Vault is sealed.

        :return: True if Vault is seal, False otherwise.
        :rtype: bool
        """
        seal_status = self.read_seal_status()
        return seal_status['sealed']

    def read_seal_status(self):
        """Read the seal status of the Vault.

        This is an unauthenticated endpoint.

        Supported methods:
            GET: /sys/seal-status. Produces: 200 application/json

        :return: The JSON response of the request.
        :rtype: dict
        """
        api_path = '/v1/sys/seal-status'
        response = self._adapter.get(
            url=api_path,
        )
        return response.json()

    def seal(self):
        """Seal the Vault.

        In HA mode, only an active node can be sealed. Standby nodes should be restarted to get the same effect.
        Requires a token with root policy or sudo capability on the path.

        Supported methods:
            PUT: /sys/seal. Produces: 204 (empty body)

        :return: The response of the request.
        :rtype: requests.Response
        """
        api_path = '/v1/sys/seal'
        return self._adapter.put(
            url=api_path,
        )

    def submit_unseal_key(self, key=None, reset=False, migrate=False):
        """Enter a single master key share to progress the unsealing of the Vault.

        If the threshold number of master key shares is reached, Vault will attempt to unseal the Vault. Otherwise, this
        API must be called multiple times until that threshold is met.

        Either the key or reset parameter must be provided; if both are provided, reset takes precedence.

        Supported methods:
            PUT: /sys/unseal. Produces: 200 application/json

        :param key: Specifies a single master key share. This is required unless reset is true.
        :type key: str | unicode
        :param reset: Specifies if previously-provided unseal keys are discarded and the unseal process is reset.
        :type reset: bool
        :param migrate: Available in 1.0 Beta - Used to migrate the seal from shamir to autoseal or autoseal to shamir.
            Must be provided on all unseal key calls.
        :type: migrate: bool
        :return: The JSON response of the request.
        :rtype: dict
        """

        params = {
            'migrate': migrate,
        }
        if not reset and key is not None:
            params['key'] = key
        elif reset:
            params['reset'] = reset

        api_path = '/v1/sys/unseal'
        response = self._adapter.put(
            url=api_path,
            json=params,
        )
        return response.json()

    def submit_unseal_keys(self, keys, migrate=False):
        """Enter multiple master key share to progress the unsealing of the Vault.

        :param key: List of master key shares.
        :type key: List[str]
        :param migrate: Available in 1.0 Beta - Used to migrate the seal from shamir to autoseal or autoseal to shamir.
            Must be provided on all unseal key calls.
        :type: migrate: bool
        :return: The JSON response of the last unseal request.
        :rtype: dict
        """
        result = None

        for key in keys:
            result = self.submit_unseal_key(
                key=key,
                migrate=migrate,
            )
            if not result['sealed']:
                break

        return result
