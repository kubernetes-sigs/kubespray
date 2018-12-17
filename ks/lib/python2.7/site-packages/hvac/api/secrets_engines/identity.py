#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Identity secret engine module."""
from hvac import exceptions
from hvac.api.vault_api_base import VaultApiBase
from hvac.constants.identity import ALLOWED_GROUP_TYPES

DEFAULT_MOUNT_POINT = 'identity'


class Identity(VaultApiBase):
    """Identity Secrets Engine (API).

    Reference: https://www.vaultproject.io/api/secret/identity/entity.html
    """

    def create_or_update_entity(self, name, entity_id=None, metadata=None, policies=None, disabled=False,
                                mount_point=DEFAULT_MOUNT_POINT):
        """Create or update an Entity.

        Supported methods:
            POST: /{mount_point}/entity. Produces: 200 application/json

        :param entity_id: ID of the entity. If set, updates the corresponding existing entity.
        :type entity_id: str | unicode
        :param name: Name of the entity.
        :type name: str | unicode
        :param metadata: Metadata to be associated with the entity.
        :type metadata: dict
        :param policies: Policies to be tied to the entity.
        :type policies: str | unicode
        :param disabled: Whether the entity is disabled. Disabled entities' associated tokens cannot be used, but are
            not revoked.
        :type disabled: bool
        :param mount_point: The "path" the method/backend was mounted on.
        :type mount_point: str | unicode
        :return: The JSON response for creates, the generic response object for updates, of the request.
        :rtype: dict | requests.Response
        """
        if metadata is None:
            metadata = {}
        if not isinstance(metadata, dict):
            error_msg = 'unsupported metadata argument provided "{arg}" ({arg_type}), required type: dict"'
            raise exceptions.ParamValidationError(error_msg.format(
                arg=metadata,
                arg_type=type(metadata),
            ))
        params = {
            'name': name,
            'metadata': metadata,
            'policies': policies,
            'disabled': disabled,
        }
        if entity_id is not None:
            params['id'] = entity_id
        api_path = '/v1/{mount_point}/entity'.format(mount_point=mount_point)
        response = self._adapter.post(
            url=api_path,
            json=params,
        )
        if response.status_code == 204:
            return response
        else:
            return response.json()

    def create_or_update_entity_by_name(self, name, metadata=None, policies=None, disabled=False,
                                        mount_point=DEFAULT_MOUNT_POINT):
        """Create or update an entity by a given name.

        Supported methods:
            POST: /{mount_point}/entity/name/{name}. Produces: 200 application/json

        :param name: Name of the entity.
        :type name: str | unicode
        :param metadata: Metadata to be associated with the entity.
        :type metadata: dict
        :param policies: Policies to be tied to the entity.
        :type policies: str | unicode
        :param disabled: Whether the entity is disabled. Disabled
            entities' associated tokens cannot be used, but are not revoked.
        :type disabled: bool
        :param mount_point: The "path" the method/backend was mounted on.
        :type mount_point: str | unicode
        :return: The JSON response for creates, the generic response of the request for updates.
        :rtype: requests.Response | dict
        """
        if metadata is None:
            metadata = {}
        if not isinstance(metadata, dict):
            error_msg = 'unsupported metadata argument provided "{arg}" ({arg_type}), required type: dict"'
            raise exceptions.ParamValidationError(error_msg.format(
                arg=metadata,
                arg_type=type(metadata),
            ))
        params = {
            'metadata': metadata,
            'policies': policies,
            'disabled': disabled,
        }
        api_path = '/v1/{mount_point}/entity/name/{name}'.format(
            mount_point=mount_point,
            name=name,
        )
        response = self._adapter.post(
            url=api_path,
            json=params,
        )
        if response.status_code == 204:
            return response
        else:
            return response.json()

    def read_entity(self, entity_id, mount_point=DEFAULT_MOUNT_POINT):
        """Query an entity by its identifier.

        Supported methods:
            GET: /auth/{mount_point}/entity/id/{id}. Produces: 200 application/json

        :param entity_id: Identifier of the entity.
        :type entity_id: str
        :param mount_point: The "path" the secret engine was mounted on.
        :type mount_point: str | unicode
        :return: The JSON response of the request.
        :rtype: dict
        """
        api_path = '/v1/{mount_point}//entity/id/{id}'.format(
            mount_point=mount_point,
            id=entity_id,
        )
        response = self._adapter.get(url=api_path)
        return response.json()

    def read_entity_by_name(self, name, mount_point=DEFAULT_MOUNT_POINT):
        """Query an entity by its name.

        Supported methods:
            GET: /{mount_point}/entity/name/{name}. Produces: 200 application/json

        :param name: Name of the entity.
        :type name: str | unicode
        :param mount_point: The "path" the method/backend was mounted on.
        :type mount_point: str | unicode
        :return: The JSON response of the request.
        :rtype: requests.Response
        """
        api_path = '/v1/{mount_point}/entity/name/{name}'.format(
            mount_point=mount_point,
            name=name,
        )
        response = self._adapter.get(
            url=api_path,
        )
        return response.json()

    def update_entity(self, entity_id, name=None, metadata=None, policies=None, disabled=False,
                      mount_point=DEFAULT_MOUNT_POINT):
        """Update an existing entity.

        Supported methods:
            POST: /{mount_point}/entity/id/{id}. Produces: 200 application/json

        :param entity_id: Identifier of the entity.
        :type entity_id: str | unicode
        :param name: Name of the entity.
        :type name: str | unicode
        :param metadata: Metadata to be associated with the entity.
        :type metadata: dict
        :param policies: Policies to be tied to the entity.
        :type policies: str | unicode
        :param disabled: Whether the entity is disabled. Disabled entities' associated tokens cannot be used, but
            are not revoked.
        :type disabled: bool
        :param mount_point: The "path" the method/backend was mounted on.
        :type mount_point: str | unicode
        :return: The JSON response where available, otherwise the generic response object, of the request.
        :rtype: dict | requests.Response
        """
        if metadata is None:
            metadata = {}
        if not isinstance(metadata, dict):
            error_msg = 'unsupported metadata argument provided "{arg}" ({arg_type}), required type: dict"'
            raise exceptions.ParamValidationError(error_msg.format(
                arg=metadata,
                arg_type=type(metadata),
            ))
        params = {
            'name': name,
            'metadata': metadata,
            'policies': policies,
            'disabled': disabled,
        }
        api_path = '/v1/{mount_point}/entity/id/{id}'.format(
            mount_point=mount_point,
            id=entity_id,
        )
        response = self._adapter.post(
            url=api_path,
            json=params,
        )
        if response.status_code == 204:
            return response
        else:
            return response.json()

    def delete_entity(self, entity_id, mount_point=DEFAULT_MOUNT_POINT):
        """Delete an entity and all its associated aliases.

        Supported methods:
            DELETE: /{mount_point}/entity/id/:id. Produces: 204 (empty body)

        :param entity_id: Identifier of the entity.
        :type entity_id: str
        :param mount_point: The "path" the secret engine was mounted on.
        :type mount_point: str | unicode
        :return: The response of the request.
        :rtype: requests.Response
        """
        api_path = '/v1/{mount_point}/entity/id/{id}'.format(
            mount_point=mount_point,
            id=entity_id,
        )
        return self._adapter.delete(
            url=api_path,
        )

    def delete_entity_by_name(self, name, mount_point=DEFAULT_MOUNT_POINT):
        """Delete an entity and all its associated aliases, given the entity name.

        Supported methods:
            DELETE: /{mount_point}/entity/name/{name}. Produces: 204 (empty body)

        :param name: Name of the entity.
        :type name: str | unicode
        :param mount_point: The "path" the method/backend was mounted on.
        :type mount_point: str | unicode
        :return: The response of the request.
        :rtype: requests.Response
        """
        api_path = '/v1/{mount_point}/entity/name/{name}'.format(
            mount_point=mount_point,
            name=name,
        )
        return self._adapter.delete(
            url=api_path,
        )

    def list_entities(self, method='LIST', mount_point=DEFAULT_MOUNT_POINT):
        """List available entities entities by their identifiers.

        :param method: Supported methods:
            LIST: /{mount_point}/entity/id. Produces: 200 application/json
            GET: /{mount_point}/entity/id?list=true. Produces: 200 application/json
        :type method: str | unicode
        :param mount_point: The "path" the method/backend was mounted on.
        :type mount_point: str | unicode
        :return: The JSON response of the request.
        :rtype: dict
        """
        if method == 'LIST':
            api_path = '/v1/{mount_point}/entity/id'.format(mount_point=mount_point)
            response = self._adapter.list(
                url=api_path,
            )

        elif method == 'GET':
            api_path = '/v1/{mount_point}/entity/id?list=true'.format(mount_point=mount_point)
            response = self._adapter.get(
                url=api_path,
            )
        else:
            error_message = '"method" parameter provided invalid value; LIST or GET allowed, "{method}" provided'.format(method=method)
            raise exceptions.ParamValidationError(error_message)

        return response.json()

    def list_entities_by_name(self, method='LIST', mount_point=DEFAULT_MOUNT_POINT):
        """List available entities by their names.

        :param method: Supported methods:
            LIST: /{mount_point}/entity/name. Produces: 200 application/json
            GET: /{mount_point}/entity/name?list=true. Produces: 200 application/json
        :type method: str | unicode
        :param mount_point: The "path" the method/backend was mounted on.
        :type mount_point: str | unicode
        :return: The JSON response of the request.
        :rtype: dict
        """
        if method == 'LIST':
            api_path = '/v1/{mount_point}/entity/name'.format(mount_point=mount_point)
            response = self._adapter.list(
                url=api_path,
            )

        elif method == 'GET':
            api_path = '/v1/{mount_point}/entity/name'.format(mount_point=mount_point)
            response = self._adapter.list(
                url=api_path,
            )
        else:
            error_message = '"method" parameter provided invalid value; LIST or GET allowed, "{method}" provided'.format(method=method)
            raise exceptions.ParamValidationError(error_message)

        return response.json()

    def merge_entities(self, from_entity_ids, to_entity_id, force=False, mount_point=DEFAULT_MOUNT_POINT):
        """Merge many entities into one entity.

        Supported methods:
            POST: /{mount_point}/entity/merge. Produces: 204 (empty body)

        :param from_entity_ids: Entity IDs which needs to get merged.
        :type from_entity_ids: array
        :param to_entity_id: Entity ID into which all the other entities need to get merged.
        :type to_entity_id: str | unicode
        :param force: Setting this will follow the 'mine' strategy for merging MFA secrets. If there are secrets of the
            same type both in entities that are merged from and in entity into which all others are getting merged,
            secrets in the destination will be unaltered. If not set, this API will throw an error containing all the
            conflicts.
        :type force: bool
        :param mount_point: The "path" the method/backend was mounted on.
        :type mount_point: str | unicode
        :return: The response of the request.
        :rtype: requests.Response
        """
        params = {
            'from_entity_ids': from_entity_ids,
            'to_entity_id': to_entity_id,
            'force': force,
        }
        api_path = '/v1/{mount_point}/entity/merge'.format(mount_point=mount_point)
        return self._adapter.post(
            url=api_path,
            json=params,
        )

    def create_or_update_entity_alias(self, name, canonical_id, mount_accessor, alias_id=None, mount_point=DEFAULT_MOUNT_POINT):
        """Create a new alias for an entity.

        Supported methods:
            POST: /{mount_point}/entity-alias. Produces: 200 application/json

        :param name: Name of the alias. Name should be the identifier of the client in the authentication source. For
            example, if the alias belongs to userpass backend, the name should be a valid username within userpass
            backend. If alias belongs to GitHub, it should be the GitHub username.
        :type name: str | unicode
        :param alias_id: ID of the entity alias. If set, updates the  corresponding entity alias.
        :type alias_id: str | unicode
        :param canonical_id: Entity ID to which this alias belongs to.
        :type canonical_id: str | unicode
        :param mount_accessor: Accessor of the mount to which the alias should belong to.
        :type mount_accessor: str | unicode
        :param mount_point: The "path" the method/backend was mounted on.
        :type mount_point: str | unicode
        :return: The JSON response of the request.
        :rtype: requests.Response
        """
        params = {
            'name': name,
            'canonical_id': canonical_id,
            'mount_accessor': mount_accessor,
        }
        if alias_id is not None:
            params['id'] = alias_id
        api_path = '/v1/{mount_point}/entity-alias'.format(mount_point=mount_point)
        response = self._adapter.post(
            url=api_path,
            json=params,
        )
        return response.json()

    def read_entity_alias(self, alias_id, mount_point=DEFAULT_MOUNT_POINT):
        """Query the entity alias by its identifier.

        Supported methods:
            GET: /{mount_point}/entity-alias/id/{id}. Produces: 200 application/json

        :param alias_id: Identifier of entity alias.
        :type alias_id: str | unicode
        :param mount_point: The "path" the method/backend was mounted on.
        :type mount_point: str | unicode
        :return: The JSON response of the request.
        :rtype: dict
        """
        api_path = '/v1/{mount_point}/entity-alias/id/{id}'.format(
            mount_point=mount_point,
            id=alias_id,
        )
        response = self._adapter.get(
            url=api_path,
        )
        return response.json()

    def update_entity_alias(self, alias_id, name, canonical_id, mount_accessor, mount_point=DEFAULT_MOUNT_POINT):
        """Update an existing entity alias.

        Supported methods:
            POST: /{mount_point}/entity-alias/id/{id}. Produces: 200 application/json

        :param alias_id: Identifier of the entity alias.
        :type alias_id: str | unicode
        :param name: Name of the alias. Name should be the identifier of the client in the authentication source. For
            example, if the alias belongs to userpass backend, the name should be a valid username within userpass
            backend. If alias belongs to GitHub, it should be the GitHub username.
        :type name: str | unicode
        :param canonical_id: Entity ID to which this alias belongs to.
        :type canonical_id: str | unicode
        :param mount_accessor: Accessor of the mount to which the alias should belong to.
        :type mount_accessor: str | unicode
        :param mount_point: The "path" the method/backend was mounted on.
        :type mount_point: str | unicode
        :return: The JSON response where available, otherwise the generic response object, of the request.
        :rtype: dict | requests.Response
        """
        params = {
            'name': name,
            'canonical_id': canonical_id,
            'mount_accessor': mount_accessor,
        }
        api_path = '/v1/{mount_point}/entity-alias/id/{id}'.format(
            mount_point=mount_point,
            id=alias_id,
        )
        response = self._adapter.post(
            url=api_path,
            json=params,
        )
        if response.status_code == 204:
            return response
        else:
            return response.json()

    def list_entity_aliases(self, method='LIST', mount_point=DEFAULT_MOUNT_POINT):
        """List available entity aliases by their identifiers.

        :param method: Supported methods:
            LIST: /{mount_point}/entity-alias/id. Produces: 200 application/json
            GET: /{mount_point}/entity-alias/id?list=true. Produces: 200 application/json
        :type method: str | unicode
        :param mount_point: The "path" the method/backend was mounted on.
        :type mount_point: str | unicode
        :return: The the JSON response of the request.
        :rtype: dict
        """

        if method == 'LIST':
            api_path = '/v1/{mount_point}/entity-alias/id'.format(mount_point=mount_point)
            response = self._adapter.list(
                url=api_path,
            )

        elif method == 'GET':
            api_path = '/v1/{mount_point}/entity-alias/id?list=true'.format(mount_point=mount_point)
            response = self._adapter.get(
                url=api_path,
            )
        else:
            error_message = '"method" parameter provided invalid value; LIST or GET allowed, "{method}" provided'.format(method=method)
            raise exceptions.ParamValidationError(error_message)

        return response.json()

    def delete_entity_alias(self, alias_id, mount_point=DEFAULT_MOUNT_POINT):
        """Delete a entity alias.

        Supported methods:
            DELETE: /{mount_point}/entity-alias/id/{alias_id}. Produces: 204 (empty body)

        :param alias_id: Identifier of the entity.
        :type alias_id: str | unicode
        :param mount_point: The "path" the method/backend was mounted on.
        :type mount_point: str | unicode
        :return: The response of the request.
        :rtype: requests.Response
        """
        api_path = '/v1/{mount_point}/entity-alias/id/{id}'.format(
            mount_point=mount_point,
            id=alias_id,
        )
        return self._adapter.delete(
            url=api_path,
        )

    def create_or_update_group(self, name, group_id=None, group_type='internal', metadata=None, policies=None,
                               member_group_ids=None, member_entity_ids=None, mount_point=DEFAULT_MOUNT_POINT):
        """Create or update a Group.

        Supported methods:
            POST: /{mount_point}/group. Produces: 200 application/json

        :param group_id: ID of the group. If set, updates the corresponding existing group.
        :type group_id: str | unicode
        :param name: Name of the group.
        :type name: str | unicode
        :param group_type: Type of the group, internal or external. Defaults to internal.
        :type group_type: str | unicode
        :param metadata: Metadata to be associated with the group.
        :type metadata: dict
        :param policies: Policies to be tied to the group.
        :type policies: str | unicode
        :param member_group_ids:  Group IDs to be assigned as group members.
        :type member_group_ids: str | unicode
        :param member_entity_ids: Entity IDs to be assigned as  group members.
        :type member_entity_ids: str | unicode
        :param mount_point: The "path" the method/backend was mounted on.
        :type mount_point: str | unicode
        :return: The JSON response where available, otherwise the generic response object, of the request.
        :rtype: dict | requests.Response
        """
        if metadata is None:
            metadata = {}
        if not isinstance(metadata, dict):
            error_msg = 'unsupported metadata argument provided "{arg}" ({arg_type}), required type: dict"'
            raise exceptions.ParamValidationError(error_msg.format(
                arg=metadata,
                arg_type=type(metadata),
            ))
        if group_type not in ALLOWED_GROUP_TYPES:
            error_msg = 'unsupported group_type argument provided "{arg}", allowed values: ({allowed_values})'
            raise exceptions.ParamValidationError(error_msg.format(
                arg=group_type,
                allowed_values=ALLOWED_GROUP_TYPES,
            ))
        params = {
            'name': name,
            'type': group_type,
            'metadata': metadata,
            'policies': policies,
        }
        if group_id is not None:
            params['id'] = group_id
        if group_type == 'external' and member_entity_ids is not None:
            # InvalidRequest: member entities can't be set manually for external groups
            params['member_entity_ids'] = member_entity_ids
        if group_type == 'external' and member_group_ids is not None:
            # InvalidRequest: member groups can't be set for external groups
            params['member_group_ids'] = member_group_ids
        api_path = '/v1/{mount_point}/group'.format(mount_point=mount_point)
        response = self._adapter.post(
            url=api_path,
            json=params,
        )
        if response.status_code == 204:
            return response
        else:
            return response.json()

    def read_group(self, group_id, mount_point=DEFAULT_MOUNT_POINT):
        """Query the group by its identifier.

        Supported methods:
            GET: /{mount_point}/group/id/{id}. Produces: 200 application/json

        :param group_id: Identifier of the group.
        :type group_id: str | unicode
        :param mount_point: The "path" the method/backend was mounted on.
        :type mount_point: str | unicode
        :return: The JSON response of the request.
        :rtype: requests.Response
        """
        api_path = '/v1/{mount_point}/group/id/{id}'.format(
            mount_point=mount_point,
            id=group_id,
        )
        response = self._adapter.get(
            url=api_path,
        )
        return response.json()

    def update_group(self, group_id, name, group_type="internal", metadata=None, policies=None, member_group_ids=None,
                     member_entity_ids=None, mount_point=DEFAULT_MOUNT_POINT):
        """Update an existing group.

        Supported methods:
            POST: /{mount_point}/group/id/{id}. Produces: 200 application/json

        :param group_id: Identifier of the entity.
        :type group_id: str | unicode
        :param name: Name of the group.
        :type name: str | unicode
        :param group_type: Type of the group, internal or external. Defaults to internal.
        :type group_type: str | unicode
        :param metadata: Metadata to be associated with the group.
        :type metadata: dict
        :param policies: Policies to be tied to the group.
        :type policies: str | unicode
        :param member_group_ids:  Group IDs to be assigned as group members.
        :type member_group_ids: str | unicode
        :param member_entity_ids: Entity IDs to be assigned as group members.
        :type member_entity_ids: str | unicode
        :param mount_point: The "path" the method/backend was mounted on.
        :type mount_point: str | unicode
        :return: The JSON response where available, otherwise the generic response object, of the request.
        :rtype: dict | requests.Response
        """
        if metadata is None:
            metadata = {}
        if not isinstance(metadata, dict):
            error_msg = 'unsupported metadata argument provided "{arg}" ({arg_type}), required type: dict"'
            raise exceptions.ParamValidationError(error_msg.format(
                arg=metadata,
                arg_type=type(metadata),
            ))
        if group_type not in ALLOWED_GROUP_TYPES:
            error_msg = 'unsupported group_type argument provided "{arg}", allowed values: ({allowed_values})'
            raise exceptions.ParamValidationError(error_msg.format(
                arg=group_type,
                allowed_values=ALLOWED_GROUP_TYPES,
            ))
        params = {
            'name': name,
            'type': group_type,
            'metadata': metadata,
            'policies': policies,
        }
        if group_type == 'external' and member_entity_ids is not None:
            # InvalidRequest: member entities can't be set manually for external groups
            params['member_entity_ids'] = member_entity_ids
        if group_type == 'external' and member_group_ids is not None:
            # InvalidRequest: member groups can't be set for external groups
            params['member_group_ids'] = member_group_ids
        api_path = '/v1/{mount_point}/group/id/{id}'.format(
            mount_point=mount_point,
            id=group_id,
        )
        response = self._adapter.post(
            url=api_path,
            json=params,
        )
        if response.status_code == 204:
            return response
        else:
            return response.json()

    def delete_group(self, group_id, mount_point=DEFAULT_MOUNT_POINT):
        """Delete a group.

        Supported methods:
            DELETE: /{mount_point}/group/id/{id}. Produces: 204 (empty body)

        :param group_id: Identifier of the entity.
        :type group_id: str | unicode
        :param mount_point: The "path" the method/backend was mounted on.
        :type mount_point: str | unicode
        :return: The response of the request.
        :rtype: requests.Response
        """
        api_path = '/v1/{mount_point}/group/id/{id}'.format(
            mount_point=mount_point,
            id=group_id,
        )
        return self._adapter.delete(
            url=api_path,
        )

    def list_groups(self, method='LIST', mount_point=DEFAULT_MOUNT_POINT):
        """List available groups by their identifiers.

        :param method: Supported methods:
            LIST: /{mount_point}/group/id. Produces: 200 application/json
            GET: /{mount_point}/group/id?list=true. Produces: 200 application/json
        :type method: str | unicode
        :param mount_point: The "path" the method/backend was mounted on.
        :type mount_point: str | unicode
        :return: The JSON response of the request.
        :rtype: dict
        """

        if method == 'LIST':
            api_path = '/v1/{mount_point}/group/id'.format(mount_point=mount_point)
            response = self._adapter.list(
                url=api_path,
            )

        elif method == 'GET':
            api_path = '/v1/{mount_point}/group/id?list=true'.format(mount_point=mount_point)
            response = self._adapter.get(
                url=api_path,
            )
        else:
            error_message = '"method" parameter provided invalid value; LIST or GET allowed, "{method}" provided'.format(method=method)
            raise exceptions.ParamValidationError(error_message)

        return response.json()

    def list_groups_by_name(self, method='LIST', mount_point=DEFAULT_MOUNT_POINT):
        """List available groups by their names.

        :param method: Supported methods:
            LIST: /{mount_point}/group/name. Produces: 200 application/json
            GET: /{mount_point}/group/name?list=true. Produces: 200 application/json
        :type method: str | unicode
        :param mount_point: The "path" the method/backend was mounted on.
        :type mount_point: str | unicode
        :return: The JSON response of the request.
        :rtype: dict
        """

        if method == 'LIST':
            api_path = '/v1/{mount_point}/group/name'.format(mount_point=mount_point)
            response = self._adapter.list(
                url=api_path,
            )

        elif method == 'GET':
            api_path = '/v1/{mount_point}/group/name?list-true'.format(mount_point=mount_point)
            response = self._adapter.list(
                url=api_path,
            )
        else:
            error_message = '"method" parameter provided invalid value; LIST or GET allowed, "{method}" provided'.format(method=method)
            raise exceptions.ParamValidationError(error_message)

        return response.json()

    def create_or_update_group_by_name(self, name, group_type="internal", metadata=None, policies=None, member_group_ids=None,
                                       member_entity_ids=None, mount_point=DEFAULT_MOUNT_POINT):
        """Create or update a group by its name.

        Supported methods:
            POST: /{mount_point}/group/name/{name}. Produces: 200 application/json

        :param name: Name of the group.
        :type name: str | unicode
        :param group_type: Type of the group, internal or external. Defaults to internal.
        :type group_type: str | unicode
        :param metadata: Metadata to be associated with the group.
        :type metadata: dict
        :param policies: Policies to be tied to the group.
        :type policies: str | unicode
        :param member_group_ids: Group IDs to be assigned as group members.
        :type member_group_ids: str | unicode
        :param member_entity_ids: Entity IDs to be assigned as group members.
        :type member_entity_ids: str | unicode
        :param mount_point: The "path" the method/backend was mounted on.
        :type mount_point: str | unicode
        :return: The response of the request.
        :rtype: requests.Response
        """

        if metadata is None:
            metadata = {}
        if not isinstance(metadata, dict):
            error_msg = 'unsupported metadata argument provided "{arg}" ({arg_type}), required type: dict"'
            raise exceptions.ParamValidationError(error_msg.format(
                arg=metadata,
                arg_type=type(metadata),
            ))
        if group_type not in ALLOWED_GROUP_TYPES:
            error_msg = 'unsupported group_type argument provided "{arg}", allowed values: ({allowed_values})'
            raise exceptions.ParamValidationError(error_msg.format(
                arg=group_type,
                allowed_values=ALLOWED_GROUP_TYPES,
            ))
        params = {
            'type': group_type,
            'metadata': metadata,
            'policies': policies,
            'member_group_ids': member_group_ids,
            'member_entity_ids': member_entity_ids,
        }
        api_path = '/v1/{mount_point}/group/name/{name}'.format(
            mount_point=mount_point,
            name=name,
        )
        response = self._adapter.post(
            url=api_path,
            json=params,
        )
        return response

    def read_group_by_name(self, name, mount_point=DEFAULT_MOUNT_POINT):
        """Query a group by its name.

        Supported methods:
            GET: /{mount_point}/group/name/{name}. Produces: 200 application/json

        :param name: Name of the group.
        :type name: str | unicode
        :param mount_point: The "path" the method/backend was mounted on.
        :type mount_point: str | unicode
        :return: The JSON response of the request.
        :rtype: dict
        """
        api_path = '/v1/{mount_point}/group/name/{name}'.format(
            mount_point=mount_point,
            name=name,
        )
        response = self._adapter.get(
            url=api_path,
        )
        return response.json()

    def delete_group_by_name(self, name, mount_point=DEFAULT_MOUNT_POINT):
        """Delete a group, given its name.

        Supported methods:
            DELETE: /{mount_point}/group/name/{name}. Produces: 204 (empty body)

        :param name: Name of the group.
        :type name: str | unicode
        :param mount_point: The "path" the method/backend was mounted on.
        :type mount_point: str | unicode
        :return: The response of the request.
        :rtype: requests.Response
        """
        api_path = '/v1/{mount_point}/group/name/{name}'.format(
            mount_point=mount_point,
            name=name,
        )
        return self._adapter.delete(
            url=api_path,
        )

    def create_or_update_group_alias(self, name, alias_id=None, mount_accessor=None, canonical_id=None, mount_point=DEFAULT_MOUNT_POINT):
        """Creates or update a group alias.

        Supported methods:
            POST: /{mount_point}/group-alias. Produces: 200 application/json

        :param alias_id: ID of the group alias. If set, updates the corresponding existing group alias.
        :type alias_id: str | unicode
        :param name: Name of the group alias.
        :type name: str | unicode
        :param mount_accessor: Mount accessor to which this alias belongs to
        :type mount_accessor: str | unicode
        :param canonical_id: ID of the group to which this is an alias.
        :type canonical_id: str | unicode
        :param mount_point: The "path" the method/backend was mounted on.
        :type mount_point: str | unicode
        :return: The JSON response of the request.
        :rtype: requests.Response
        """
        params = {
            'name': name,
            'mount_accessor': mount_accessor,
            'canonical_id': canonical_id,
        }
        if alias_id is not None:
            params['id'] = alias_id
        api_path = '/v1/{mount_point}/group-alias'.format(mount_point=mount_point)
        response = self._adapter.post(
            url=api_path,
            json=params,
        )
        return response.json()

    def update_group_alias(self, entity_id, name, mount_accessor="", canonical_id="", mount_point=DEFAULT_MOUNT_POINT):
        """Update an existing group alias.

        Supported methods:
            POST: /{mount_point}/group-alias/id/{id}. Produces: 200 application/json

        :param entity_id: ID of the group alias.
        :type entity_id: str | unicode
        :param name: Name of the group alias.
        :type name: str | unicode
        :param mount_accessor: Mount accessor to which this alias belongs
            toMount accessor to which this alias belongs to.
        :type mount_accessor: str | unicode
        :param canonical_id: ID of the group to which this is an alias.
        :type canonical_id: str | unicode
        :param mount_point: The "path" the method/backend was mounted on.
        :type mount_point: str | unicode
        :return: The response of the request.
        :rtype: requests.Response
        """
        params = {
            'name': name,
            'mount_accessor': mount_accessor,
            'canonical_id': canonical_id,
        }
        api_path = '/v1/{mount_point}/group-alias/id/{id}'.format(
            mount_point=mount_point,
            id=entity_id,
        )
        return self._adapter.post(
            url=api_path,
            json=params,
        )

    def read_group_alias(self, alias_id, mount_point=DEFAULT_MOUNT_POINT):
        """Query the group alias by its identifier.

        Supported methods:
            GET: /{mount_point}/group-alias/id/:id. Produces: 200 application/json

        :param alias_id: ID of the group alias.
        :type alias_id: str | unicode
        :param mount_point: The "path" the method/backend was mounted on.
        :type mount_point: str | unicode
        :return: The JSON response of the request.
        :rtype: dict
        """
        api_path = '/v1/{mount_point}/group-alias/id/{id}'.format(
            mount_point=mount_point,
            id=alias_id,
        )
        response = self._adapter.get(
            url=api_path,
        )
        return response.json()

    def delete_group_alias(self, entity_id, mount_point=DEFAULT_MOUNT_POINT):
        """Delete a group alias.

        Supported methods:
            DELETE: /{mount_point}/group-alias/id/{id}. Produces: 204 (empty body)

        :param entity_id: ID of the group alias.
        :type entity_id: str | unicode
        :param mount_point: The "path" the method/backend was mounted on.
        :type mount_point: str | unicode
        :return: The response of the request.
        :rtype: requests.Response
        """
        api_path = '/v1/{mount_point}/group-alias/id/{id}'.format(
            mount_point=mount_point,
            id=entity_id,
        )
        return self._adapter.delete(
            url=api_path,
        )

    def list_group_aliases(self, method='LIST', mount_point=DEFAULT_MOUNT_POINT):
        """List available group aliases by their identifiers.

        :param method: Supported methods:
            LIST: /{mount_point}/group-alias/id. Produces: 200 application/json
            GET: /{mount_point}/group-alias/id?list=true. Produces: 200 application/json
        :type method: str | unicode
        :param mount_point: The "path" the method/backend was mounted on.
        :type mount_point: str | unicode
        :return: The "data" key from the JSON response of the request.
        :rtype: dict
        """

        if method == 'LIST':
            api_path = '/v1/{mount_point}/group-alias/id'.format(mount_point=mount_point)
            response = self._adapter.list(
                url=api_path,
            )
        elif method == 'GET':
            api_path = '/v1/{mount_point}/group-alias/id'.format(mount_point=mount_point)
            response = self._adapter.list(
                url=api_path,
            )
        else:
            error_message = '"method" parameter provided invalid value; LIST or GET allowed, "{method}" provided'.format(method=method)
            raise exceptions.ParamValidationError(error_message)

        return response.json()

    def lookup_entity(self, name=None, entity_id=None, alias_id=None, alias_name=None, alias_mount_accessor=None, mount_point=DEFAULT_MOUNT_POINT):
        """Query an entity based on the given criteria.

        The criteria can be name, id, alias_id, or a combination of alias_name and alias_mount_accessor.

        Supported methods:
            POST: /{mount_point}/lookup/entity. Produces: 200 application/json

        :param name: Name of the entity.
        :type name: str | unicode
        :param entity_id: ID of the entity.
        :type entity_id: str | unicode
        :param alias_id: ID of the alias.
        :type alias_id: str | unicode
        :param alias_name: Name of the alias. This should be supplied in conjunction with alias_mount_accessor.
        :type alias_name: str | unicode
        :param alias_mount_accessor: Accessor of the mount to which the alias belongs to. This should be supplied in conjunction with alias_name.
        :type alias_mount_accessor: str | unicode
        :param mount_point: The "path" the method/backend was mounted on.
        :type mount_point: str | unicode
        :return: The JSON response of the request.
        :rtype: dict
        """
        params = {}
        if name is not None:
            params['name'] = name
        elif entity_id is not None:
            params['id'] = entity_id
        elif alias_id is not None:
            params['alias_id'] = alias_id
        elif alias_name is not None and alias_mount_accessor is not None:
            params['alias_name'] = alias_name
            params['alias_mount_accessor'] = alias_mount_accessor
        api_path = '/v1/{mount_point}/lookup/entity'.format(mount_point=mount_point)
        response = self._adapter.post(
            url=api_path,
            json=params,
        )
        return response.json()

    def lookup_group(self, name=None, group_id=None, alias_id=None, alias_name=None, alias_mount_accessor=None, mount_point=DEFAULT_MOUNT_POINT):
        """Query a group based on the given criteria.

        The criteria can be name, id, alias_id, or a combination of alias_name and alias_mount_accessor.

        Supported methods:
            POST: /{mount_point}/lookup/group. Produces: 200 application/json

        :param name: Name of the group.
        :type name: str | unicode
        :param group_id: ID of the group.
        :type group_id: str | unicode
        :param alias_id: ID of the alias.
        :type alias_id: str | unicode
        :param alias_name: Name of the alias. This should be supplied in conjunction with alias_mount_accessor.
        :type alias_name: str | unicode
        :param alias_mount_accessor: Accessor of the mount to which the alias belongs to. This should be supplied in conjunction with alias_name.
        :type alias_mount_accessor: str | unicode
        :param mount_point: The "path" the method/backend was mounted on.
        :type mount_point: str | unicode
        :return: The JSON response of the request.
        :rtype: dict
        """
        params = {}
        if name is not None:
            params['name'] = name
        elif group_id is not None:
            params['id'] = group_id
        elif alias_id is not None:
            params['alias_id'] = alias_id
        elif alias_name is not None and alias_mount_accessor is not None:
            params['alias_name'] = alias_name
            params['alias_mount_accessor'] = alias_mount_accessor
        api_path = '/v1/{mount_point}/lookup/group'.format(mount_point=mount_point)
        response = self._adapter.post(
            url=api_path,
            json=params,
        )
        return response.json()
