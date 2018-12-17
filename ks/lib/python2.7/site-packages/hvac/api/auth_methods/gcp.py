#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""GCP methods module."""
import logging

from hvac import exceptions
from hvac.api.vault_api_base import VaultApiBase
from hvac.constants.gcp import ALLOWED_ROLE_TYPES, GCP_CERTS_ENDPOINT
from hvac.utils import validate_list_of_strings_param, list_to_comma_delimited

DEFAULT_MOUNT_POINT = 'gcp'

logger = logging.getLogger(__name__)


class Gcp(VaultApiBase):
    """Google Cloud Auth Method (API).

    Reference: https://www.vaultproject.io/api/auth/{mount_point}/index.html
    """

    def configure(self, credentials="", google_certs_endpoint=GCP_CERTS_ENDPOINT, mount_point=DEFAULT_MOUNT_POINT):
        """Configure the credentials required for the GCP auth method to perform API calls to Google Cloud.

        These credentials will be used to query the status of IAM entities and get service account or other Google
        public certificates to confirm signed JWTs passed in during login.

        Supported methods:
            POST: /auth/{mount_point}/config. Produces: 204 (empty body)


        :param credentials: A JSON string containing the contents of a GCP credentials file. The credentials file must
            have the following permissions: `iam.serviceAccounts.get`, `iam.serviceAccountKeys.get`.
            If this value is empty, Vault will try to use Application Default Credentials from the machine on which the
            Vault server is running. The project must have the iam.googleapis.com API enabled.
        :type credentials: str | unicode
        :param google_certs_endpoint: The Google OAuth2 endpoint from which to obtain public certificates. This is used
            for testing and should generally not be set by end users.
        :type google_certs_endpoint: str | unicode
        :param mount_point: The "path" the method/backend was mounted on.
        :type mount_point: str | unicode
        :return: The response of the request.
        :rtype: requests.Response
        """
        params = {
            'credentials': credentials,
            'google_certs_endpoint': google_certs_endpoint,
        }
        api_path = '/v1/auth/{mount_point}/config'.format(mount_point=mount_point)
        return self._adapter.post(
            url=api_path,
            json=params,
        )

    def read_config(self, mount_point=DEFAULT_MOUNT_POINT):
        """Read the configuration, if any, including credentials.

        Supported methods:
            GET: /auth/{mount_point}/config. Produces: 200 application/json

        :param mount_point: The "path" the method/backend was mounted on.
        :type mount_point: str | unicode
        :return: The data key from the JSON response of the request.
        :rtype: dict
        """
        api_path = '/v1/auth/{mount_point}/config'.format(mount_point=mount_point)
        response = self._adapter.get(
            url=api_path,
        )
        return response.json().get('data')

    def delete_config(self, mount_point=DEFAULT_MOUNT_POINT):
        """Delete all GCP configuration data. This operation is idempotent.

        Supported methods:
            DELETE: /auth/{mount_point}/config. Produces: 204 (empty body)


        :param mount_point: The "path" the method/backend was mounted on.
        :type mount_point: str | unicode
        :return: The response of the request.
        :rtype: requests.Response
        """
        api_path = '/v1/auth/{mount_point}/config'.format(mount_point=mount_point)
        return self._adapter.delete(
            url=api_path,
        )

    def create_role(self, name, role_type, project_id, ttl="", max_ttl="", period="", policies=None,
                    bound_service_accounts=None, max_jwt_exp='15m', allow_gce_inference=True, bound_zones=None,
                    bound_regions=None, bound_instance_groups=None, bound_labels=None, mount_point=DEFAULT_MOUNT_POINT):
        """Register a role in the GCP auth method.

        Role types have specific entities that can perform login operations against this endpoint. Constraints specific
            to the role type must be set on the role. These are applied to the authenticated entities attempting to
            login.

        Supported methods:
            POST: /auth/{mount_point}/role/{name}. Produces: 204 (empty body)


        :param name: The name of the role.
        :type name: str | unicode
        :param role_type: The type of this role. Certain fields correspond to specific roles and will be rejected
            otherwise.
        :type role_type: str | unicode
        :param project_id: The GCP project ID. Only entities belonging to this project can authenticate with this role.
        :type project_id: str | unicode
        :param ttl: The TTL period of tokens issued using this role. This can be specified as an integer number of
            seconds or as a duration value like "5m".
        :type ttl: str | unicode
        :param max_ttl: The maximum allowed lifetime of tokens issued in seconds using this role. This can be specified
            as an integer number of seconds or as a duration value like "5m".
        :type max_ttl: str | unicode
        :param period: If set, indicates that the token generated using this role should never expire. The token should
            be renewed within the duration specified by this value. At each renewal, the token's TTL will be set to the
            value of this parameter. This can be specified as an integer number of seconds or as a duration value like
            "5m".
        :type period: str | unicode
        :param policies: The list of policies to be set on tokens issued using this role.
        :type policies: list
        :param bound_service_accounts: <required for iam> A list of service account emails or IDs that login is
            restricted  to. If set to `*`, all service accounts are allowed (role will still be bound by project). Will be
            inferred from service account used to issue metadata token for GCE instances.
        :type bound_service_accounts: list
        :param max_jwt_exp: <iam only> The number of seconds past the time of authentication that the login param JWT
            must expire within. For example, if a user attempts to login with a token that expires within an hour and
            this is set to 15 minutes, Vault will return an error prompting the user to create a new signed JWT with a
            shorter exp. The GCE metadata tokens currently do not allow the exp claim to be customized.
        :type max_jwt_exp: str | unicode
        :param allow_gce_inference: <iam only> A flag to determine if this role should allow GCE instances to
            authenticate by inferring service accounts from the GCE identity metadata token.
        :type allow_gce_inference: bool
        :param bound_zones: <gce only> The list of zones that a GCE instance must belong to in order to be
            authenticated. If bound_instance_groups is provided, it is assumed to be a zonal group and the group must
            belong to this zone.
        :type bound_zones: list
        :param bound_regions: <gce only> The list of regions that a GCE instance must belong to in order to be
            authenticated. If bound_instance_groups is provided, it is assumed to be a regional group and the group
            must belong to this region. If bound_zones are provided, this attribute is ignored.
        :type bound_regions: list
        :param bound_instance_groups: <gce only> The instance groups that an authorized instance must belong to in
            order to be authenticated. If specified, either bound_zones or bound_regions must be set too.
        :type bound_instance_groups: list
        :param bound_labels: <gce only> A list of GCP labels formatted as "key:value" strings that must be set on
            authorized GCE instances. Because GCP labels are not currently ACL'd, we recommend that this be used in
            conjunction with other restrictions.
        :type bound_labels: list
        :param mount_point: The "path" the method/backend was mounted on.
        :type mount_point: str | unicode
        :return: The data key from the JSON response of the request.
        :rtype: requests.Response
        """
        type_specific_params = {
            'iam': {
                'max_jwt_exp': '15m',
                'allow_gce_inference': True,
            },
            'gce': {
                'bound_zones': None,
                'bound_regions': None,
                'bound_instance_groups': None,
                'bound_labels': None,
            },
        }

        list_of_strings_params = {
            'policies': policies,
            'bound_service_accounts': bound_service_accounts,
            'bound_zones': bound_zones,
            'bound_regions': bound_regions,
            'bound_instance_groups': bound_instance_groups,
            'bound_labels': bound_labels,

        }
        for param_name, param_argument in list_of_strings_params.items():
            validate_list_of_strings_param(
                param_name=param_name,
                param_argument=param_argument,
            )

        if role_type not in ALLOWED_ROLE_TYPES:
            error_msg = 'unsupported role_type argument provided "{arg}", supported types: "{role_types}"'
            raise exceptions.ParamValidationError(error_msg.format(
                arg=type,
                role_types=','.join(ALLOWED_ROLE_TYPES),
            ))

        params = {
            'type': role_type,
            'project_id': project_id,
            'ttl': ttl,
            'max_ttl': max_ttl,
            'period': period,
            'policies': list_to_comma_delimited(policies),
            'bound_service_accounts': list_to_comma_delimited(bound_service_accounts),
        }
        if role_type == 'iam':
            params['max_jwt_exp'] = max_jwt_exp
            params['allow_gce_inference'] = allow_gce_inference
            for param, default_arg in type_specific_params['gce'].items():
                if locals().get(param) != default_arg:
                    warning_msg = 'Argument for parameter "{param}" ignored for role type iam'.format(
                        param=param
                    )
                    logger.warning(warning_msg)
        elif role_type == 'gce':
            params['bound_zones'] = list_to_comma_delimited(bound_zones)
            params['bound_regions'] = list_to_comma_delimited(bound_regions)
            params['bound_instance_groups'] = list_to_comma_delimited(bound_instance_groups)
            params['bound_labels'] = list_to_comma_delimited(bound_labels)
            for param, default_arg in type_specific_params['iam'].items():
                if locals().get(param) != default_arg:
                    warning_msg = 'Argument for parameter "{param}" ignored for role type gce'.format(
                        param=param
                    )
                    logger.warning(warning_msg)

        api_path = '/v1/auth/{mount_point}/role/{name}'.format(
            mount_point=mount_point,
            name=name,
        )
        return self._adapter.post(
            url=api_path,
            json=params,
        )

    def edit_service_accounts_on_iam_role(self, name, add=None, remove=None, mount_point=DEFAULT_MOUNT_POINT):
        """Edit service accounts for an existing IAM role in the GCP auth method.

        This allows you to add or remove service accounts from the list of service accounts on the role.

        Supported methods:
            POST: /auth/{mount_point}/role/{name}/service-accounts. Produces: 204 (empty body)


        :param name: The name of an existing iam type role. This will return an error if role is not an iam type role.
        :type name: str | unicode
        :param add: The list of service accounts to add to the role's service accounts.
        :type add: list
        :param remove: The list of service accounts to remove from the role's service accounts.
        :type remove: list
        :param mount_point: The "path" the method/backend was mounted on.
        :type mount_point: str | unicode
        :return: The response of the request.
        :rtype: requests.Response
        """
        params = {
            'add': add,
            'remove': remove,
        }
        api_path = '/v1/auth/{mount_point}/role/{name}/service-accounts'.format(
            mount_point=mount_point,
            name=name,
        )
        return self._adapter.post(
            url=api_path,
            json=params,
        )

    def edit_labels_on_gce_role(self, name, add=None, remove=None, mount_point=DEFAULT_MOUNT_POINT):
        """Edit labels for an existing GCE role in the backend.

        This allows you to add or remove labels (keys, values, or both) from the list of keys on the role.

        Supported methods:
            POST: /auth/{mount_point}/role/{name}/labels. Produces: 204 (empty body)


        :param name: The name of an existing gce role. This will return an error if role is not a gce type role.
        :type name: str | unicode
        :param add: The list of key:value labels to add to the GCE role's bound labels.
        :type add: list
        :param remove: The list of label keys to remove from the role's bound labels. If any of the specified keys do
            not exist, no error is returned (idempotent).
        :type remove: list
        :param mount_point: The "path" the method/backend was mounted on.
        :type mount_point: str | unicode
        :return: The response of the edit_labels_on_gce_role request.
        :rtype: requests.Response
        """
        params = {
            'add': add,
            'remove': remove,
        }
        api_path = '/v1/auth/{mount_point}/role/{name}/labels'.format(
            mount_point=mount_point,
            name=name,
        )
        return self._adapter.post(
            url=api_path,
            json=params,
        )

    def read_role(self, name, mount_point=DEFAULT_MOUNT_POINT):
        """Read the previously registered role configuration.

        Supported methods:
            GET: /auth/{mount_point}/role/{name}. Produces: 200 application/json


        :param name: The name of the role to read.
        :type name: str | unicode
        :param mount_point: The "path" the method/backend was mounted on.
        :type mount_point: str | unicode
        :return: The data key from the JSON response of the read_role request.
        :rtype: JSON
        """
        params = {
            'name': name,
        }
        api_path = '/v1/auth/{mount_point}/role/{name}'.format(
            mount_point=mount_point,
            name=name,
        )
        response = self._adapter.get(
            url=api_path,
            json=params,
        )
        return response.json().get('data')

    def list_roles(self, mount_point=DEFAULT_MOUNT_POINT):
        """List all the roles that are registered with the plugin.

        Supported methods:
            LIST: /auth/{mount_point}/roles. Produces: 200 application/json


        :param mount_point: The "path" the method/backend was mounted on.
        :type mount_point: str | unicode
        :return: The data key from the JSON response of the request.
        :rtype: dict
        """
        api_path = '/v1/auth/{mount_point}/roles'.format(mount_point=mount_point)
        response = self._adapter.list(
            url=api_path,
        )
        return response.json().get('data')

    def delete_role(self, role, mount_point=DEFAULT_MOUNT_POINT):
        """Delete the previously registered role.

        Supported methods:
            DELETE: /auth/{mount_point}/role/{role}. Produces: 204 (empty body)


        :param role: The name of the role to delete.
        :type role: str | unicode
        :param mount_point: The "path" the method/backend was mounted on.
        :type mount_point: str | unicode
        :return: The response of the request.
        :rtype: requests.Response
        """
        params = {
            'role': role,
        }
        api_path = '/v1/auth/{mount_point}/role/{role}'.format(
            mount_point=mount_point,
            role=role,
        )
        return self._adapter.delete(
            url=api_path,
            json=params,
        )

    def login(self, role, jwt, use_token=True, mount_point=DEFAULT_MOUNT_POINT):
        """Login to retrieve a Vault token via the GCP auth method.

        This endpoint takes a signed JSON Web Token (JWT) and a role name for some entity. It verifies the JWT
            signature with Google Cloud to authenticate that entity and then authorizes the entity for the given role.

        Supported methods:
            POST: /auth/{mount_point}/login. Produces: 200 application/json


        :param role: The name of the role against which the login is being attempted.
        :type role: str | unicode
        :param jwt: A signed JSON web token
        :type jwt: str | unicode
        :param use_token: if True, uses the token in the response received from the auth request to set the "token"
            attribute on the the :py:meth:`hvac.adapters.Adapter` instance under the _adapater Client attribute.
        :type use_token: bool
        :param mount_point: The "path" the method/backend was mounted on.
        :type mount_point: str | unicode
        :return: The JSON response of the request.
        :rtype: dict
        """
        params = {
            'role': role,
            'jwt': jwt,
        }
        api_path = '/v1/auth/{mount_point}/login'.format(mount_point=mount_point)
        response = self._adapter.login(
            url=api_path,
            use_token=use_token,
            json=params,
        )
        return response
