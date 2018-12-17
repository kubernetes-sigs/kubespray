#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""KvV2 methods module."""
from hvac import exceptions
from hvac.api.vault_api_base import VaultApiBase

DEFAULT_MOUNT_POINT = 'secret'


class KvV2(VaultApiBase):
    """KV Secrets Engine - Version 2 (API).

    Reference: https://www.vaultproject.io/api/secret/kv/kv-v2.html
    """

    def configure(self, max_versions=10, cas_required=None, mount_point=DEFAULT_MOUNT_POINT):
        """Configure backend level settings that are applied to every key in the key-value store.

        Supported methods:
            POST: /{mount_point}/config. Produces: 204 (empty body)


        :param max_versions: The number of versions to keep per key. This value applies to all keys, but a key's
            metadata setting can overwrite this value. Once a key has more than the configured allowed versions the
            oldest version will be permanently deleted. Defaults to 10.
        :type max_versions: int
        :param cas_required: If true all keys will require the cas parameter to be set on all write requests.
        :type cas_required: bool
        :param mount_point: The "path" the secret engine was mounted on.
        :type mount_point: str | unicode
        :return: The response of the request.
        :rtype: requests.Response
        """
        params = {
            'max_versions': max_versions,
        }
        if cas_required is not None:
            params['cas_required'] = cas_required
        api_path = '/v1/{mount_point}/config'.format(mount_point=mount_point)
        return self._adapter.post(
            url=api_path,
            json=params,
        )

    def read_configuration(self, mount_point=DEFAULT_MOUNT_POINT):
        """Read the KV Version 2 configuration.

        Supported methods:
            GET: /auth/{mount_point}/config. Produces: 200 application/json


        :param mount_point: The "path" the secret engine was mounted on.
        :type mount_point: str | unicode
        :return: The JSON response of the request.
        :rtype: dict
        """
        api_path = '/v1/{mount_point}/config'.format(
            mount_point=mount_point,
        )
        response = self._adapter.get(url=api_path)
        return response.json()

    def read_secret_version(self, path, version=None, mount_point=DEFAULT_MOUNT_POINT):
        """Retrieve the secret at the specified location.

        Supported methods:
            GET: /{mount_point}/data/{path}. Produces: 200 application/json


        :param path: Specifies the path of the secret to read. This is specified as part of the URL.
        :type path: str | unicode
        :param version: Specifies the version to return. If not set the latest version is returned.
        :type version: int
        :param mount_point: The "path" the secret engine was mounted on.
        :type mount_point: str | unicode
        :return: The JSON response of the request.
        :rtype: dict
        """
        params = {}
        if version is not None:
            params['version'] = version
        api_path = '/v1/{mount_point}/data/{path}'.format(mount_point=mount_point, path=path)
        response = self._adapter.get(
            url=api_path,
            params=params,
        )
        return response.json()

    def create_or_update_secret(self, path, secret, cas=None, mount_point=DEFAULT_MOUNT_POINT):
        """Create a new version of a secret at the specified location.

        If the value does not yet exist, the calling token must have an ACL policy granting the create capability. If
        the value already exists, the calling token must have an ACL policy granting the update capability.

        Supported methods:
            POST: /{mount_point}/data/{path}. Produces: 200 application/json

        :param path: Path
        :type path: str | unicode
        :param cas: Set the "cas" value to use a Check-And-Set operation. If not set the write will be allowed. If set
            to 0 a write will only be allowed if the key doesn't exist. If the index is non-zero the write will only be
            allowed if the key's current version matches the version specified in the cas parameter.
        :type cas: int
        :param secret: The contents of the "secret" dict will be stored and returned on read.
        :type secret: dict
        :param mount_point: The "path" the secret engine was mounted on.
        :type mount_point: str | unicode
        :return: The JSON response of the request.
        :rtype: dict
        """
        params = {
            'options': {},
            'data': secret,
        }

        if cas is not None:
            params['options']['cas'] = cas

        api_path = '/v1/{mount_point}/data/{path}'.format(mount_point=mount_point, path=path)
        response = self._adapter.post(
            url=api_path,
            json=params,
        )
        return response.json()

    def patch(self, path, secret, mount_point=DEFAULT_MOUNT_POINT):
        """Set or update data in the KV store without overwriting.

        :param path: Path
        :type path: str | unicode
        :param secret: The contents of the "secret" dict will be stored and returned on read.
        :type secret: dict
        :param mount_point: The "path" the secret engine was mounted on.
        :type mount_point: str | unicode
        :return: The JSON response of the create_or_update_secret request.
        :rtype: dict
        """
        # First, do a read.
        try:
            current_secret_version = self.read_secret_version(
                path=path,
                mount_point=mount_point,
            )
        except exceptions.InvalidPath:
            raise exceptions.InvalidPath('No value found at "{path}"; patch only works on existing data.'.format(path=path))

        # Update existing secret dict.
        patched_secret = current_secret_version['data']['data']
        patched_secret.update(secret)

        # Write back updated secret.
        return self.create_or_update_secret(
            path=path,
            cas=current_secret_version['data']['metadata']['version'],
            secret=patched_secret,
            mount_point=mount_point,
        )

    def delete_latest_version_of_secret(self, path, mount_point=DEFAULT_MOUNT_POINT):
        """Issue a soft delete of the secret's latest version at the specified location.

        This marks the version as deleted and will stop it from being returned from reads, but the underlying data will
        not be removed. A delete can be undone using the undelete path.

        Supported methods:
            DELETE: /{mount_point}/data/{path}. Produces: 204 (empty body)


        :param path: Specifies the path of the secret to delete. This is specified as part of the URL.
        :type path: str | unicode
        :param mount_point: The "path" the secret engine was mounted on.
        :type mount_point: str | unicode
        :return: The response of the request.
        :rtype: requests.Response
        """
        api_path = '/v1/{mount_point}/data/{path}'.format(mount_point=mount_point, path=path)
        return self._adapter.delete(
            url=api_path,
        )

    def delete_secret_versions(self, path, versions, mount_point=DEFAULT_MOUNT_POINT):
        """Issue a soft delete of the specified versions of the secret.

        This marks the versions as deleted and will stop them from being returned from reads,
        but the underlying data will not be removed. A delete can be undone using the
        undelete path.

        Supported methods:
            POST: /{mount_point}/delete/{path}. Produces: 204 (empty body)


        :param path: Specifies the path of the secret to delete. This is specified as part of the URL.
        :type path: str | unicode
        :param versions: The versions to be deleted. The versioned data will not be deleted, but it will no longer be
            returned in normal get requests.
        :type versions: int
        :param mount_point: The "path" the secret engine was mounted on.
        :type mount_point: str | unicode
        :return: The response of the request.
        :rtype: requests.Response
        """
        if not isinstance(versions, list) or len(versions) == 0:
            error_msg = 'argument to "versions" must be a list containing one or more integers, "{versions}" provided.'.format(
                versions=versions
            )
            raise exceptions.ParamValidationError(error_msg)
        params = {
            'versions': versions,
        }
        api_path = '/v1/{mount_point}/delete/{path}'.format(mount_point=mount_point, path=path)
        return self._adapter.post(
            url=api_path,
            json=params,
        )

    def undelete_secret_versions(self, path, versions, mount_point=DEFAULT_MOUNT_POINT):
        """Undelete the data for the provided version and path in the key-value store.

        This restores the data, allowing it to be returned on get requests.

        Supported methods:
            POST: /{mount_point}/undelete/{path}. Produces: 204 (empty body)


        :param path: Specifies the path of the secret to undelete. This is specified as part of the URL.
        :type path: str | unicode
        :param versions: The versions to undelete. The versions will be restored and their data will be returned on
            normal get requests.
        :type versions: list of int
        :param mount_point: The "path" the secret engine was mounted on.
        :type mount_point: str | unicode
        :return: The response of the request.
        :rtype: requests.Response
        """
        if not isinstance(versions, list) or len(versions) == 0:
            error_msg = 'argument to "versions" must be a list containing one or more integers, "{versions}" provided.'.format(
                versions=versions
            )
            raise exceptions.ParamValidationError(error_msg)
        params = {
            'versions': versions,
        }
        api_path = '/v1/{mount_point}/undelete/{path}'.format(mount_point=mount_point, path=path)
        return self._adapter.post(
            url=api_path,
            json=params,
        )

    def destroy_secret_versions(self, path, versions, mount_point=DEFAULT_MOUNT_POINT):
        """Permanently remove the specified version data and numbers for the provided path from the key-value store.

        Supported methods:
            POST: /{mount_point}/destroy/{path}. Produces: 204 (empty body)


        :param path: Specifies the path of the secret to destroy.
            This is specified as part of the URL.
        :type path: str | unicode
        :param versions: The versions to destroy. Their data will be
            permanently deleted.
        :type versions: list of int
        :param mount_point: The "path" the secret engine was mounted on.
        :type mount_point: str | unicode
        :return: The response of the request.
        :rtype: requests.Response
        """
        if not isinstance(versions, list) or len(versions) == 0:
            error_msg = 'argument to "versions" must be a list containing one or more integers, "{versions}" provided.'.format(
                versions=versions
            )
            raise exceptions.ParamValidationError(error_msg)
        params = {
            'versions': versions,
        }
        api_path = '/v1/{mount_point}/destroy/{path}'.format(mount_point=mount_point, path=path)
        return self._adapter.post(
            url=api_path,
            json=params,
        )

    def list_secrets(self, path, mount_point=DEFAULT_MOUNT_POINT):
        """Return a list of key names at the specified location.

        Folders are suffixed with /. The input must be a folder; list on a file will not return a value. Note that no
        policy-based filtering is performed on keys; do not encode sensitive information in key names. The values
        themselves are not accessible via this command.

        Supported methods:
            LIST: /{mount_point}/metadata/{path}. Produces: 200 application/json


        :param path: Specifies the path of the secrets to list. This is specified as part of the URL.
        :type path: str | unicode
        :param mount_point: The "path" the secret engine was mounted on.
        :type mount_point: str | unicode
        :return: The JSON response of the request.
        :rtype: dict
        """
        api_path = '/v1/{mount_point}/metadata/{path}'.format(mount_point=mount_point, path=path)
        response = self._adapter.list(
            url=api_path,
        )
        return response.json()

    def read_secret_metadata(self, path, mount_point=DEFAULT_MOUNT_POINT):
        """Retrieve the metadata and versions for the secret at the specified path.

        Supported methods:
            GET: /{mount_point}/metadata/{path}. Produces: 200 application/json


        :param path: Specifies the path of the secret to read. This is specified as part of the URL.
        :type path: str | unicode
        :param mount_point: The "path" the secret engine was mounted on.
        :type mount_point: str | unicode
        :return: The JSON response of the request.
        :rtype: dict
        """
        api_path = '/v1/{mount_point}/metadata/{path}'.format(mount_point=mount_point, path=path)
        response = self._adapter.get(
            url=api_path,
        )
        return response.json()

    def update_metadata(self, path, max_versions=None, cas_required=None, mount_point=DEFAULT_MOUNT_POINT):
        """Updates the max_versions of cas_required setting on an existing path.

        Supported methods:
            POST: /{mount_point}/metadata/{path}. Produces: 204 (empty body)


        :param path: Path
        :type path: str | unicode
        :param max_versions: The number of versions to keep per key. If not set, the backend's configured max version is
            used. Once a key has more than the configured allowed versions the oldest version will be permanently
            deleted.
        :type max_versions: int
        :param cas_required: If true the key will require the cas parameter to be set on all write requests. If false,
            the backend's configuration will be used.
        :type cas_required: bool
        :param mount_point: The "path" the secret engine was mounted on.
        :type mount_point: str | unicode
        :return: The response of the request.
        :rtype: requests.Response
        """
        params = {}
        if max_versions is not None:
            params['max_versions'] = max_versions
        if cas_required is not None:
            if not isinstance(cas_required, bool):
                error_msg = 'bool expected for cas_required param, {type} received'.format(type=type(cas_required))
                raise exceptions.ParamValidationError(error_msg)
            params['cas_required'] = cas_required
        api_path = '/v1/{mount_point}/metadata/{path}'.format(mount_point=mount_point, path=path)
        return self._adapter.post(
            url=api_path,
            json=params,
        )

    def delete_metadata_and_all_versions(self, path, mount_point=DEFAULT_MOUNT_POINT):
        """Delete (permanently) the key metadata and all version data for the specified key.

        All version history will be removed.

        Supported methods:
            DELETE: /{mount_point}/metadata/{path}. Produces: 204 (empty body)


        :param path: Specifies the path of the secret to delete. This is specified as part of the URL.
        :type path: str | unicode
        :param mount_point: The "path" the secret engine was mounted on.
        :type mount_point: str | unicode
        :return: The response of the request.
        :rtype: requests.Response
        """
        api_path = '/v1/{mount_point}/metadata/{path}'.format(mount_point=mount_point, path=path)
        return self._adapter.delete(
            url=api_path,
        )
