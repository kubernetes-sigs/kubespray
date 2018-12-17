import logging
from unittest import TestCase
from unittest import skipIf

from parameterized import parameterized, param

from hvac import exceptions
from hvac.tests import utils


@skipIf(utils.skip_if_vault_version_lt('0.9.0'), "Identity secrets engine open sourced in Vault version >=0.9.0")
class TestIdentity(utils.HvacIntegrationTestCase, TestCase):
    TEST_APPROLE_PATH = 'identity-test-approle'
    TEST_MOUNT_POINT = 'identity'
    TEST_ENTITY_NAME = 'test-entity'
    TEST_ALIAS_NAME = 'test-alias'
    TEST_GROUP_NAME = 'test-group'
    TEST_GROUP_ALIAS_NAME = 'test-group-alias'

    test_approle_accessor = None

    def setUp(self):
        super(TestIdentity, self).setUp()
        self.client.sys.enable_auth_method(
            method_type='approle',
            path=self.TEST_APPROLE_PATH,
        )
        list_auth_response = self.client.sys.list_auth_methods()
        self.test_approle_accessor = list_auth_response['data']['%s/' % self.TEST_APPROLE_PATH]['accessor']

    def tearDown(self):
        self.tear_down_entities()
        self.tear_down_entity_aliases()
        self.tear_down_groups()
        self.client.sys.disable_auth_method(
            path=self.TEST_APPROLE_PATH,
        )
        super(TestIdentity, self).tearDown()

    def tear_down_entities(self):
        try:
            list_entities_response = self.client.secrets.identity.list_entities(mount_point=self.TEST_MOUNT_POINT)
            logging.debug('list_entities_response in tearDown: %s' % list_entities_response)
            entity_ids = list_entities_response['data']['keys']
        except exceptions.InvalidPath:
            logging.debug('InvalidPath raised when calling list_entites_by_id in tearDown...')
            entity_ids = []
        for entity_id in entity_ids:
            logging.debug('Deleting entity ID: %s' % entity_id)
            self.client.secrets.identity.delete_entity(
                entity_id=entity_id,
                mount_point=self.TEST_MOUNT_POINT,
            )

    def tear_down_entity_aliases(self):
        try:
            list_entity_aliases_response = self.client.secrets.identity.list_entity_aliases(mount_point=self.TEST_MOUNT_POINT)
            logging.debug('list_entity_aliases_response in tearDown: %s' % list_entity_aliases_response)
            alias_ids = list_entity_aliases_response['keys']
        except exceptions.InvalidPath:
            logging.debug('InvalidPath raised when calling list_entites_by_id in tearDown...')
            alias_ids = []
        for alias_id in alias_ids:
            logging.debug('Deleting alias ID: %s' % alias_id)
            self.client.secrets.identity.delete_entity_alias(
                alias_id=alias_id,
                mount_point=self.TEST_MOUNT_POINT,
            )

    def tear_down_groups(self):
        try:
            list_group_response = self.client.secrets.identity.list_groups(mount_point=self.TEST_MOUNT_POINT)
            logging.debug('list_group_response in tearDown: %s' % list_group_response)
            group_ids = list_group_response['data']['keys']
        except exceptions.InvalidPath:
            logging.debug('InvalidPath raised when calling list_groups in tearDown...')
            group_ids = []
        for group_id in group_ids:
            logging.debug('Deleting group ID: %s' % group_id)
            self.client.secrets.identity.delete_group(
                group_id=group_id,
                mount_point=self.TEST_MOUNT_POINT,
            )

    @parameterized.expand([
        param(
            'create success',
        ),
        param(
            'create success with metadata',
            metadata=dict(something='meta')
        ),
        param(
            'create failure with metadata',
            metadata='not a dict',
            raises=exceptions.ParamValidationError,
            exception_message='unsupported metadata argument provided',
        ),
        param(
            'update success',
            create_first=True,
        ),
    ])
    def test_create_or_update_entity(self, label, metadata=None, create_first=False, raises=None, exception_message=''):
        entity_id = None
        if create_first:
            create_first_response = self.client.secrets.identity.create_or_update_entity(
                    name=self.TEST_ENTITY_NAME,
                    entity_id=entity_id,
                    metadata=metadata,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            logging.debug('create_first_response: %s' % create_first_response)
            entity_id = create_first_response['data']['id']
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.secrets.identity.create_or_update_entity(
                    name=self.TEST_ENTITY_NAME,
                    metadata=metadata,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            create_or_update_response = self.client.secrets.identity.create_or_update_entity(
                    name=self.TEST_ENTITY_NAME,
                    entity_id=entity_id,
                    metadata=metadata,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            logging.debug('create_or_update_response: %s' % create_or_update_response)
            if isinstance(create_or_update_response, dict):
                self.assertIn(
                    member='id',
                    container=create_or_update_response['data'],
                )
                if entity_id is not None:
                    self.assertEqual(
                        first=entity_id,
                        second=create_or_update_response['data']['id'],
                    )
            else:
                self.assertEqual(
                    first=create_or_update_response.status_code,
                    second=204,
                )

    @parameterized.expand([
        param(
            'create success',
        ),
        param(
            'create success with metadata',
            metadata=dict(something='meta')
        ),
        param(
            'create failure with metadata',
            metadata='not a dict',
            raises=exceptions.ParamValidationError,
            exception_message='unsupported metadata argument provided',
        ),
        param(
            'update success',
            create_first=True,
        ),
    ])
    @skipIf(utils.skip_if_vault_version_lt('0.11.2'), '"by name" operations added in Vault v0.11.2')
    def test_create_or_update_entity_by_name(self, label, metadata=None, create_first=False, raises=None, exception_message=''):
        entity_id = None
        if create_first:
            create_first_response = self.client.secrets.identity.create_or_update_entity(
                    name=self.TEST_ENTITY_NAME,
                    entity_id=entity_id,
                    metadata=metadata,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            logging.debug('create_first_response: %s' % create_first_response)
            entity_id = create_first_response['data']['id']
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.secrets.identity.create_or_update_entity_by_name(
                    name=self.TEST_ENTITY_NAME,
                    metadata=metadata,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            create_or_update_response = self.client.secrets.identity.create_or_update_entity_by_name(
                    name=self.TEST_ENTITY_NAME,
                    metadata=metadata,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            logging.debug('create_or_update_response: %s' % create_or_update_response)
            if not create_first:
                self.assertIn(
                    member='id',
                    container=create_or_update_response['data'],
                )
                if entity_id is not None:
                    self.assertEqual(
                        first=entity_id,
                        second=create_or_update_response['data']['id'],
                    )
            else:
                self.assertEqual(
                    first=create_or_update_response.status_code,
                    second=204,
                )

    @parameterized.expand([
        param(
            'read success',
        ),
        param(
            'read failure',
            create_first=False,
            raises=exceptions.InvalidPath
        ),
    ])
    def test_read_entity_by_id(self, label, create_first=True, raises=None, exception_message=''):
        entity_id = None
        if create_first:
            create_first_response = self.client.secrets.identity.create_or_update_entity(
                    name=self.TEST_ENTITY_NAME,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            logging.debug('create_first_response: %s' % create_first_response)
            entity_id = create_first_response['data']['id']
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.secrets.identity.read_entity(
                    entity_id=entity_id,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            read_entity_by_id_response = self.client.secrets.identity.read_entity(
                entity_id=entity_id,
                mount_point=self.TEST_MOUNT_POINT,
            )
            logging.debug('read_entity_by_id_response: %s' % read_entity_by_id_response)
            self.assertEqual(
                first=entity_id,
                second=read_entity_by_id_response['data']['id'],
            )

    @parameterized.expand([
        param(
            'read success',
        ),
        param(
            'read failure',
            create_first=False,
            raises=exceptions.InvalidPath
        ),
    ])
    @skipIf(utils.skip_if_vault_version_lt('0.11.2'), '"by name" operations added in Vault v0.11.2')
    def test_read_entity_by_name(self, label, create_first=True, raises=None, exception_message=''):
        entity_id = None
        if create_first:
            create_first_response = self.client.secrets.identity.create_or_update_entity(
                    name=self.TEST_ENTITY_NAME,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            logging.debug('create_first_response: %s' % create_first_response)
            entity_id = create_first_response['data']['id']
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.secrets.identity.read_entity_by_name(
                    name=self.TEST_ENTITY_NAME,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            read_entity_by_name_response = self.client.secrets.identity.read_entity_by_name(
                name=self.TEST_ENTITY_NAME,
                mount_point=self.TEST_MOUNT_POINT,
            )
            logging.debug('read_entity_by_name_response: %s' % read_entity_by_name_response)
            self.assertEqual(
                first=entity_id,
                second=read_entity_by_name_response['data']['id'],
            )

    @parameterized.expand([
        param(
            'update success',
        ),
        param(
            'update success with metadata',
            metadata=dict(something='meta')
        ),
        param(
            'update failure with metadata',
            metadata='not a dict',
            raises=exceptions.ParamValidationError,
            exception_message='unsupported metadata argument provided',
        ),
    ])
    def test_update_entity(self, label, metadata=None, raises=None, exception_message=''):
        create_first_response = self.client.secrets.identity.create_or_update_entity(
                name=self.TEST_ENTITY_NAME,
                mount_point=self.TEST_MOUNT_POINT,
            )
        logging.debug('create_first_response: %s' % create_first_response)
        entity_id = create_first_response['data']['id']
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.secrets.identity.update_entity(
                    entity_id=entity_id,
                    metadata=metadata,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            update_entity_response = self.client.secrets.identity.update_entity(
                    entity_id=entity_id,
                    metadata=metadata,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            logging.debug('update_entity_response: %s' % update_entity_response)
            if isinstance(update_entity_response, dict):
                self.assertEqual(
                    first=update_entity_response['data']['id'],
                    second=entity_id,
                )
            else:
                self.assertEqual(
                    first=update_entity_response.status_code,
                    second=204,
                )

    @parameterized.expand([
        param(
            'delete success',
        ),
        param(
            'delete success with no corresponding entity',
            create_first=False,
        ),
    ])
    def test_delete_entity_by_id(self, label, create_first=True, raises=None, exception_message=''):
        entity_id = None
        if create_first:
            create_first_response = self.client.secrets.identity.create_or_update_entity(
                    name=self.TEST_ENTITY_NAME,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            logging.debug('create_first_response: %s' % create_first_response)
            entity_id = create_first_response['data']['id']
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.secrets.identity.delete_entity(
                    entity_id=entity_id,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            delete_entity_response = self.client.secrets.identity.delete_entity(
                    entity_id=entity_id,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            logging.debug('update_entity_response: %s' % delete_entity_response)
            self.assertEqual(
                first=delete_entity_response.status_code,
                second=204,
            )

    @parameterized.expand([
        param(
            'delete success',
        ),
        param(
            'delete success with no corresponding entity',
            create_first=False,
        ),
    ])
    @skipIf(utils.skip_if_vault_version_lt('0.11.2'), '"by name" operations added in Vault v0.11.2')
    def test_delete_entity_by_name(self, label, create_first=True, raises=None, exception_message=''):
        if create_first:
            create_first_response = self.client.secrets.identity.create_or_update_entity(
                    name=self.TEST_ENTITY_NAME,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            logging.debug('create_first_response: %s' % create_first_response)
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.secrets.identity.delete_entity_by_name(
                    name=self.TEST_ENTITY_NAME,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            delete_entity_response = self.client.secrets.identity.delete_entity_by_name(
                    name=self.TEST_ENTITY_NAME,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            logging.debug('update_entity_response: %s' % delete_entity_response)
            self.assertEqual(
                first=delete_entity_response.status_code,
                second=204,
            )

    @parameterized.expand([
        param(
            'list success - LIST method',
        ),
        param(
            'list success - GET method',
            method='GET',
        ),
        param(
            'list failure - invalid method',
            method='PUT',
            raises=exceptions.ParamValidationError,
            exception_message='"method" parameter provided invalid value',
        ),
    ])
    def test_list_entities_by_id(self, label, method='LIST', raises=None, exception_message=''):
        create_response = self.client.secrets.identity.create_or_update_entity(
                name=self.TEST_ENTITY_NAME,
                mount_point=self.TEST_MOUNT_POINT,
            )
        logging.debug('create_response: %s' % create_response)
        entity_id = create_response['data']['id']
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.secrets.identity.list_entities(
                    method=method,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            list_entities_response = self.client.secrets.identity.list_entities(
                    method=method,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            logging.debug('list_entities_response: %s' % list_entities_response)
            self.assertEqual(
                first=[entity_id],
                second=list_entities_response['data']['keys'],
            )

    @parameterized.expand([
        param(
            'list success - LIST method',
        ),
        param(
            'list success - GET method',
            method='GET',
        ),
        param(
            'list failure - invalid method',
            method='PUT',
            raises=exceptions.ParamValidationError,
            exception_message='"method" parameter provided invalid value',
        ),
    ])
    @skipIf(utils.skip_if_vault_version_lt('0.11.2'), '"by name" operations added in Vault v0.11.2')
    def test_list_entities_by_name(self, label, method='LIST', raises=None, exception_message=''):
        create_response = self.client.secrets.identity.create_or_update_entity(
                name=self.TEST_ENTITY_NAME,
                mount_point=self.TEST_MOUNT_POINT,
            )
        logging.debug('create_response: %s' % create_response)
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.secrets.identity.list_entities_by_name(
                    method=method,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            list_entities_response = self.client.secrets.identity.list_entities_by_name(
                    method=method,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            logging.debug('list_entities_response: %s' % list_entities_response)
            self.assertEqual(
                first=[self.TEST_ENTITY_NAME],
                second=list_entities_response['data']['keys'],
            )

    @parameterized.expand([
        param(
            'merge success',
        ),
        param(
            'merge failure',
        ),
    ])
    def test_merge_entities(self, label, raises=None, exception_message=''):
        create_response = self.client.secrets.identity.create_or_update_entity(
                name=self.TEST_ENTITY_NAME,
                mount_point=self.TEST_MOUNT_POINT,
            )
        logging.debug('create_response: %s' % create_response)
        create_response2 = self.client.secrets.identity.create_or_update_entity(
                name='%s2' % self.TEST_ENTITY_NAME,
                mount_point=self.TEST_MOUNT_POINT,
            )
        logging.debug('create_response2: %s' % create_response)
        to_entity_id = create_response['data']['id']
        from_entity_ids = [create_response2['data']['id']]
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.secrets.identity.merge_entities(
                    from_entity_ids=from_entity_ids,
                    to_entity_id=to_entity_id,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            merge_entities_response = self.client.secrets.identity.merge_entities(
                    from_entity_ids=from_entity_ids,
                    to_entity_id=to_entity_id,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            logging.debug('merge_entities_response: %s' % merge_entities_response)
            self.assertEqual(
                first=merge_entities_response.status_code,
                second=204,
            )

    @parameterized.expand([
        param(
            'create success',
        ),
        param(
            'update success',
            create_first=True,
        ),
    ])
    def test_create_or_update_entity_alias(self, label, create_first=False, raises=None, exception_message=''):
        entity_id = None
        if create_first:
            create_first_response = self.client.secrets.identity.create_or_update_entity(
                    name=self.TEST_ENTITY_NAME,
                    entity_id=entity_id,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            logging.debug('create_first_response: %s' % create_first_response)
            entity_id = create_first_response['data']['id']
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.secrets.identity.create_or_update_entity_alias(
                    name=self.TEST_ALIAS_NAME,
                    canonical_id=entity_id,
                    mount_accessor=self.test_approle_accessor,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            create_or_update_response = self.client.secrets.identity.create_or_update_entity_alias(
                    name=self.TEST_ALIAS_NAME,
                    canonical_id=entity_id,
                    mount_accessor=self.test_approle_accessor,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            logging.debug('create_or_update_response: %s' % create_or_update_response)

            self.assertIn(
                member='id',
                container=create_or_update_response['data'],
            )
            if entity_id is not None:
                self.assertEqual(
                    first=create_or_update_response['data']['canonical_id'],
                    second=entity_id,
                )

    @parameterized.expand([
        param(
            'read success',
        ),
        param(
            'read failure',
            create_first=False,
            raises=exceptions.InvalidPath,
        ),
    ])
    def test_read_entity_alias_by_id(self, label, create_first=True, raises=None, exception_message=''):
        alias_id = None
        if create_first:
            create_entity_first_response = self.client.secrets.identity.create_or_update_entity(
                    name=self.TEST_ENTITY_NAME,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            logging.debug('create_entity_first_response: %s' % create_entity_first_response)
            entity_id = create_entity_first_response['data']['id']
            create_entity_alias_first_response = self.client.secrets.identity.create_or_update_entity_alias(
                    name=self.TEST_ALIAS_NAME,
                    canonical_id=entity_id,
                    mount_accessor=self.test_approle_accessor,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            logging.debug('create_entity_alias_first_response: %s' % create_entity_alias_first_response)
            alias_id = create_entity_alias_first_response['data']['id']
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.secrets.identity.read_entity_alias(
                    alias_id=alias_id,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            read_entity_alias_response = self.client.secrets.identity.read_entity_alias(
                    alias_id=alias_id,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            logging.debug('read_entity_alias_response: %s' % read_entity_alias_response)

            self.assertIn(
                member='id',
                container=read_entity_alias_response['data'],
            )
            if alias_id is not None:
                self.assertEqual(
                    first=read_entity_alias_response['data']['id'],
                    second=alias_id,
                )

    @parameterized.expand([
        param(
            'update success',
        ),
        param(
            'update failure with invalid mount accessor',
            mount_accessor='not a valid accessor',
            raises=exceptions.InvalidRequest,
            exception_message='invalid mount accessor',
        ),
    ])
    def test_update_entity_alias_by_id(self, label, mount_accessor=None, raises=None, exception_message=''):
        if mount_accessor is None:
            mount_accessor = self.test_approle_accessor
        create_entity_first_response = self.client.secrets.identity.create_or_update_entity(
                name=self.TEST_ENTITY_NAME,
                mount_point=self.TEST_MOUNT_POINT,
            )
        logging.debug('create_entity_first_response: %s' % create_entity_first_response)
        entity_id = create_entity_first_response['data']['id']
        create_entity_alias_first_response = self.client.secrets.identity.create_or_update_entity_alias(
                name=self.TEST_ALIAS_NAME,
                canonical_id=entity_id,
                mount_accessor=self.test_approle_accessor,
                mount_point=self.TEST_MOUNT_POINT,
            )
        logging.debug('create_entity_alias_first_response: %s' % create_entity_alias_first_response)
        alias_id = create_entity_alias_first_response['data']['id']
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.secrets.identity.update_entity_alias(
                    alias_id=alias_id,
                    name=self.TEST_ALIAS_NAME,
                    canonical_id=entity_id,
                    mount_accessor=mount_accessor,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            update_entity_response = self.client.secrets.identity.update_entity_alias(
                    alias_id=alias_id,
                    name=self.TEST_ALIAS_NAME,
                    canonical_id=entity_id,
                    mount_accessor=mount_accessor,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            logging.debug('update_entity_response: %s' % update_entity_response)
            if isinstance(update_entity_response, dict):
                self.assertIn(
                    member='id',
                    container=update_entity_response['data'],
                )
                self.assertEqual(
                    first=update_entity_response['data']['id'],
                    second=alias_id,
                )
            else:
                self.assertEqual(
                    first=update_entity_response.status_code,
                    second=204,
                )

    @parameterized.expand([
        param(
            'list success - LIST method',
        ),
        param(
            'list success - GET method',
            method='GET',
        ),
        param(
            'list failure - invalid method',
            method='PUT',
            raises=exceptions.ParamValidationError,
            exception_message='"method" parameter provided invalid value',
        ),
    ])
    def test_list_entity_aliases_by_id(self, label, method='LIST', raises=None, exception_message=''):
        create_response = self.client.secrets.identity.create_or_update_entity(
                name=self.TEST_ENTITY_NAME,
                mount_point=self.TEST_MOUNT_POINT,
            )
        logging.debug('create_response: %s' % create_response)
        entity_id = create_response['data']['id']
        create_entity_alias_first_response = self.client.secrets.identity.create_or_update_entity_alias(
                name=self.TEST_ALIAS_NAME,
                canonical_id=entity_id,
                mount_accessor=self.test_approle_accessor,
                mount_point=self.TEST_MOUNT_POINT,
            )
        alias_id = create_entity_alias_first_response['data']['id']
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.secrets.identity.list_entity_aliases(
                    method=method,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            list_entities_response = self.client.secrets.identity.list_entity_aliases(
                    method=method,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            logging.debug('list_entities_response: %s' % list_entities_response)
            self.assertEqual(
                first=[alias_id],
                second=list_entities_response['data']['keys'],
            )

    @parameterized.expand([
        param(
            'delete success',
        ),
        param(
            'delete success with no corresponding entity',
            create_first=False,
        ),
    ])
    def test_delete_entity_alias_by_id(self, label, create_first=True, raises=None, exception_message=''):
        alias_id = None
        if create_first:
            create_first_response = self.client.secrets.identity.create_or_update_entity(
                    name=self.TEST_ENTITY_NAME,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            logging.debug('create_first_response: %s' % create_first_response)
            entity_id = create_first_response['data']['id']
            create_entity_alias_first_response = self.client.secrets.identity.create_or_update_entity_alias(
                    name=self.TEST_ALIAS_NAME,
                    canonical_id=entity_id,
                    mount_accessor=self.test_approle_accessor,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            alias_id = create_entity_alias_first_response['data']['id']
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.secrets.identity.delete_entity_alias(
                    alias_id=alias_id,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            delete_entity_response = self.client.secrets.identity.delete_entity_alias(
                    alias_id=alias_id,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            logging.debug('update_entity_response: %s' % delete_entity_response)
            self.assertEqual(
                first=delete_entity_response.status_code,
                second=204,
            )

    @parameterized.expand([
        param(
            'create success',
        ),
        param(
            'create success with metadata',
            metadata=dict(something='meta')
        ),
        param(
            'create failure with metadata',
            metadata='not a dict',
            raises=exceptions.ParamValidationError,
            exception_message='unsupported metadata argument provided',
        ),
        param(
            'create success with group type',
            group_type='external',
        ),
        param(
            'create failure with invalid group type',
            group_type='cosmic',
            raises=exceptions.ParamValidationError,
            exception_message='unsupported group_type argument provided "cosmic"',
        ),
        param(
            'update success',
            create_first=True,
        ),
    ])
    def test_create_or_update_group(self, label, metadata=None, group_type='internal', create_first=False, raises=None, exception_message=''):
        group_id = None
        if create_first:
            create_first_response = self.client.secrets.identity.create_or_update_group(
                    name=self.TEST_GROUP_NAME,
                    group_type=group_type,
                    metadata=metadata,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            logging.debug('create_first_response: %s' % create_first_response)
            group_id = create_first_response['data']['id']
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.secrets.identity.create_or_update_group(
                    name=self.TEST_GROUP_NAME,
                    group_id=group_id,
                    group_type=group_type,
                    metadata=metadata,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            create_or_update_response = self.client.secrets.identity.create_or_update_group(
                    name=self.TEST_GROUP_NAME,
                    group_id=group_id,
                    group_type=group_type,
                    metadata=metadata,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            logging.debug('create_or_update_response: %s' % create_or_update_response)
            if isinstance(create_or_update_response, dict):
                self.assertIn(
                    member='id',
                    container=create_or_update_response['data'],
                )
                if group_id is not None:
                    self.assertEqual(
                        first=group_id,
                        second=create_or_update_response['data']['id'],
                    )
            else:
                self.assertEqual(
                    first=create_or_update_response.status_code,
                    second=204,
                )

    @parameterized.expand([
        param(
            'update success',
        ),
        param(
            'update success with metadata',
            metadata=dict(something='meta')
        ),
        param(
            'update failure with metadata',
            metadata='not a dict',
            raises=exceptions.ParamValidationError,
            exception_message='unsupported metadata argument provided',
        ),
        param(
            'update failure with changed group type',
            group_type='external',
            raises=exceptions.InvalidRequest,
            exception_message='group type cannot be changed',
        ),
        param(
            'update failure with invalid group type',
            group_type='cosmic',
            raises=exceptions.ParamValidationError,
            exception_message='unsupported group_type argument provided "cosmic"',
        ),
        param(
            'update success',
            create_first=True,
        ),
    ])
    def test_update_group_by_id(self, label, metadata=None, group_type='internal', create_first=True, raises=None, exception_message=''):
        group_id = None
        if create_first:
            create_first_response = self.client.secrets.identity.create_or_update_group(
                    name=self.TEST_GROUP_NAME,
                    group_type='internal',
                    metadata=None,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            logging.debug('create_first_response: %s' % create_first_response)
            group_id = create_first_response['data']['id']
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.secrets.identity.update_group(
                    name=self.TEST_GROUP_NAME,
                    group_id=group_id,
                    group_type=group_type,
                    metadata=metadata,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            update_response = self.client.secrets.identity.update_group(
                    name=self.TEST_GROUP_NAME,
                    group_id=group_id,
                    group_type=group_type,
                    metadata=metadata,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            logging.debug('update_response: %s' % update_response)

            if isinstance(update_response, dict):
                self.assertEqual(
                    first=update_response['data']['id'],
                    second=group_id,
                )
            else:
                self.assertEqual(
                    first=update_response.status_code,
                    second=204,
                )

    @parameterized.expand([
        param(
            'list success - LIST method',
        ),
        param(
            'list success - GET method',
            method='GET',
        ),
        param(
            'list failure - invalid method',
            method='PUT',
            raises=exceptions.ParamValidationError,
            exception_message='"method" parameter provided invalid value',
        ),
    ])
    @skipIf(utils.skip_if_vault_version_lt('0.11.2'), '"by name" operations added in Vault v0.11.2')
    def test_list_groups_by_name(self, label, method='LIST', raises=None, exception_message=''):
        create_response = self.client.secrets.identity.create_or_update_group(
                name=self.TEST_GROUP_NAME,
                mount_point=self.TEST_MOUNT_POINT,
            )
        logging.debug('create_response: %s' % create_response)
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.secrets.identity.list_groups_by_name(
                    method=method,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            list_groups_response = self.client.secrets.identity.list_groups_by_name(
                    method=method,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            logging.debug('list_groups_response: %s' % list_groups_response)
            self.assertEqual(
                first=[self.TEST_GROUP_NAME],
                second=list_groups_response['data']['keys'],
            )

    @parameterized.expand([
        param(
            'update success',
        ),
        param(
            'update success with metadata',
            metadata=dict(something='meta')
        ),
        param(
            'update failure with metadata',
            metadata='not a dict',
            raises=exceptions.ParamValidationError,
            exception_message='unsupported metadata argument provided',
        ),
        param(
            'update failure with changed group type',
            group_type='external',
            raises=exceptions.InvalidRequest,
            exception_message='group type cannot be changed',
        ),
        param(
            'update failure with invalid group type',
            group_type='cosmic',
            raises=exceptions.ParamValidationError,
            exception_message='unsupported group_type argument provided "cosmic"',
        ),
        param(
            'update success',
            create_first=True,
        ),
    ])
    @skipIf(utils.skip_if_vault_version_lt('0.11.2'), '"by name" operations added in Vault v0.11.2')
    def test_create_or_update_group_by_name(self, label, metadata=None, group_type='internal', create_first=True, raises=None, exception_message=''):
        if create_first:
            create_first_response = self.client.secrets.identity.create_or_update_group(
                    name=self.TEST_GROUP_NAME,
                    group_type='internal',
                    metadata=None,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            logging.debug('create_first_response: %s' % create_first_response)
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.secrets.identity.create_or_update_group_by_name(
                    name=self.TEST_GROUP_NAME,
                    group_type=group_type,
                    metadata=metadata,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            update_response = self.client.secrets.identity.create_or_update_group_by_name(
                    name=self.TEST_GROUP_NAME,
                    group_type=group_type,
                    metadata=metadata,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            logging.debug('update_response: %s' % update_response)
            self.assertEqual(
                first=update_response.status_code,
                second=204,
            )

    @parameterized.expand([
        param(
            'read success',
        ),
        param(
            'read failure',
            create_first=False,
            raises=exceptions.InvalidPath
        ),
    ])
    @skipIf(utils.skip_if_vault_version_lt('0.11.2'), '"by name" operations added in Vault v0.11.2')
    def test_read_group_by_name(self, label, create_first=True, raises=None, exception_message=''):
        group_id = None
        if create_first:
            create_first_response = self.client.secrets.identity.create_or_update_group(
                    name=self.TEST_GROUP_NAME,
                    group_type='internal',
                    metadata=None,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            logging.debug('create_first_response: %s' % create_first_response)
            group_id = create_first_response['data']['id']
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.secrets.identity.read_entity_by_name(
                    name=self.TEST_GROUP_NAME,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            read_group_response = self.client.secrets.identity.read_group_by_name(
                name=self.TEST_GROUP_NAME,
                mount_point=self.TEST_MOUNT_POINT,
            )
            logging.debug('read_group_response: %s' % read_group_response)
            self.assertEqual(
                first=group_id,
                second=read_group_response['data']['id'],
            )

    @parameterized.expand([
        param(
            'create success',
        ),
        param(
            'update success',
            create_first=True,
        ),
    ])
    def test_create_or_update_group_alias(self, label, create_first=False, raises=None, exception_message=''):
        alias_id = None
        create_first_response = self.client.secrets.identity.create_or_update_group(
                name=self.TEST_ENTITY_NAME,
                mount_point=self.TEST_MOUNT_POINT,
            )
        logging.debug('create_first_response: %s' % create_first_response)
        if create_first:
            create_alias_response = self.client.secrets.identity.create_or_update_group_alias(
                    name=self.TEST_GROUP_NAME,
                    mount_accessor=self.test_approle_accessor,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            logging.debug('create_alias_response: %s' % create_alias_response)
            alias_id = create_alias_response['data']['id']
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.secrets.identity.create_or_update_group_alias(
                    name=self.TEST_ENTITY_NAME,
                    alias_id=alias_id,
                    mount_accessor=self.test_approle_accessor,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            create_or_update_response = self.client.secrets.identity.create_or_update_group_alias(
                    name=self.TEST_GROUP_NAME,
                    alias_id=alias_id,
                    mount_accessor=self.test_approle_accessor,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            logging.debug('create_or_update_response: %s' % create_or_update_response)
            # if not create_first:
            self.assertIn(
                member='id',
                container=create_or_update_response['data'],
            )
            if alias_id is not None:
                self.assertEqual(
                    first=alias_id,
                    second=create_or_update_response['data']['id'],
                )
            # else:
            #     self.assertEqual(
            #         first=create_or_update_response.status_code,
            #         second=204,
            #     )

    @parameterized.expand([
        param(
            'read success',
        ),
        param(
            'read failure',
            create_first=False,
            raises=exceptions.InvalidPath,
        ),
    ])
    def test_read_group_alias(self, label, create_first=True, raises=None, exception_message=''):
        alias_id = None
        create_first_response = self.client.secrets.identity.create_or_update_group(
                name=self.TEST_ENTITY_NAME,
                mount_point=self.TEST_MOUNT_POINT,
            )
        logging.debug('create_first_response: %s' % create_first_response)
        if create_first:
            create_alias_response = self.client.secrets.identity.create_or_update_group_alias(
                    name=self.TEST_GROUP_NAME,
                    mount_accessor=self.test_approle_accessor,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            logging.debug('create_alias_response: %s' % create_alias_response)
            alias_id = create_alias_response['data']['id']
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.secrets.identity.read_group_alias(
                    alias_id=alias_id,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            read_group_alias_response = self.client.secrets.identity.read_group_alias(
                    alias_id=alias_id,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            logging.debug('read_group_alias_response: %s' % read_group_alias_response)

            self.assertIn(
                member='id',
                container=read_group_alias_response['data'],
            )
            if alias_id is not None:
                self.assertEqual(
                    first=read_group_alias_response['data']['id'],
                    second=alias_id,
                )

    @parameterized.expand([
        param(
            'list success - LIST method',
        ),
        param(
            'list success - GET method',
            method='GET',
        ),
        param(
            'list failure - invalid method',
            method='PUT',
            raises=exceptions.ParamValidationError,
            exception_message='"method" parameter provided invalid value',
        ),
    ])
    def test_list_group_aliases(self, label, method='LIST', raises=None, exception_message=''):
        create_group_response = self.client.secrets.identity.create_or_update_group(
                name=self.TEST_GROUP_ALIAS_NAME,
                group_type='internal',
                metadata=None,
                mount_point=self.TEST_MOUNT_POINT,
            )
        logging.debug('create_group_response: %s' % create_group_response)
        create_alias_response = self.client.secrets.identity.create_or_update_group_alias(
                name=self.TEST_GROUP_NAME,
                mount_accessor=self.test_approle_accessor,
                mount_point=self.TEST_MOUNT_POINT,
            )
        logging.debug('create_alias_response: %s' % create_alias_response)
        alias_id = create_alias_response['data']['id']
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.secrets.identity.list_group_aliases(
                    method=method,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            list_groups_response = self.client.secrets.identity.list_group_aliases(
                    method=method,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            logging.debug('list_groups_response: %s' % list_groups_response)
            self.assertEqual(
                first=[alias_id],
                second=list_groups_response['data']['keys'],
            )

    @parameterized.expand([
        param(
            'lookup entity',
            criteria=['entity_id'],
        ),
        param(
            'lookup entity alias',
            criteria=['alias_id'],
        ),
    ])
    def test_lookup_entity(self, label, criteria, raises=None, exception_message=''):
        lookup_params = {}
        create_entity_response = self.client.secrets.identity.create_or_update_entity(
                name=self.TEST_ENTITY_NAME,
                mount_point=self.TEST_MOUNT_POINT,
            )
        logging.debug('create_entity_response: %s' % create_entity_response)
        entity_id = create_entity_response['data']['id']
        create_alias_response = self.client.secrets.identity.create_or_update_entity_alias(
                name=self.TEST_ALIAS_NAME,
                canonical_id=entity_id,
                mount_accessor=self.test_approle_accessor,
                mount_point=self.TEST_MOUNT_POINT,
            )
        logging.debug('create_alias_response: %s' % create_alias_response)
        alias_id = create_alias_response['data']['id']
        if 'entity_id' in criteria:
            lookup_params['entity_id'] = entity_id
        elif 'alias_id' in criteria:
            lookup_params['alias_id'] = alias_id
        logging.debug('lookup_params: %s' % lookup_params)
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.secrets.identity.lookup_entity(
                    mount_point=self.TEST_MOUNT_POINT,
                    **lookup_params
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            lookup_entity_response = self.client.secrets.identity.lookup_entity(
                    mount_point=self.TEST_MOUNT_POINT,
                    **lookup_params
                )
            logging.debug('lookup_entity_response: %s' % lookup_entity_response)
            if 'entity_id' in criteria:
                self.assertEqual(
                    first=lookup_entity_response['data']['name'],
                    second=self.TEST_ENTITY_NAME,
                )
            elif 'alias_id' in criteria:
                self.assertEqual(
                    first=lookup_entity_response['data']['aliases'][0]['name'],
                    second=self.TEST_ALIAS_NAME,
                )

    @parameterized.expand([
        param(
            'lookup group',
            criteria=['group_id'],
        ),
        param(
            'lookup group alias',
            criteria=['alias_id'],
        ),
        param(
            'lookup name',
            criteria=['name'],
        ),
        param(
            'lookup alias',
            criteria=['alias_name', 'alias_mount_accessor'],
        ),
    ])
    def test_lookup_group(self, label, criteria, raises=None, exception_message=''):
        lookup_params = {}
        create_group_response = self.client.secrets.identity.create_or_update_group(
                name=self.TEST_GROUP_NAME,
                group_type='external',
                mount_point=self.TEST_MOUNT_POINT,
            )
        logging.debug('create_group_response: %s' % create_group_response)
        group_id = create_group_response['data']['id']
        create_alias_response = self.client.secrets.identity.create_or_update_group_alias(
                    name=self.TEST_GROUP_ALIAS_NAME,
                    canonical_id=group_id,
                    mount_accessor=self.test_approle_accessor,
                    mount_point=self.TEST_MOUNT_POINT,
                )
        logging.debug('create_alias_response: %s' % create_alias_response)
        alias_id = create_alias_response['data']['id']
        if 'group_id' in criteria:
            lookup_params['group_id'] = group_id
        elif 'alias_id' in criteria:
            lookup_params['alias_id'] = alias_id
        elif 'name' in criteria:
            lookup_params['name'] = self.TEST_GROUP_NAME
        elif 'alias_name' in criteria and 'alias_mount_accessor' in criteria:
            lookup_params['alias_name'] = self.TEST_GROUP_ALIAS_NAME
            lookup_params['alias_mount_accessor'] = self.test_approle_accessor
        logging.debug('lookup_params: %s' % lookup_params)
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.secrets.identity.lookup_group(
                    mount_point=self.TEST_MOUNT_POINT,
                    **lookup_params
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            lookup_group_response = self.client.secrets.identity.lookup_group(
                    mount_point=self.TEST_MOUNT_POINT,
                    **lookup_params
                )
            logging.debug('lookup_group_response: %s' % lookup_group_response)
            if 'group_id' in criteria or 'name' in criteria:
                self.assertEqual(
                    first=lookup_group_response['data']['name'],
                    second=self.TEST_GROUP_NAME,
                )
            elif 'alias_id' in criteria or ('alias_name' in criteria and 'alias_mount_accessor' in criteria):
                self.assertEqual(
                    first=lookup_group_response['data']['alias']['name'],
                    second=self.TEST_GROUP_ALIAS_NAME,
                )
