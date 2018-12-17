from hvac.api.system_backend.system_backend_mixin import SystemBackendMixin


class Mount(SystemBackendMixin):

    def list_mounted_secrets_engines(self):
        """Lists all the mounted secrets engines.

        Supported methods:
            POST: /sys/mounts. Produces: 200 application/json

        :return: JSON response of the request.
        :rtype: dict
        """
        response = self._adapter.get('/v1/sys/mounts')
        return response.json()

    def enable_secrets_engine(self, backend_type, path=None, description=None, config=None, plugin_name=None,
                              options=None, local=False, seal_wrap=False):
        """Enable a new secrets engine at the given path.

        Supported methods:
            POST: /sys/mounts/{path}. Produces: 204 (empty body)

        :param backend_type: The name of the backend type, such as "github" or "token".
        :type backend_type: str | unicode
        :param path: The path to mount the method on. If not provided, defaults to the value of the "method_type"
            argument.
        :type path: str | unicode
        :param description: A human-friendly description of the mount.
        :type description: str | unicode
        :param config: Configuration options for this mount. These are the possible values:

            * **default_lease_ttl**: The default lease duration, specified as a string duration like "5s" or "30m".
            * **max_lease_ttl**: The maximum lease duration, specified as a string duration like "5s" or "30m".
            * **force_no_cache**: Disable caching.
            * **plugin_name**: The name of the plugin in the plugin catalog to use.
            * **audit_non_hmac_request_keys**: Comma-separated list of keys that will not be HMAC'd by audit devices in
              the request data object.
            * **audit_non_hmac_response_keys**: Comma-separated list of keys that will not be HMAC'd by audit devices in
              the response data object.
            * **listing_visibility**: Specifies whether to show this mount in the UI-specific listing endpoint. ("unauth" or "hidden")
            * **passthrough_request_headers**: Comma-separated list of headers to whitelist and pass from the request to
              the backend.
        :type config: dict
        :param options: Specifies mount type specific options that are passed to the backend.

            * **version**: <KV> The version of the KV to mount. Set to "2" for mount KV v2.
        :type options: dict
        :param plugin_name: Specifies the name of the plugin to use based from the name in the plugin catalog. Applies only to plugin backends.
        :type plugin_name: str | unicode
        :param local: <Vault enterprise only> Specifies if the auth method is a local only. Local auth methods are not
            replicated nor (if a secondary) removed by replication.
        :type local: bool
        :param seal_wrap: <Vault enterprise only> Enable seal wrapping for the mount.
        :type seal_wrap: bool
        :return: The response of the request.
        :rtype: requests.Response
        """
        if path is None:
            path = backend_type

        params = {
            'type': backend_type,
            'description': description,
            'config': config,
            'options': options,
            'plugin_name': plugin_name,
            'local': local,
            'seal_wrap': seal_wrap,
        }

        api_path = '/v1/sys/mounts/{path}'.format(path=path)
        return self._adapter.post(
            url=api_path,
            json=params,
        )

    def disable_secrets_engine(self, path):
        """Disable the mount point specified by the provided path.

        Supported methods:
            DELETE: /sys/mounts/{path}. Produces: 204 (empty body)

        :param path: Specifies the path where the secrets engine will be mounted. This is specified as part of the URL.
        :type path: str | unicode
        :return: The response of the request.
        :rtype: requests.Response
        """
        api_path = '/v1/sys/mounts/{path}'.format(path=path)
        return self._adapter.delete(
            url=api_path,
        )

    def read_mount_configuration(self, path):
        """Read the given mount's configuration.

        Unlike the mounts endpoint, this will return the current time in seconds for each TTL, which may be the system
        default or a mount-specific value.

        Supported methods:
            GET: /sys/mounts/{path}/tune. Produces: 200 application/json

        :param path: Specifies the path where the secrets engine will be mounted. This is specified as part of the URL.
        :type path: str | unicode
        :return: The JSON response of the request.
        :rtype: requests.Response
        """
        api_path = '/v1/sys/mounts/{path}/tune'.format(path=path)
        response = self._adapter.get(
            url=api_path,
        )
        return response.json()

    def tune_mount_configuration(self, path, default_lease_ttl=None, max_lease_ttl=None, description=None,
                                 audit_non_hmac_request_keys=None, audit_non_hmac_response_keys=None,
                                 listing_visibility=None, passthrough_request_headers=None):
        """Tune configuration parameters for a given mount point.

        Supported methods:
            POST: /sys/mounts/{path}/tune. Produces: 204 (empty body)

        :param path: Specifies the path where the secrets engine will be mounted. This is specified as part of the URL.
        :type path: str | unicode
        :param mount_point: The path the associated secret backend is mounted
        :type mount_point: str
        :param description: Specifies the description of the mount. This overrides the current stored value, if any.
        :type description: str
        :param default_lease_ttl: Default time-to-live. This overrides the global default. A value of 0 is equivalent to
            the system default TTL
        :type default_lease_ttl: int
        :param max_lease_ttl: Maximum time-to-live. This overrides the global default. A value of 0 are equivalent and
            set to the system max TTL.
        :type max_lease_ttl: int
        :param audit_non_hmac_request_keys: Specifies the comma-separated list of keys that will not be HMAC'd by audit
            devices in the request data object.
        :type audit_non_hmac_request_keys: list
        :param audit_non_hmac_response_keys: Specifies the comma-separated list of keys that will not be HMAC'd by audit
            devices in the response data object.
        :type audit_non_hmac_response_keys: list
        :param listing_visibility: Speficies whether to show this mount in the UI-specific listing endpoint. Valid
            values are "unauth" or "".
        :type listing_visibility: str
        :param passthrough_request_headers: Comma-separated list of headers to whitelist and pass from the request
            to the backend.
        :type passthrough_request_headers: str
        :return: The response from the request.
        :rtype: request.Response
        """
        # All parameters are optional for this method. Until/unless we include input validation, we simply loop over the
        # parameters and add which parameters are set.
        optional_parameters = [
            'default_lease_ttl',
            'max_lease_ttl',
            'description',
            'audit_non_hmac_request_keys',
            'audit_non_hmac_response_keys',
            'listing_visibility',
            'passthrough_request_headers',
        ]
        params = {}
        for optional_parameter in optional_parameters:
            if locals().get(optional_parameter) is not None:
                params[optional_parameter] = locals().get(optional_parameter)

        api_path = '/v1/sys/mounts/{path}/tune'.format(path=path)
        return self._adapter.post(
            url=api_path,
            json=params,
        )

    def move_backend(self, from_path, to_path):
        """Move an already-mounted backend to a new mount point.

        Supported methods:
            POST: /sys/remount. Produces: 204 (empty body)

        :param from_path: Specifies the previous mount point.
        :type from_path: str | unicode
        :param to_path: Specifies the new destination mount point.
        :type to_path: str | unicode
        :return: The response of the request.
        :rtype: requests.Response
        """
        params = {
            'from': from_path,
            'to': to_path,
        }
        api_path = '/v1/sys/remount'
        return self._adapter.post(
            url=api_path,
            json=params,
        )
