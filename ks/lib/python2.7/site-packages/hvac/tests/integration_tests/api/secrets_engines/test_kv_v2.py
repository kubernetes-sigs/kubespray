import logging
from unittest import TestCase
from unittest import skipIf

from parameterized import parameterized, param

from hvac import exceptions
from hvac.tests import utils


@skipIf(utils.skip_if_vault_version_lt('0.10.0'), "KV version 2 secret engine not available before Vault version 0.10.0")
class TestKvV2(utils.HvacIntegrationTestCase, TestCase):
    DEFAULT_MOUNT_POINT = 'kvv2'

    def setUp(self):
        super(TestKvV2, self).setUp()
        self.client.enable_secret_backend(
            backend_type='kv',
            mount_point=self.DEFAULT_MOUNT_POINT,
            options=dict(version=2),
        )

    def tearDown(self):
        self.client.disable_secret_backend(mount_point=self.DEFAULT_MOUNT_POINT)
        super(TestKvV2, self).tearDown()

    @parameterized.expand([
        ('no parameters',),
        ('set max versions', 1),
        ('set cas required', 10, True),
        ('set max versions and cas required', 17, True),
    ])
    def test_configure_and_read_configuration(self, test_label, max_versions=10, cas_required=None):
        configure_arguments = dict(mount_point=self.DEFAULT_MOUNT_POINT)
        if max_versions is not None:
            configure_arguments['max_versions'] = max_versions
        if cas_required is not None:
            configure_arguments['cas_required'] = cas_required
        self.client.secrets.kv.v2.configure(**configure_arguments)
        read_configuration_response = self.client.secrets.kv.v2.read_configuration(
            mount_point=self.DEFAULT_MOUNT_POINT,
        )
        logging.debug('read_configuration_response: %s' % read_configuration_response)
        self.assertEqual(
            first=max_versions,
            second=read_configuration_response['data']['max_versions'],
        )
        self.assertEqual(
            first=cas_required or False,
            second=read_configuration_response['data']['cas_required'],
        )

    @parameterized.expand([
        ('nonexistent secret', 'no-secret-here', None, False, exceptions.InvalidPath),
        ('read secret version 2 back', 'top-secret', 2, 2),
        ('read secret version 1 back', 'top-secret', 1, 5),
        ('read current secret version', 'top-secret', None, 10),
        ('read current secret version', 'top-secret', None, 15),
    ])
    def test_read_secret_version(self, test_label, path, version=None, write_secret_before_test=True, raises=None):
        if write_secret_before_test:
            for num in range(1, write_secret_before_test + 1):
                test_secret = {
                    'pssst': num,
                }
                self.client.secrets.kv.v2.create_or_update_secret(
                    path=path,
                    secret=test_secret,
                    mount_point=self.DEFAULT_MOUNT_POINT
                )
        if raises:
            with self.assertRaises(raises):
                self.client.secrets.kv.v2.read_secret_version(
                    path=path,
                    version=version,
                    mount_point=self.DEFAULT_MOUNT_POINT,
                )
        else:
            read_secret_result = self.client.secrets.kv.v2.read_secret_version(
                path=path,
                version=version,
                mount_point=self.DEFAULT_MOUNT_POINT,
            )
            logging.debug('read_secret_result: %s' % read_secret_result)
            expected_version = version or write_secret_before_test
            self.assertDictEqual(
                d1=dict(pssst=expected_version),
                d2=read_secret_result['data']['data'],
            )

    @parameterized.expand([
        ('create secret', 'hvac', None, False),
        ('create secret with cas of 0', 'hvac', 0, False),
        ('update secret', 'hvac', None),
        ('update secret with valid cas of 1', 'hvac', 1, True),
        ('update secret with invalid cas', 'hvac', -1, True, exceptions.InvalidRequest, 'did not match the current version'),
        ('update with cas of 0 after path already written', 'hvac', 0, True, exceptions.InvalidRequest, 'did not match the current version'),
    ])
    def test_create_or_update_secret(self, test_label, path, cas=None, write_secret_before_test=True, raises=None, exception_message=''):
        test_secret = {
            'pssst': 'hi',
        }

        if write_secret_before_test:
            self.client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret=test_secret,
                mount_point=self.DEFAULT_MOUNT_POINT,
            )
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.secrets.kv.v2.create_or_update_secret(
                    path=path,
                    secret=test_secret,
                    cas=cas,
                    mount_point=self.DEFAULT_MOUNT_POINT,
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            create_or_update_secret_result = self.client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret=test_secret,
                cas=cas,
                mount_point=self.DEFAULT_MOUNT_POINT,
            )
            expected_version = 2 if write_secret_before_test else 1
            logging.debug('create_or_update_secret_result: %s' % create_or_update_secret_result)
            self.assertEqual(
                first=expected_version,
                second=create_or_update_secret_result['data']['version'],
            )

    @parameterized.expand([
        param(
            'add new key to existing secret',
            update_dict=dict(new_key='some secret')
        ),
        param(
            'add new key to nonexistent secret',
            update_dict=dict(new_key='some secret'),
            write_secret_before_test=False,
            raises=exceptions.InvalidPath,
            exception_message='patch only works on existing data.',
        ),
        param(
            'update existing key on existing secret',
            update_dict=dict(pssst='some secret')
        ),
    ])
    def test_patch(self, label, update_dict, mount_point=DEFAULT_MOUNT_POINT, write_secret_before_test=True, raises=None, exception_message=''):
        path = 'hvac_kv_v2_test_patch'
        test_secret = {
            'pssst': 'hi',
        }

        if write_secret_before_test:
            self.client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret=test_secret,
                mount_point=mount_point,
            )
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.secrets.kv.v2.patch(
                    path=path,
                    secret=update_dict,
                    mount_point=mount_point,
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            patch_result = self.client.secrets.kv.v2.patch(
                path=path,
                secret=update_dict,
                mount_point=mount_point,
            )
            expected_version = 2 if write_secret_before_test else 1
            logging.debug('patch_result: %s' % patch_result)
            self.assertEqual(
                first=expected_version,
                second=patch_result['data']['version'],
            )

            read_secret_result = self.client.secrets.kv.v2.read_secret_version(
                path=path,
                mount_point=mount_point,
            )
            logging.debug('read_secret_result: %s' % read_secret_result)
            for k, v in update_dict.items():
                self.assertEqual(
                    first=v,
                    second=read_secret_result['data']['data'][k]
                )

    @parameterized.expand([
        ('successful delete one version written', 'hvac'),
        ('successful delete two versions written', 'hvac', 2),
        ('successful delete three versions written', 'hvac', 3),
        ('nonexistent path', 'no-secret-here', 0, exceptions.InvalidPath),
    ])
    def test_delete_latest_version_of_secret(self, test_label, path, write_secret_before_test=1, raises=None, exception_message=''):
        if write_secret_before_test:
            for num in range(1, write_secret_before_test + 1):
                test_secret = {
                    'pssst': num,
                }
                self.client.secrets.kv.v2.create_or_update_secret(
                    path=path,
                    secret=test_secret,
                    mount_point=self.DEFAULT_MOUNT_POINT
                )
        if raises:
            self.client.secrets.kv.v2.delete_latest_version_of_secret(
                path=path,
                mount_point=self.DEFAULT_MOUNT_POINT,
            )
            with self.assertRaises(raises) as cm:
                self.client.secrets.kv.v2.read_secret_metadata(
                    path=path,
                    mount_point=self.DEFAULT_MOUNT_POINT,
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            delete_latest_version_of_secret_result = self.client.secrets.kv.v2.delete_latest_version_of_secret(
                path=path,
                mount_point=self.DEFAULT_MOUNT_POINT,
            )
            logging.debug('delete_latest_version_of_secret_result: %s' % delete_latest_version_of_secret_result)
            read_secret_metadata_result = self.client.secrets.kv.v2.read_secret_metadata(
                path=path,
                mount_point=self.DEFAULT_MOUNT_POINT,
            )
            logging.debug('read_secret_metadata_result: %s' % read_secret_metadata_result)
            self.assertNotEqual(
                first=read_secret_metadata_result['data']['versions'][str(write_secret_before_test)]['deletion_time'],
                second=''
            )
            for num in range(1, write_secret_before_test):
                self.assertEqual(
                    first=read_secret_metadata_result['data']['versions'][str(num)]['deletion_time'],
                    second='',
                )

    @parameterized.expand([
        ('successful delete one version written', 'hvac', 1, [1]),
        ('successful delete one out of two versions written 1', 'hvac', 2, [1]),
        ('successful delete one out of two versions written 2', 'hvac', 2, [2]),
        ('successful delete two out of two versions written', 'hvac', 2, [1, 2]),
        ('successful delete three out of seven versions written 135', 'hvac', 7, [1, 3, 5]),
        ('successful delete three out of seven versions written 137', 'hvac', 7, [1, 3, 7]),
        ('invalid versions arg none', 'boom', 0, None, exceptions.ParamValidationError),
        ('invalid versions arg empty', 'boom', 0, [], exceptions.ParamValidationError),
        ('invalid versions arg not a list', 'goes', 0, '1', exceptions.ParamValidationError),
        ('nonexistent version 1', 'no-version-here', 3, [5]),
        ('nonexistent version 2', 'no-versions-here', 3, [7, 9]),
        ('nonexistent version 3', 'no-versions-here', 3, [7, 12]),
    ])
    def test_delete_secret_versions(self, test_label, path, write_secret_before_test=1, deleted_versions=None, raises=None, exception_message=''):

        if write_secret_before_test:
            for num in range(1, write_secret_before_test + 1):
                test_secret = {
                    'pssst': num,
                }
                self.client.secrets.kv.v2.create_or_update_secret(
                    path=path,
                    secret=test_secret,
                    mount_point=self.DEFAULT_MOUNT_POINT
                )
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.secrets.kv.v2.delete_secret_versions(
                    path=path,
                    versions=deleted_versions,
                    mount_point=self.DEFAULT_MOUNT_POINT,
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            delete_secret_versions_result = self.client.secrets.kv.v2.delete_secret_versions(
                path=path,
                versions=deleted_versions,
                mount_point=self.DEFAULT_MOUNT_POINT,
            )
            logging.debug('delete_secret_versions_result: %s' % delete_secret_versions_result)
            read_secret_metadata_result = self.client.secrets.kv.v2.read_secret_metadata(
                path=path,
                mount_point=self.DEFAULT_MOUNT_POINT,
            )
            logging.debug('read_secret_metadata_result: %s' % read_secret_metadata_result)

            for deleted_version in deleted_versions:
                if str(deleted_version) in read_secret_metadata_result['data']['versions']:
                    self.assertNotEqual(
                        first=read_secret_metadata_result['data']['versions'][str(deleted_version)]['deletion_time'],
                        second='',
                        msg='Version "{num}" should be deleted but is not. Full read metadata response versions: {metadata}'.format(
                            num=deleted_version,
                            metadata=read_secret_metadata_result['data']['versions'],
                        )
                    )

            for nondeleted_version in set(range(1, write_secret_before_test + 1)) - set(deleted_versions):
                self.assertEqual(
                    first=read_secret_metadata_result['data']['versions'][str(nondeleted_version)]['deletion_time'],
                    second='',
                    msg='Version "{num}" should not be deleted but is. Full read metadata response versions: {metadata}'.format(
                        num=nondeleted_version,
                        metadata=read_secret_metadata_result['data']['versions'],
                    )
                )

    @parameterized.expand([
        ('successful undelete one version written', 'hvac', 1, [1]),
        ('successful undelete one out of two versions written 1', 'hvac', 2, [1]),
        ('successful undelete one out of two versions written 2', 'hvac', 2, [2]),
        ('successful undelete two out of two versions written', 'hvac', 2, [1, 2]),
        ('successful undelete three out of seven versions written 135', 'hvac', 7, [1, 3, 5]),
        ('successful undelete three out of seven versions written 137', 'hvac', 7, [1, 3, 7]),
        ('invalid versions arg none', 'boom', 0, None, exceptions.ParamValidationError),
        ('invalid versions arg empty', 'boom', 0, [], exceptions.ParamValidationError),
        ('invalid versions arg not a list', 'goes', 1, '1', exceptions.ParamValidationError),
        ('nonexistent version 1', 'no-version-here', 3, [5]),
        ('nonexistent version 2', 'no-versions-here', 3, [7, 9]),
        ('nonexistent version 3', 'no-versions-here', 3, [7, 12]),
    ])
    def test_undelete_secret_versions(self, test_label, path, write_secret_before_test=1, undeleted_versions=None, raises=None, exception_message=''):

        if write_secret_before_test:
            for num in range(1, write_secret_before_test + 1):
                test_secret = {
                    'pssst': num,
                }
                self.client.secrets.kv.v2.create_or_update_secret(
                    path=path,
                    secret=test_secret,
                    mount_point=self.DEFAULT_MOUNT_POINT
                )
                self.client.secrets.kv.v2.delete_latest_version_of_secret(
                    path=path,
                    mount_point=self.DEFAULT_MOUNT_POINT
                )
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.secrets.kv.v2.undelete_secret_versions(
                    path=path,
                    versions=undeleted_versions,
                    mount_point=self.DEFAULT_MOUNT_POINT,
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            delete_secret_versions_result = self.client.secrets.kv.v2.undelete_secret_versions(
                path=path,
                versions=undeleted_versions,
                mount_point=self.DEFAULT_MOUNT_POINT,
            )
            logging.debug('delete_secret_versions_result: %s' % delete_secret_versions_result)
            read_secret_metadata_result = self.client.secrets.kv.v2.read_secret_metadata(
                path=path,
                mount_point=self.DEFAULT_MOUNT_POINT,
            )
            logging.debug('read_secret_metadata_result: %s' % read_secret_metadata_result)
            for deleted_version in undeleted_versions:
                if str(deleted_version) in read_secret_metadata_result['data']['versions']:
                    self.assertEqual(
                        first=read_secret_metadata_result['data']['versions'][str(deleted_version)]['deletion_time'],
                        second='',
                        msg='Version "{num}" should be undeleted but is not. Full read metadata response versions: {metadata}'.format(
                            num=deleted_version,
                            metadata=read_secret_metadata_result['data']['versions'],
                        )
                    )

            for nondeleted_version in set(range(1, write_secret_before_test + 1)) - set(undeleted_versions):
                self.assertNotEqual(
                    first=read_secret_metadata_result['data']['versions'][str(nondeleted_version)]['deletion_time'],
                    second='',
                    msg='Version "{num}" should be deleted but it is not. Full read metadata response versions: {metadata}'.format(
                        num=nondeleted_version,
                        metadata=read_secret_metadata_result['data']['versions'],
                    )
                )

    @parameterized.expand([
        ('successful destroy one version written', 'hvac', 1, [1]),
        ('successful destroy one out of two versions written 1', 'hvac', 2, [1]),
        ('successful destroy one out of two versions written 2', 'hvac', 2, [2]),
        ('successful destroy two out of two versions written', 'hvac', 2, [1, 2]),
        ('successful destroy three out of seven versions written 135', 'hvac', 7, [1, 3, 5]),
        ('successful destroy three out of seven versions written 137', 'hvac', 7, [1, 3, 7]),
        ('invalid versions arg None', 'boom', 0, None, exceptions.ParamValidationError),
        ('invalid versions arg empty', 'boom', 0, [], exceptions.ParamValidationError),
        ('invalid versions arg not a list', 'goes', 0, '1', exceptions.ParamValidationError),
        ('nonexistent version 1', 'no-version-here', 3, [5]),
        ('nonexistent version 2', 'no-versions-here', 3, [7, 9]),
        ('nonexistent version 3', 'no-versions-here', 3, [7, 12]),
    ])
    def test_destroy_secret_versions(self, test_label, path, write_secret_before_test=1, destoryed_versions=None, raises=None, exception_message=''):

        if write_secret_before_test:
            logging.error(write_secret_before_test)
            for num in range(1, write_secret_before_test + 1):
                test_secret = {
                    'pssst': num,
                }
                self.client.secrets.kv.v2.create_or_update_secret(
                    path=path,
                    secret=test_secret,
                    mount_point=self.DEFAULT_MOUNT_POINT
                )
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.secrets.kv.v2.destroy_secret_versions(
                    path=path,
                    versions=destoryed_versions,
                    mount_point=self.DEFAULT_MOUNT_POINT,
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            destroy_secret_versions_result = self.client.secrets.kv.v2.destroy_secret_versions(
                path=path,
                versions=destoryed_versions,
                mount_point=self.DEFAULT_MOUNT_POINT,
            )
            logging.debug('destroy_secret_versions_result: %s' % destroy_secret_versions_result)
            read_secret_metadata_result = self.client.secrets.kv.v2.read_secret_metadata(
                path=path,
                mount_point=self.DEFAULT_MOUNT_POINT,
            )
            logging.debug('read_secret_metadata_result: %s' % read_secret_metadata_result)
            for destoryed_version in destoryed_versions:
                if str(destoryed_version) in read_secret_metadata_result['data']['versions']:
                    self.assertTrue(
                        expr=read_secret_metadata_result['data']['versions'][str(destoryed_version)]['destroyed'],
                        msg='Version "{num}" should be destoryed but is not. Full read metadata response versions: {metadata}'.format(
                            num=destoryed_version,
                            metadata=read_secret_metadata_result['data']['versions'],
                        )
                    )
            for nondestoryed_version in set(range(1, write_secret_before_test + 1)) - set(destoryed_versions):
                self.assertFalse(
                    expr=read_secret_metadata_result['data']['versions'][str(nondestoryed_version)]['destroyed'],
                    msg='Version "{num}" should not be destoryed but is. Full read metadata response versions: {metadata}'.format(
                        num=nondestoryed_version,
                        metadata=read_secret_metadata_result['data']['versions'],
                    )
                )

    @parameterized.expand([
        ('nonexistent secret', 'hvac/no-secret-here', False, exceptions.InvalidPath),
        ('list secret', 'hvac/top-secret'),
    ])
    def test_list_secrets(self, test_label, path, write_secret_before_test=True, raises=None, exception_message=''):
        test_secret = {
            'pssst': 'hi',
        }
        test_path_prefix, test_key = path.split('/')[:2]

        if write_secret_before_test:
            self.client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret=test_secret,
                mount_point=self.DEFAULT_MOUNT_POINT
            )
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.secrets.kv.v2.list_secrets(
                    path=test_path_prefix,
                    mount_point=self.DEFAULT_MOUNT_POINT
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            list_secrets_result = self.client.secrets.kv.v2.list_secrets(
                path=test_path_prefix,
                mount_point=self.DEFAULT_MOUNT_POINT
            )

            logging.debug('list_secrets_result: %s' % list_secrets_result)
            self.assertEqual(
                first=dict(keys=[test_key]),
                second=list_secrets_result['data'],
            )

    @parameterized.expand([
        ('update with no params', 'hvac'),
        ('update max versions 7', 'hvac', 7),
        ('update max versions 0', 'hvac', 0),
        ('update cas_required true', 'hvac', None, True),
        ('update cas_required false', 'hvac', None, False),
        ('update with invalid cas_required param', 'hvac', None, 'cats', True, exceptions.ParamValidationError, 'bool expected for cas_required param'),
    ])
    def test_update_metadata(self, test_label, path, max_versions=None, cas_required=None, write_secret_before_test=True, raises=None, exception_message=''):
        if write_secret_before_test:
            test_secret = {
                'pssst': 'hi itsame hvac',
            }
            self.client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret=test_secret,
                mount_point=self.DEFAULT_MOUNT_POINT
            )
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.secrets.kv.v2.update_metadata(
                    path=path,
                    max_versions=max_versions,
                    cas_required=cas_required,
                    mount_point=self.DEFAULT_MOUNT_POINT,
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            update_metadata_result = self.client.secrets.kv.v2.update_metadata(
                path=path,
                max_versions=max_versions,
                cas_required=cas_required,
                mount_point=self.DEFAULT_MOUNT_POINT,
            )
            logging.debug('update_metadata_result: %s' % update_metadata_result)
            read_secret_metadata_result = self.client.secrets.kv.v2.read_secret_metadata(
                path=path,
                mount_point=self.DEFAULT_MOUNT_POINT,
            )
            logging.debug('read_secret_metadata_result: %s' % read_secret_metadata_result)
            for key, argument in dict(max_versions=max_versions, cas_required=cas_required).items():
                if argument is not None:
                    self.assertEqual(
                        first=argument,
                        second=read_secret_metadata_result['data'][key],
                    )

    @parameterized.expand([
        ('nonexistent secret', 'hvac/no-secret-here', False),
        ('delete extant secret metadata', 'hvac/top-secret'),
    ])
    def test_delete_metadata_and_all_versions(self, test_label, path, write_secret_before_test=True):
        test_secret = {
            'pssst': 'hi',
        }

        if write_secret_before_test:
            self.client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret=test_secret,
                mount_point=self.DEFAULT_MOUNT_POINT
            )
        delete_metadata_and_all_versions_result = self.client.secrets.kv.v2.delete_metadata_and_all_versions(
            path=path,
            mount_point=self.DEFAULT_MOUNT_POINT
        )
        logging.debug('delete_metadata_and_all_versions_result: %s' % delete_metadata_and_all_versions_result)
        with self.assertRaises(exceptions.InvalidPath):
            read_secret_metadata_result = self.client.secrets.kv.v2.read_secret_metadata(
                path=path,
                mount_point=self.DEFAULT_MOUNT_POINT,
            )
            logging.debug('read_secret_metadata_result: %s' % read_secret_metadata_result)
