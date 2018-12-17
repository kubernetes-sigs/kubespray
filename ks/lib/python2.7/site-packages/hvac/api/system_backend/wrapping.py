from hvac.api.system_backend.system_backend_mixin import SystemBackendMixin


class Wrapping(SystemBackendMixin):

    def unwrap(self, token=None):
        """Return the original response inside the given wrapping token.

        Unlike simply reading cubbyhole/response (which is deprecated), this endpoint provides additional validation
        checks on the token, returns the original value on the wire rather than a JSON string representation of it, and
        ensures that the response is properly audit-logged.

        Supported methods:
            POST: /sys/wrapping/unwrap. Produces: 200 application/json

        :param token: Specifies the wrapping token ID. This is required if the client token is not the wrapping token.
            Do not use the wrapping token in both locations.
        :type token: str | unicode
        :return: The JSON response of the request.
        :rtype: dict
        """
        params = {}
        if token is not None:
            params['token'] = token

        api_path = '/v1/sys/wrapping/unwrap'
        response = self._adapter.post(
            url=api_path,
            json=params,
        )

        return response.json()
