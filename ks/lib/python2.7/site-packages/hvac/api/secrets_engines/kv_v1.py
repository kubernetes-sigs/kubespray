#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""KvV1 methods module."""
from hvac import exceptions
from hvac.api.vault_api_base import VaultApiBase

DEFAULT_MOUNT_POINT = 'secret'


class KvV1(VaultApiBase):
    """KV Secrets Engine - Version 1 (API).

    Reference: https://www.vaultproject.io/api/secrets/kv/kv-v1.html
    """

    def read_secret(self, path, mount_point=DEFAULT_MOUNT_POINT):
        """Retrieve the secret at the specified location.

        Supported methods:
            GET: /{mount_point}/{path}. Produces: 200 application/json


        :param path: Specifies the path of the secret to read. This is specified as part of the URL.
        :type path: str | unicode
        :param mount_point: The "path" the secret engine was mounted on.
        :type mount_point: str | unicode
        :return: The JSON response of the read_secret request.
        :rtype: dict
        """
        api_path = '/v1/{mount_point}/{path}'.format(mount_point=mount_point, path=path)
        response = self._adapter.get(
            url=api_path,
        )
        return response.json()

    def list_secrets(self, path, mount_point=DEFAULT_MOUNT_POINT):
        """Return a list of key names at the specified location.

        Folders are suffixed with /. The input must be a folder; list on a file will not return a value. Note that no
        policy-based filtering is performed on keys; do not encode sensitive information in key names. The values
        themselves are not accessible via this command.

        Supported methods:
            LIST: /{mount_point}/{path}. Produces: 200 application/json

        :param path: Specifies the path of the secrets to list.
            This is specified as part of the URL.
        :type path: str | unicode
        :param mount_point: The "path" the secret engine was mounted on.
        :type mount_point: str | unicode
        :return: The JSON response of the list_secrets request.
        :rtype: dict
        """
        api_path = '/v1/{mount_point}/{path}'.format(mount_point=mount_point, path=path)
        response = self._adapter.list(
            url=api_path,
        )
        return response.json()

    def create_or_update_secret(self, path, secret, method=None, mount_point=DEFAULT_MOUNT_POINT):
        """Store a secret at the specified location.

        If the value does not yet exist, the calling token must have an ACL policy granting the create capability.
        If the value already exists, the calling token must have an ACL policy granting the update capability.

        Supported methods:
            POST: /{mount_point}/{path}. Produces: 204 (empty body)
            PUT: /{mount_point}/{path}. Produces: 204 (empty body)

        :param path: Specifies the path of the secrets to create/update. This is specified as part of the URL.
        :type path: str | unicode
        :param secret: Specifies keys, paired with associated values, to be held at the given location. Multiple
            key/value pairs can be specified, and all will be returned on a read operation. A key called ttl will
            trigger some special behavior. See the Vault KV secrets engine documentation for details.
        :type secret: dict
        :param method: Optional parameter to explicitly request a POST (create) or PUT (update) request to the selected
            kv secret engine. If no argument is provided for this parameter, hvac attempts to intelligently determine
            which method is appropriate.
        :type method: str | unicode
        :param mount_point: The "path" the secret engine was mounted on.
        :type mount_point: str | unicode
        :return: The response of the create_or_update_secret request.
        :rtype: requests.Response
        """
        if method is None:
            # If no method was selected by the caller, use the result of a `read_secret()` call to determine if we need
            # to perform an update (PUT) or creation (POST) request.
            try:
                self.read_secret(
                    path=path,
                    mount_point=mount_point,
                )
                method = 'PUT'
            except exceptions.InvalidPath:
                method = 'POST'

        if method == 'POST':
            api_path = '/v1/{mount_point}/{path}'.format(mount_point=mount_point, path=path)
            return self._adapter.post(
                url=api_path,
                json=secret,
            )

        elif method == 'PUT':
            api_path = '/v1/{mount_point}/{path}'.format(mount_point=mount_point, path=path)
            return self._adapter.post(
                url=api_path,
                json=secret,
            )

        else:
            error_message = '"method" parameter provided invalid value; POST or PUT allowed, "{method}" provided'.format(method=method)
            raise exceptions.ParamValidationError(error_message)

    def delete_secret(self, path, mount_point=DEFAULT_MOUNT_POINT):
        """Delete the secret at the specified location.

        Supported methods:
            DELETE: /{mount_point}/{path}. Produces: 204 (empty body)


        :param path: Specifies the path of the secret to delete.
            This is specified as part of the URL.
        :type path: str | unicode
        :param mount_point: The "path" the secret engine was mounted on.
        :type mount_point: str | unicode
        :return: The response of the delete_secret request.
        :rtype: requests.Response
        """
        api_path = '/v1/{mount_point}/{path}'.format(mount_point=mount_point, path=path)
        return self._adapter.delete(
            url=api_path,
        )
