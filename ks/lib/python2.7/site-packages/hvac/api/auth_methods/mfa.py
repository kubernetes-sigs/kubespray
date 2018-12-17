#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Multi-factor authentication methods module."""
from hvac.api.vault_api_base import VaultApiBase
from hvac import exceptions

SUPPORTED_MFA_TYPES = [
    'duo',
]
SUPPORTED_AUTH_METHODS = [
    'ldap',
    'okta',
    'radius',
    'userpass'
]


class Mfa(VaultApiBase):
    """Multi-factor authentication Auth Method (API).

    .. warning::
        This class's methods correspond to a legacy / unsupported set of Vault API routes. Please see the reference link
        for additional context.

    Reference: https://www.vaultproject.io/docs/auth/mfa.html
    """

    def configure(self, mount_point, mfa_type='duo', force=False):
        """Configure MFA for a supported method.

        This endpoint allows you to turn on multi-factor authentication with a given backend.
        Currently only Duo is supported.

        Supported methods:
            POST: /auth/{mount_point}/mfa_config. Produces: 204 (empty body)

        :param mount_point: The "path" the method/backend was mounted on.
        :type mount_point: str | unicode
        :param mfa_type: Enables MFA with given backend (available: duo)
        :type mfa_type: str | unicode
        :param force: If True, make the "mfa_config" request regardless of circumstance. If False (the default), verify
            the provided mount_point is available and one of the types of methods supported by this feature.
        :type force: bool
        :return: The response of the configure MFA request.
        :rtype: requests.Response
        """
        if mfa_type != 'duo' and not force:
            # The situation described via this exception is not likely to change in the future.
            # However we provided that flexibility here just in case.
            error_msg = 'Unsupported mfa_type argument provided "{arg}", supported types: "{mfa_types}"'
            raise exceptions.ParamValidationError(error_msg.format(
                mfa_types=','.join(SUPPORTED_MFA_TYPES),
                arg=mfa_type,
            ))
        params = {
            'type': mfa_type,
        }

        api_path = '/v1/auth/{mount_point}/mfa_config'.format(
            mount_point=mount_point
        )
        return self._adapter.post(
            url=api_path,
            json=params,
        )

    def read_configuration(self, mount_point):
        """Read the MFA configuration.

        Supported methods:
            GET: /auth/{mount_point}/mfa_config. Produces: 200 application/json


        :param mount_point: The "path" the method/backend was mounted on.
        :type mount_point: str | unicode
        :return: The JSON response of the read_configuration request.
        :rtype: dict
        """
        api_path = '/v1/auth/{mount_point}/mfa_config'.format(
            mount_point=mount_point,
        )
        response = self._adapter.get(url=api_path)
        return response.json()

    def configure_duo_access(self, mount_point, host, integration_key, secret_key):
        """Configure the access keys and host for Duo API connections.

        To authenticate users with Duo, the backend needs to know what host to connect to and must authenticate with an
        integration key and secret key. This endpoint is used to configure that information.

        Supported methods:
            POST: /auth/{mount_point}/duo/access. Produces: 204 (empty body)

        :param mount_point: The "path" the method/backend was mounted on.
        :type mount_point: str | unicode
        :param host: Duo API host
        :type host: str | unicode
        :param integration_key: Duo integration key
        :type integration_key: Duo secret key
        :param secret_key: The "path" the method/backend was mounted on.
        :type secret_key: str | unicode
        :return: The response of the configure_duo_access request.
        :rtype: requests.Response
        """
        params = {
            'host': host,
            'ikey': integration_key,
            'skey': secret_key,
        }
        api_path = '/v1/auth/{mount_point}/duo/access'.format(
            mount_point=mount_point,
        )
        return self._adapter.post(
            url=api_path,
            json=params,
        )

    def configure_duo_behavior(self, mount_point, push_info=None, user_agent=None, username_format='%s'):
        """Configure Duo second factor behavior.

        This endpoint allows you to configure how the original auth method username maps to the Duo username by
        providing a template format string.

        Supported methods:
            POST: /auth/{mount_point}/duo/config. Produces: 204 (empty body)


        :param mount_point: The "path" the method/backend was mounted on.
        :type mount_point: str | unicode
        :param push_info: A string of URL-encoded key/value pairs that provides additional context about the
            authentication attempt in the Duo Mobile app
        :type push_info: str | unicode
        :param user_agent: User agent to connect to Duo (default "")
        :type user_agent: str | unicode
        :param username_format: Format string given auth method username as argument to create Duo username
            (default '%s')
        :type username_format: str | unicode
        :return: The response of the configure_duo_behavior request.
        :rtype: requests.Response
        """
        params = {
            'username_format': username_format,
        }
        if push_info is not None:
            params['push_info'] = push_info
        if user_agent is not None:
            params['user_agent'] = user_agent
        api_path = '/v1/auth/{mount_point}/duo/config'.format(
            mount_point=mount_point,
        )
        return self._adapter.post(
            url=api_path,
            json=params,
        )

    def read_duo_behavior_configuration(self, mount_point):
        """Read the Duo second factor behavior configuration.

        Supported methods:
            GET: /auth/{mount_point}/duo/config. Produces: 200 application/json


        :param mount_point: The "path" the method/backend was mounted on.
        :type mount_point: str | unicode
        :return: The JSON response of the read_duo_behavior_configuration request.
        :rtype: dict
        """
        api_path = '/v1/auth/{mount_point}/duo/config'.format(
            mount_point=mount_point,
        )
        response = self._adapter.get(url=api_path)
        return response.json()
