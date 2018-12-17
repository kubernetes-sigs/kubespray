from hvac.api.system_backend.system_backend_mixin import SystemBackendMixin


class Lease(SystemBackendMixin):

    def read_lease(self, lease_id):
        """Retrieve lease metadata.

        Supported methods:
            PUT: /sys/leases/lookup. Produces: 200 application/json

        :param lease_id: the ID of the lease to lookup.
        :type lease_id: str | unicode
        :return: Parsed JSON response from the leases PUT request
        :rtype: dict.
        """
        params = {
            'lease_id': lease_id
        }
        api_path = '/v1/sys/leases/lookup'
        response = self._adapter.put(
            url=api_path,
            json=params
        )
        return response.json()

    def list_leases(self, prefix):
        """Retrieve a list of lease ids.

        Supported methods:
            LIST: /sys/leases/lookup/{prefix}. Produces: 200 application/json

        :param prefix: Lease prefix to filter list by.
        :type prefix: str | unicode
        :return: The JSON response of the request.
        :rtype: dict
        """
        api_path = '/v1/sys/leases/lookup/{prefix}'.format(prefix=prefix)
        response = self._adapter.list(
            url=api_path,
        )
        return response.json()

    def renew_lease(self, lease_id, increment=None):
        """Renew a lease, requesting to extend the lease.

        Supported methods:
            PUT: /sys/leases/renew. Produces: 200 application/json

        :param lease_id: The ID of the lease to extend.
        :type lease_id: str | unicode
        :param increment: The requested amount of time (in seconds) to extend the lease.
        :type increment: int
        :return: The JSON response of the request
        :rtype: dict
        """
        params = {
            'lease_id': lease_id,
            'increment': increment,
        }
        api_path = '/v1/sys/leases/renew'
        response = self._adapter.put(
            url=api_path,
            json=params,
        )
        return response.json()

    def revoke_lease(self, lease_id):
        """Revoke a lease immediately.

        Supported methods:
            PUT: /sys/leases/revoke. Produces: 204 (empty body)

        :param lease_id: Specifies the ID of the lease to revoke.
        :type lease_id: str | unicode
        :return: The response of the request.
        :rtype: requests.Response
        """
        params = {
            'lease_id': lease_id,
        }
        api_path = '/v1/sys/leases/revoke'
        return self._adapter.put(
            url=api_path,
            json=params,
        )

    def revoke_prefix(self, prefix):
        """Revoke all secrets (via a lease ID prefix) or tokens (via the tokens' path property) generated under a given
        prefix immediately.

        This requires sudo capability and access to it should be tightly controlled as it can be used to revoke very
        large numbers of secrets/tokens at once.

        Supported methods:
            PUT: /sys/leases/revoke-prefix/{prefix}. Produces: 204 (empty body)


        :param prefix: The prefix to revoke.
        :type prefix: str | unicode
        :return: The response of the request.
        :rtype: requests.Response
        """
        params = {
            'prefix': prefix,
        }
        api_path = '/v1/sys/leases/revoke-prefix/{prefix}'.format(prefix=prefix)
        return self._adapter.put(
            url=api_path,
            json=params,
        )

    def revoke_force(self, prefix):
        """Revoke all secrets or tokens generated under a given prefix immediately.

        Unlike revoke_prefix, this path ignores backend errors encountered during revocation. This is potentially very
        dangerous and should only be used in specific emergency situations where errors in the backend or the connected
        backend service prevent normal revocation.

        Supported methods:
            PUT: /sys/leases/revoke-force/{prefix}. Produces: 204 (empty body)

        :param prefix: The prefix to revoke.
        :type prefix: str | unicode
        :return: The response of the request.
        :rtype: requests.Response
        """
        params = {
            'prefix': prefix,
        }
        api_path = '/v1/sys/leases/revoke-force/{prefix}'.format(prefix=prefix)
        return self._adapter.put(
            url=api_path,
            json=params,
        )
