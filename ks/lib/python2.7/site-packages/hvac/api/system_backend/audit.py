#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Support for "Audit"-related System Backend Methods."""
from hvac.api.system_backend.system_backend_mixin import SystemBackendMixin


class Audit(SystemBackendMixin):

    def list_enabled_audit_devices(self):
        """List enabled audit devices.

        It does not list all available audit devices.
        This endpoint requires sudo capability in addition to any path-specific capabilities.

        Supported methods:
            GET: /sys/audit. Produces: 200 application/json

        :return: JSON response of the request.
        :rtype: dict
        """
        list_audit_devices_response = self._adapter.get('/v1/sys/audit').json()
        return list_audit_devices_response

    def enable_audit_device(self, device_type, description=None, options=None, path=None):
        """Enable a new audit device at the supplied path.

        The path can be a single word name or a more complex, nested path.

        Supported methods:
            PUT: /sys/audit/{path}. Produces: 204 (empty body)

        :param device_type: Specifies the type of the audit device.
        :type device_type: str | unicode
        :param description: Human-friendly description of the audit device.
        :type description: str | unicode
        :param options: Configuration options to pass to the audit device itself. This is
            dependent on the audit device type.
        :type options: str | unicode
        :param path: Specifies the path in which to enable the audit device. This is part of
            the request URL.
        :type path: str | unicode
        :return: The response of the request.
        :rtype: requests.Response
        """

        if path is None:
            path = device_type

        params = {
            'type': device_type,
            'description': description,
            'options': options,
        }

        api_path = '/v1/sys/audit/{path}'.format(path=path)
        return self._adapter.post(
            url=api_path,
            json=params
        )

    def disable_audit_device(self, path):
        """Disable the audit device at the given path.

        Supported methods:
            DELETE: /sys/audit/{path}. Produces: 204 (empty body)

        :param path: The path of the audit device to delete. This is part of the request URL.
        :type path: str | unicode
        :return: The response of the request.
        :rtype: requests.Response
        """
        api_path = '/v1/sys/audit/{path}'.format(path=path)
        return self._adapter.delete(
            url=api_path,
        )

    def calculate_hash(self, path, input_to_hash):
        """Hash the given input data with the specified audit device's hash function and salt.

        This endpoint can be used to discover whether a given plaintext string (the input parameter) appears in the
        audit log in obfuscated form.

        Supported methods:
            POST: /sys/audit-hash/{path}. Produces: 204 (empty body)

        :param path: The path of the audit device to generate hashes for. This is part of the request URL.
        :type path: str | unicode
        :param input_to_hash: The input string to hash.
        :type input_to_hash: str | unicode
        :return: The JSON response of the request.
        :rtype: requests.Response
        """
        params = {
            'input': input_to_hash,
        }

        api_path = '/v1/sys/audit-hash/{path}'.format(path=path)
        response = self._adapter.post(
            url=api_path,
            json=params
        )
        return response.json()
