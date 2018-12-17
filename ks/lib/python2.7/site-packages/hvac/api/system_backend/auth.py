#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Support for "Auth"-related System Backend Methods."""
from hvac.api.system_backend.system_backend_mixin import SystemBackendMixin
from hvac.utils import validate_list_of_strings_param, list_to_comma_delimited
from hvac import exceptions


class Auth(SystemBackendMixin):

    def list_auth_methods(self):
        """List all enabled auth methods.

        Supported methods:
            GET: /sys/auth. Produces: 200 application/json

        :return: The JSON response of the request.
        :rtype: dict
        """
        api_path = '/v1/sys/auth'
        response = self._adapter.get(
            url=api_path,
        )
        return response.json()

    def enable_auth_method(self, method_type, description=None, config=None, plugin_name=None, local=False, path=None):
        """Enable a new auth method.

        After enabling, the auth method can be accessed and configured via the auth path specified as part of the URL.
        This auth path will be nested under the auth prefix.

        Supported methods:
            POST: /sys/auth/{path}. Produces: 204 (empty body)

        :param method_type: The name of the authentication method type, such as "github" or "token".
        :type method_type: str | unicode
        :param description: A human-friendly description of the auth method.
        :type description: str | unicode
        :param config: Configuration options for this auth method. These are the possible values:

            * **default_lease_ttl**: The default lease duration, specified as a string duration like "5s" or "30m".
            * **max_lease_ttl**: The maximum lease duration, specified as a string duration like "5s" or "30m".
            * **audit_non_hmac_request_keys**: Comma-separated list of keys that will not be HMAC'd by audit devices in
              the request data object.
            * **audit_non_hmac_response_keys**: Comma-separated list of keys that will not be HMAC'd by audit devices in
              the response data object.
            * **listing_visibility**: Speficies whether to show this mount in the UI-specific listing endpoint.
            * **passthrough_request_headers**: Comma-separated list of headers to whitelist and pass from the request to
              the backend.
        :type config: dict
        :param plugin_name: The name of the auth plugin to use based from the name in the plugin catalog. Applies only
            to plugin methods.
        :type plugin_name: str | unicode
        :param local: <Vault enterprise only> Specifies if the auth method is a local only. Local auth methods are not
            replicated nor (if a secondary) removed by replication.
        :type local: bool
        :param path: The path to mount the method on. If not provided, defaults to the value of the "method_type"
            argument.
        :type path: str | unicode
        :return: The response of the request.
        :rtype: requests.Response
        """
        if path is None:
            path = method_type

        params = {
            'type': method_type,
            'description': description,
            'config': config,
            'plugin_name': plugin_name,
            'local': local,
        }
        api_path = '/v1/sys/auth/{path}'.format(path=path)
        return self._adapter.post(
            url=api_path,
            json=params
        )

    def disable_auth_method(self, path):
        """Disable the auth method at the given auth path.

        Supported methods:
            DELETE: /sys/auth/{path}. Produces: 204 (empty body)

        :param path: The path the method was mounted on. If not provided, defaults to the value of the "method_type"
            argument.
        :type path: str | unicode
        :return: The response of the request.
        :rtype: requests.Response
        """
        api_path = '/v1/sys/auth/{path}'.format(path=path)
        return self._adapter.delete(
            url=api_path,
        )

    def read_auth_method_tuning(self, path):
        """Read the given auth path's configuration.

        This endpoint requires sudo capability on the final path, but the same functionality can be achieved without
        sudo via sys/mounts/auth/[auth-path]/tune.

        Supported methods:
            GET: /sys/auth/{path}/tune. Produces: 200 application/json

        :param path: The path the method was mounted on. If not provided, defaults to the value of the "method_type"
            argument.
        :type path: str | unicode
        :return: The JSON response of the request.
        :rtype: dict
        """
        api_path = '/v1/sys/auth/{path}/tune'.format(
            path=path,
        )
        response = self._adapter.get(
            url=api_path,
        )
        return response.json()

    def tune_auth_method(self, path, default_lease_ttl=None, max_lease_ttl=None, description=None,
                         audit_non_hmac_request_keys=None, audit_non_hmac_response_keys=None, listing_visibility='',
                         passthrough_request_headers=None):
        """Tune configuration parameters for a given auth path.

        This endpoint requires sudo capability on the final path, but the same functionality can be achieved without
        sudo via sys/mounts/auth/[auth-path]/tune.

        Supported methods:
            POST: /sys/auth/{path}/tune. Produces: 204 (empty body)

        :param path: The path the method was mounted on. If not provided, defaults to the value of the "method_type"
            argument.
        :type path: str | unicode
        :param default_lease_ttl: Specifies the default time-to-live. If set on a specific auth path, this overrides the
            global default.
        :type default_lease_ttl: int
        :param max_lease_ttl: The maximum time-to-live. If set on a specific auth path, this overrides the global
            default.
        :type max_lease_ttl: int
        :param description: Specifies the description of the mount. This overrides the current stored value, if any.
        :type description: str | unicode
        :param audit_non_hmac_request_keys: Specifies the list of keys that will not be HMAC'd by audit devices in the
            request data object.
        :type audit_non_hmac_request_keys: array
        :param audit_non_hmac_response_keys: Specifies the list of keys that will not be HMAC'd by audit devices in the
            response data object.
        :type audit_non_hmac_response_keys: list
        :param listing_visibility: Specifies whether to show this mount in the UI-specific listing endpoint. Valid
            values are "unauth" or "".
        :type listing_visibility: list
        :param passthrough_request_headers: List of headers to whitelist and pass from the request to the backend.
        :type passthrough_request_headers: list
        :return: The response of the request.
        :rtype: requests.Response
        """

        if listing_visibility not in ['unauth', '']:
            error_msg = 'invalid listing_visibility argument provided: "{arg}"; valid values: "unauth" or ""'.format(
                arg=listing_visibility,
            )
            raise exceptions.ParamValidationError(error_msg)

        # All parameters are optional for this method. Until/unless we include input validation, we simply loop over the
        # parameters and add which parameters are set.
        optional_parameters = {
            'default_lease_ttl': dict(),
            'max_lease_ttl': dict(),
            'description': dict(),
            'audit_non_hmac_request_keys': dict(comma_delimited_list=True),
            'audit_non_hmac_response_keys': dict(comma_delimited_list=True),
            'listing_visibility': dict(),
            'passthrough_request_headers': dict(comma_delimited_list=True),
        }
        params = {}
        for optional_parameter, parameter_specification in optional_parameters.items():
            if locals().get(optional_parameter) is not None:
                if parameter_specification.get('comma_delimited_list'):
                    argument = locals().get(optional_parameter)
                    validate_list_of_strings_param(optional_parameter, argument)
                    params[optional_parameter] = list_to_comma_delimited(argument)
                else:
                    params[optional_parameter] = locals().get(optional_parameter)

        api_path = '/v1/sys/auth/{path}/tune'.format(path=path)
        return self._adapter.post(
            url=api_path,
            json=params,
        )
