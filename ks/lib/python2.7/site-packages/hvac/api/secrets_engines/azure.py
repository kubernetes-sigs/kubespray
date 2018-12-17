#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Azure secret engine methods module."""
import json

from hvac import exceptions
from hvac.api.vault_api_base import VaultApiBase
from hvac.constants.azure import VALID_ENVIRONMENTS

DEFAULT_MOUNT_POINT = 'azure'


class Azure(VaultApiBase):
    """Azure Secrets Engine (API).

    Reference: https://www.vaultproject.io/api/secret/azure/index.html
    """

    def configure(self, subscription_id, tenant_id, client_id="", client_secret="", environment='AzurePublicCloud',
                  mount_point=DEFAULT_MOUNT_POINT):
        """Configure the credentials required for the plugin to perform API calls to Azure.

        These credentials will be used to query roles and create/delete service principals. Environment variables will
        override any parameters set in the config.

        Supported methods:
            POST: /{mount_point}/config. Produces: 204 (empty body)


        :param subscription_id: The subscription id for the Azure Active Directory
        :type subscription_id: str | unicode
        :param tenant_id: The tenant id for the Azure Active Directory.
        :type tenant_id: str | unicode
        :param client_id: The OAuth2 client id to connect to Azure.
        :type client_id: str | unicode
        :param client_secret: The OAuth2 client secret to connect to Azure.
        :type client_secret: str | unicode
        :param environment: The Azure environment. If not specified, Vault will use Azure Public Cloud.
        :type environment: str | unicode
        :param mount_point: The OAuth2 client secret to connect to Azure.
        :type mount_point: str | unicode
        :return: The response of the request.
        :rtype: requests.Response
        """
        if environment not in VALID_ENVIRONMENTS:
            error_msg = 'invalid environment argument provided "{arg}", supported environments: "{environments}"'
            raise exceptions.ParamValidationError(error_msg.format(
                arg=environment,
                environments=','.join(VALID_ENVIRONMENTS),
            ))
        params = {
            'subscription_id': subscription_id,
            'tenant_id': tenant_id,
            'client_id': client_id,
            'client_secret': client_secret,
            'environment': environment,
        }
        api_path = '/v1/{mount_point}/config'.format(mount_point=mount_point)
        return self._adapter.post(
            url=api_path,
            json=params,
        )

    def read_config(self, mount_point=DEFAULT_MOUNT_POINT):
        """Read the stored configuration, omitting client_secret.

        Supported methods:
            GET: /{mount_point}/config. Produces: 200 application/json


        :param mount_point: The "path" the method/backend was mounted on.
        :type mount_point: str | unicode
        :return: The data key from the JSON response of the request.
        :rtype: dict
        """
        api_path = '/v1/{mount_point}/config'.format(mount_point=mount_point)
        response = self._adapter.get(
            url=api_path,
        )
        return response.json().get('data')

    def delete_config(self, mount_point=DEFAULT_MOUNT_POINT):
        """Delete the stored Azure configuration and credentials.

        Supported methods:
            DELETE: /auth/{mount_point}/config. Produces: 204 (empty body)


        :param mount_point: The "path" the method/backend was mounted on.
        :type mount_point: str | unicode
        :return: The response of the request.
        :rtype: requests.Response
        """
        api_path = '/v1/{mount_point}/config'.format(mount_point=mount_point)
        return self._adapter.delete(
            url=api_path,
        )

    def create_or_update_role(self, name, azure_roles, ttl="", max_ttl="", mount_point=DEFAULT_MOUNT_POINT):
        """Create or update a Vault role.

        The provided Azure roles must exist for this call to succeed. See the Azure secrets roles docs for more
        information about roles.

        Supported methods:
            POST: /{mount_point}/roles/{name}. Produces: 204 (empty body)


        :param name: Name of the role.
        :type name: str | unicode
        :param azure_roles:  List of Azure roles to be assigned to the generated service principal.
        :type azure_roles: list(dict)
        :param ttl: Specifies the default TTL for service principals generated using this role. Accepts time suffixed
            strings ("1h") or an integer number of seconds. Defaults to the system/engine default TTL time.
        :type ttl: str | unicode
        :param max_ttl: Specifies the maximum TTL for service principals generated using this role. Accepts time
            suffixed strings ("1h") or an integer number of seconds. Defaults to the system/engine max TTL time.
        :type max_ttl: str | unicode
        :param mount_point: The "path" the method/backend was mounted on.
        :type mount_point: str | unicode
        :return: The response of the request.
        :rtype: requests.Response
        """
        params = {
            'azure_roles': json.dumps(azure_roles),
            'ttl': ttl,
            'max_ttl': max_ttl,
        }
        api_path = '/v1/{mount_point}/roles/{name}'.format(
            mount_point=mount_point,
            name=name
        )
        return self._adapter.post(
            url=api_path,
            json=params,
        )

    def list_roles(self, mount_point=DEFAULT_MOUNT_POINT):
        """List all of the roles that are registered with the plugin.

        Supported methods:
            LIST: /{mount_point}/roles. Produces: 200 application/json


        :param mount_point: The "path" the method/backend was mounted on.
        :type mount_point: str | unicode
        :return: The data key from the JSON response of the request.
        :rtype: dict
        """
        api_path = '/v1/{mount_point}/roles'.format(mount_point=mount_point)
        response = self._adapter.list(
            url=api_path,
        )
        return response.json().get('data')

    def generate_credentials(self, name, mount_point=DEFAULT_MOUNT_POINT):
        """Generate a new service principal based on the named role.

        Supported methods:
            GET: /{mount_point}/creds/{name}. Produces: 200 application/json


        :param name: Specifies the name of the role to create credentials against.
        :type name: str | unicode
        :param mount_point: The "path" the method/backend was mounted on.
        :type mount_point: str | unicode
        :return: The data key from the JSON response of the request.
        :rtype: dict
        """
        api_path = '/v1/{mount_point}/creds/{name}'.format(
            mount_point=mount_point,
            name=name,
        )
        response = self._adapter.get(
            url=api_path,
        )
        return response.json().get('data')
