#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Support for "Health"-related System Backend Methods."""
from hvac import exceptions
from hvac.api.system_backend.system_backend_mixin import SystemBackendMixin


class Health(SystemBackendMixin):
    """.

    Reference: https://www.vaultproject.io/api/system/index.html
    """

    def read_health_status(self, standby_ok=False, active_code=200, standby_code=429, dr_secondary_code=472,
                           performance_standby_code=473, sealed_code=503, uninit_code=501, method='HEAD'):
        """Read the health status of Vault.

        This matches the semantics of a Consul HTTP health check and provides a simple way to monitor the health of a
        Vault instance.


        :param standby_ok: Specifies if being a standby should still return the active status code instead of the
            standby status code. This is useful when Vault is behind a non-configurable load balance that just wants a
            200-level response.
        :type standby_ok: bool
        :param active_code: The status code that should be returned for an active node.
        :type active_code: int
        :param standby_code: Specifies the status code that should be returned for a standby node.
        :type standby_code: int
        :param dr_secondary_code: Specifies the status code that should be returned for a DR secondary node.
        :type dr_secondary_code: int
        :param performance_standby_code: Specifies the status code that should be returned for a performance standby
            node.
        :type performance_standby_code: int
        :param sealed_code: Specifies the status code that should be returned for a sealed node.
        :type sealed_code: int
        :param uninit_code: Specifies the status code that should be returned for a uninitialized node.
        :type uninit_code: int
        :param method: Supported methods:
            HEAD: /sys/health. Produces: 000 (empty body)
            GET: /sys/health. Produces: 000 application/json
        :type method: str | unicode
        :return: The JSON response of the request.
        :rtype: requests.Response
        """
        params = {
            'standby_ok': standby_ok,
            'active_code': active_code,
            'standby_code': standby_code,
            'dr_secondary_code': dr_secondary_code,
            'performance_standby_code': performance_standby_code,
            'sealed_code': sealed_code,
            'uninit_code': uninit_code,
        }

        if method == 'HEAD':
            api_path = '/v1/sys/health'.format()
            response = self._adapter.head(
                url=api_path,
            )
            return response
        elif method == 'GET':
            api_path = '/v1/sys/health'.format()
            response = self._adapter.get(
                url=api_path,
                json=params,
            )
            return response.json()
        else:
            error_message = '"method" parameter provided invalid value; HEAD or GET allowed, "{method}" provided'.format(method=method)
            raise exceptions.ParamValidationError(error_message)
