#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""LDAP methods module."""
from hvac import exceptions
from hvac.api.vault_api_base import VaultApiBase
from hvac.constants.ldap import DEFAULT_GROUP_FILTER

DEFAULT_MOUNT_POINT = 'ldap'


class Ldap(VaultApiBase):
    """LDAP Auth Method (API).

    Reference: https://www.vaultproject.io/api/auth/ldap/index.html
    """

    def configure(self, user_dn, group_dn, url='ldap://127.0.0.1', case_sensitive_names=False, starttls=False,
                  tls_min_version='tls12', tls_max_version='tls12', insecure_tls=False, certificate=None, bind_dn=None,
                  bind_pass=None, user_attr='cn', discover_dn=False, deny_null_bind=True, upn_domain=None,
                  group_filter=DEFAULT_GROUP_FILTER, group_attr='cn', mount_point=DEFAULT_MOUNT_POINT):
        """
        Configure the LDAP auth method.

        Supported methods:
            POST: /auth/{mount_point}/config. Produces: 204 (empty body)

        :param user_dn: Base DN under which to perform user search. Example: ou=Users,dc=example,dc=com
        :type user_dn: str | unicode
        :param group_dn: LDAP search base to use for group membership search. This can be the root containing either
            groups or users. Example: ou=Groups,dc=example,dc=com
        :type group_dn: str | unicode
        :param url: The LDAP server to connect to. Examples: ldap://ldap.myorg.com, ldaps://ldap.myorg.com:636.
            Multiple URLs can be specified with commas, e.g. ldap://ldap.myorg.com,ldap://ldap2.myorg.com; these will be
            tried in-order.
        :type url: str | unicode
        :param case_sensitive_names: If set, user and group names assigned to policies within the backend will be case
            sensitive. Otherwise, names will be normalized to lower case. Case will still be preserved when sending the
            username to the LDAP server at login time; this is only for matching local user/group definitions.
        :type case_sensitive_names: bool
        :param starttls: If true, issues a StartTLS command after establishing an unencrypted connection.
        :type starttls: bool
        :param tls_min_version: Minimum TLS version to use. Accepted values are tls10, tls11 or tls12.
        :type tls_min_version: str | unicode
        :param tls_max_version: Maximum TLS version to use. Accepted values are tls10, tls11 or tls12.
        :type tls_max_version: str | unicode
        :param insecure_tls: If true, skips LDAP server SSL certificate verification - insecure, use with caution!
        :type insecure_tls: bool
        :param certificate: CA certificate to use when verifying LDAP server certificate, must be x509 PEM encoded.
        :type certificate: str | unicode
        :param bind_dn: Distinguished name of object to bind when performing user search. Example:
            cn=vault,ou=Users,dc=example,dc=com
        :type bind_dn: str | unicode
        :param bind_pass:  Password to use along with binddn when performing user search.
        :type bind_pass: str | unicode
        :param user_attr: Attribute on user attribute object matching the username passed when authenticating. Examples:
            sAMAccountName, cn, uid
        :type user_attr: str | unicode
        :param discover_dn: Use anonymous bind to discover the bind DN of a user.
        :type discover_dn: bool
        :param deny_null_bind: This option prevents users from bypassing authentication when providing an empty password.
        :type deny_null_bind: bool
        :param upn_domain: The userPrincipalDomain used to construct the UPN string for the authenticating user. The
            constructed UPN will appear as [username]@UPNDomain. Example: example.com, which will cause vault to bind as
            username@example.com.
        :type upn_domain: str | unicode
        :param group_filter: Go template used when constructing the group membership query. The template can access the
            following context variables: [UserDN, Username]. The default is
            `(|(memberUid={{.Username}})(member={{.UserDN}})(uniqueMember={{.UserDN}}))`, which is compatible with several
            common directory schemas. To support nested group resolution for Active Directory, instead use the following
            query: (&(objectClass=group)(member:1.2.840.113556.1.4.1941:={{.UserDN}})).
        :type group_filter: str | unicode
        :param group_attr: LDAP attribute to follow on objects returned by groupfilter in order to enumerate user group
            membership. Examples: for groupfilter queries returning group objects, use: cn. For queries returning user
            objects, use: memberOf. The default is cn.
        :type group_attr: str | unicode
        :param mount_point: The "path" the method/backend was mounted on.
        :type mount_point: str | unicode
        :return: The response of the configure request.
        :rtype: requests.Response
        """
        params = {
            'userdn': user_dn,
            'groupdn': group_dn,
            'url': url,
            'case_sensitive_names': case_sensitive_names,
            'starttls': starttls,
            'tls_min_version': tls_min_version,
            'tls_max_version': tls_max_version,
            'insecure_tls': insecure_tls,
            'certificate': certificate,
            'userattr': user_attr,
            'discoverdn': discover_dn,
            'deny_null_bind': deny_null_bind,
            'groupfilter': group_filter,
            'groupattr': group_attr,
        }
        # Fill out params dictionary with any optional parameters provided
        if upn_domain is not None:
            params['upndomain'] = upn_domain
        if bind_dn is not None:
            params['binddn'] = bind_dn
        if bind_pass is not None:
            params['bindpass'] = bind_pass
        if certificate is not None:
            params['certificate'] = certificate

        api_path = '/v1/auth/{mount_point}/config'.format(mount_point=mount_point)
        return self._adapter.post(
            url=api_path,
            json=params,
        )

    def read_configuration(self, mount_point=DEFAULT_MOUNT_POINT):
        """
        Retrieve the LDAP configuration for the auth method.

        Supported methods:
            GET: /auth/{mount_point}/config. Produces: 200 application/json

        :param mount_point: The "path" the method/backend was mounted on.
        :type mount_point: str | unicode
        :return: The JSON response of the read_configuration request.
        :rtype: dict
        """
        api_path = '/v1/auth/{mount_point}/config'.format(mount_point=mount_point)
        response = self._adapter.get(
            url=api_path,
        )
        return response.json()

    def create_or_update_group(self, name, policies=None, mount_point=DEFAULT_MOUNT_POINT):
        """
        Create or update LDAP group policies.

        Supported methods:
            POST: /auth/{mount_point}/groups/{name}. Produces: 204 (empty body)


        :param name: The name of the LDAP group
        :type name: str | unicode
        :param policies: List of policies associated with the group. This parameter is transformed to a comma-delimited
            string before being passed to Vault.
        :type policies: list
        :param mount_point: The "path" the method/backend was mounted on.
        :type mount_point: str | unicode
        :return: The response of the create_or_update_group request.
        :rtype: requests.Response
        """
        if policies is None:
            policies = []
        if not isinstance(policies, list):
            error_msg = '"policies" argument must be an instance of list or None, "{policies_type}" provided.'.format(
                policies_type=type(policies),
            )
            raise exceptions.ParamValidationError(error_msg)

        params = {
            'policies': ','.join(policies),
        }
        api_path = '/v1/auth/{mount_point}/groups/{name}'.format(
            mount_point=mount_point,
            name=name,
        )
        return self._adapter.post(
            url=api_path,
            json=params,
        )

    def list_groups(self, mount_point=DEFAULT_MOUNT_POINT):
        """
        List existing LDAP existing groups that have been created in this auth method.

        Supported methods:
            LIST: /auth/{mount_point}/groups. Produces: 200 application/json


        :param mount_point: The "path" the method/backend was mounted on.
        :type mount_point: str | unicode
        :return: The JSON response of the list_groups request.
        :rtype: dict
        """
        api_path = '/v1/auth/{mount_point}/groups'.format(mount_point=mount_point)
        response = self._adapter.list(
            url=api_path,
        )
        return response.json()

    def read_group(self, name, mount_point=DEFAULT_MOUNT_POINT):
        """
        Read policies associated with a LDAP group.

        Supported methods:
            GET: /auth/{mount_point}/groups/{name}. Produces: 200 application/json


        :param name: The name of the LDAP group
        :type name: str | unicode
        :param mount_point: The "path" the method/backend was mounted on.
        :type mount_point: str | unicode
        :return: The JSON response of the read_group request.
        :rtype: dict
        """
        params = {
            'name': name,
        }
        api_path = '/v1/auth/{mount_point}/groups/{name}'.format(
            mount_point=mount_point,
            name=name,
        )
        response = self._adapter.get(
            url=api_path,
            json=params,
        )
        return response.json()

    def delete_group(self, name, mount_point=DEFAULT_MOUNT_POINT):
        """
        Delete a LDAP group and policy association.

        Supported methods:
            DELETE: /auth/{mount_point}/groups/{name}. Produces: 204 (empty body)


        :param name: The name of the LDAP group
        :type name: str | unicode
        :param mount_point: The "path" the method/backend was mounted on.
        :type mount_point: str | unicode
        :return: The response of the delete_group request.
        :rtype: requests.Response
        """
        api_path = '/v1/auth/{mount_point}/groups/{name}'.format(
            mount_point=mount_point,
            name=name,
        )
        return self._adapter.delete(
            url=api_path,
        )

    def create_or_update_user(self, username, policies=None, groups=None, mount_point=DEFAULT_MOUNT_POINT):
        """
        Create or update LDAP users policies and group associations.

        Supported methods:
            POST: /auth/{mount_point}/users/{username}. Produces: 204 (empty body)


        :param username: The username of the LDAP user
        :type username: str | unicode
        :param policies: List of policies associated with the user. This parameter is transformed to a comma-delimited
            string before being passed to Vault.
        :type policies: str | unicode
        :param groups: List of groups associated with the user. This parameter is transformed to a comma-delimited
            string before being passed to Vault.
        :type groups: str | unicode
        :param mount_point: The "path" the method/backend was mounted on.
        :type mount_point: str | unicode
        :return: The response of the create_or_update_user request.
        :rtype: requests.Response
        """
        if policies is None:
            policies = []
        if groups is None:
            groups = []
        list_required_params = {
            'policies': policies,
            'groups': groups,
        }
        for param_name, param_arg in list_required_params.items():
            if not isinstance(param_arg, list):
                error_msg = '"{param_name}" argument must be an instance of list or None, "{param_type}" provided.'.format(
                    param_name=param_name,
                    param_type=type(param_arg),
                )
                raise exceptions.ParamValidationError(error_msg)

        params = {
            'policies': ','.join(policies),
            'groups': ','.join(groups),
        }
        api_path = '/v1/auth/{mount_point}/users/{username}'.format(
            mount_point=mount_point,
            username=username,
        )
        return self._adapter.post(
            url=api_path,
            json=params,
        )

    def list_users(self, mount_point=DEFAULT_MOUNT_POINT):
        """
        List existing users in the method.

        Supported methods:
            LIST: /auth/{mount_point}/users. Produces: 200 application/json


        :param mount_point: The "path" the method/backend was mounted on.
        :type mount_point: str | unicode
        :return: The JSON response of the list_users request.
        :rtype: dict
        """
        api_path = '/v1/auth/{mount_point}/users'.format(mount_point=mount_point)
        response = self._adapter.list(
            url=api_path,
        )
        return response.json()

    def read_user(self, username, mount_point=DEFAULT_MOUNT_POINT):
        """
        Read policies associated with a LDAP user.

        Supported methods:
            GET: /auth/{mount_point}/users/{username}. Produces: 200 application/json


        :param username: The username of the LDAP user
        :type username: str | unicode
        :param mount_point: The "path" the method/backend was mounted on.
        :type mount_point: str | unicode
        :return: The JSON response of the read_user request.
        :rtype: dict
        """
        api_path = '/v1/auth/{mount_point}/users/{username}'.format(
            mount_point=mount_point,
            username=username,
        )
        response = self._adapter.get(
            url=api_path,
        )
        return response.json()

    def delete_user(self, username, mount_point=DEFAULT_MOUNT_POINT):
        """
        Delete a LDAP user and policy association.

        Supported methods:
            DELETE: /auth/{mount_point}/users/{username}. Produces: 204 (empty body)


        :param username: The username of the LDAP user
        :type username: str | unicode
        :param mount_point: The "path" the method/backend was mounted on.
        :type mount_point: str | unicode
        :return: The response of the delete_user request.
        :rtype: requests.Response
        """
        api_path = '/v1/auth/{mount_point}/users/{username}'.format(
            mount_point=mount_point,
            username=username,
        )
        return self._adapter.delete(
            url=api_path,
        )

    def login(self, username, password, use_token=True, mount_point=DEFAULT_MOUNT_POINT):
        """
        Log in with LDAP credentials.

        Supported methods:
            POST: /auth/{mount_point}/login/{username}. Produces: 200 application/json


        :param username: The username of the LDAP user
        :type username: str | unicode
        :param password: The password for the LDAP user
        :type password: str | unicode
        :param use_token: if True, uses the token in the response received from the auth request to set the "token"
            attribute on the the :py:meth:`hvac.adapters.Adapter` instance under the _adapater Client attribute.
        :type use_token: bool
        :param mount_point: The "path" the method/backend was mounted on.
        :type mount_point: str | unicode
        :return: The response of the login_with_user request.
        :rtype: requests.Response
        """
        params = {
            'password': password,
        }
        api_path = '/v1/auth/{mount_point}/login/{username}'.format(
            mount_point=mount_point,
            username=username,
        )
        return self._adapter.login(
            url=api_path,
            use_token=use_token,
            json=params,
        )
