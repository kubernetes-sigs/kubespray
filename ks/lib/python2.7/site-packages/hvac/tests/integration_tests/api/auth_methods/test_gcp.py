import json
import logging
from unittest import TestCase

from parameterized import parameterized, param

from hvac import exceptions
from hvac.tests import utils


class TestGcp(utils.HvacIntegrationTestCase, TestCase):
    TEST_MOUNT_POINT = 'gcp-test'

    def setUp(self):
        super(TestGcp, self).setUp()
        if '%s/' % self.TEST_MOUNT_POINT not in self.client.list_auth_backends():
            self.client.enable_auth_backend(
                backend_type='gcp',
                mount_point=self.TEST_MOUNT_POINT,
            )

    def tearDown(self):
        super(TestGcp, self).tearDown()
        self.client.disable_auth_backend(
            mount_point=self.TEST_MOUNT_POINT,
        )

    @parameterized.expand([
        param(
            'success',
        ),
        param(
            'set valid credentials',
            credentials=utils.load_test_data('example.jwt.json'),
        ),
        param(
            'set invalid credentials',
            credentials='some invalid JWT',
            raises=exceptions.InvalidRequest,
            exception_message='error reading google credentials from given JSON'
        ),
    ])
    def test_configure(self, label, credentials='', raises=None, exception_message=''):
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.auth.gcp.configure(
                    credentials=credentials,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            configure_response = self.client.auth.gcp.configure(
                credentials=credentials,
                mount_point=self.TEST_MOUNT_POINT,
            )
            logging.debug('configure_response: %s' % configure_response)
            self.assertEqual(
                first=configure_response.status_code,
                second=204,
            )

    @parameterized.expand([
        param(
            'success',
        ),
        param(
            'no config written yet',
            write_config_first=False,
            raises=exceptions.InvalidPath
        )
    ])
    def test_read_config(self, label, write_config_first=True, raises=None):

        credentials = utils.load_test_data('example.jwt.json')
        if write_config_first:
            self.client.auth.gcp.configure(
                credentials=credentials,
                mount_point=self.TEST_MOUNT_POINT,
            )
        if raises is not None:
            with self.assertRaises(raises):
                self.client.auth.gcp.read_config(
                    mount_point=self.TEST_MOUNT_POINT,
                )
        else:
            read_config_response = self.client.auth.gcp.read_config(
                mount_point=self.TEST_MOUNT_POINT,
            )
            logging.debug('read_config_response: %s' % read_config_response)

            creds_dict = json.loads(credentials)
            expected_config = {
                'project_id': creds_dict['project_id'],
                'client_email': creds_dict['client_email'],
                'private_key_id': creds_dict['private_key_id'],
            }
            for k, v in expected_config.items():
                self.assertEqual(
                    first=v,
                    second=read_config_response[k],
                )

    @parameterized.expand([
        # param(
        #     'success',  # TODO: figure out why this is returning a 405
        # ),
        param(
            'no existing config',
            write_config_first=False,
            raises=exceptions.UnexpectedError,
        ),
    ])
    def test_delete_config(self, label, write_config_first=True, raises=None):

        if write_config_first:
            self.client.auth.gcp.configure(
                mount_point=self.TEST_MOUNT_POINT,
            )
        if raises is not None:
            with self.assertRaises(raises):
                self.client.auth.gcp.delete_config(
                    mount_point=self.TEST_MOUNT_POINT,
                )
        else:
            delete_config_response = self.client.auth.gcp.delete_config(
                mount_point=self.TEST_MOUNT_POINT,
            )
            logging.debug('delete_config_response: %s' % delete_config_response)
            self.assertEqual(
                first=delete_config_response.status_code,
                second=204,
            )

    @parameterized.expand([
        param(
            'success iam',
            role_type='iam',
            extra_params=dict(
                bound_service_accounts=['*'],
            )
        ),
        param(
            'iam no bound service account',
            role_type='iam',
            raises=exceptions.InvalidRequest,
            exception_message='IAM role type must have at least one service account',
        ),
        param(
            'success gce',
            role_type='gce',
        ),
        param(
            'invalid role type',
            role_type='hvac',
            raises=exceptions.ParamValidationError,
            exception_message='unsupported role_type argument provided',
        ),
        param(
            'wrong policy arg type',
            role_type='iam',
            policies='cats',
            raises=exceptions.ParamValidationError,
            exception_message='unsupported policies argument provided',
        )
    ])
    def test_create_role(self, label, role_type, policies=None, extra_params=None, raises=None, exception_message=''):
        role_name = 'hvac'
        project_id = 'test-hvac-project-not-a-real-project'
        if extra_params is None:
            extra_params = {}
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.auth.gcp.create_role(
                    name=role_name,
                    role_type=role_type,
                    project_id=project_id,
                    policies=policies,
                    mount_point=self.TEST_MOUNT_POINT,
                    **extra_params
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            create_role_response = self.client.auth.gcp.create_role(
                name=role_name,
                role_type=role_type,
                project_id=project_id,
                policies=policies,
                mount_point=self.TEST_MOUNT_POINT,
                **extra_params
            )
            logging.debug('create_role_response: %s' % create_role_response)
            if utils.skip_if_vault_version_lt('0.10.0'):
                expected_status_code = 204
            else:
                expected_status_code = 200  # TODO => figure out why this isn't a 204?
            self.assertEqual(
                first=create_role_response.status_code,
                second=expected_status_code,
            )

    @parameterized.expand([
        param(
            'success add',
            add=['test'],
        ),
        param(
            'success remove',
            remove=['test'],
        ),
        param(
            'fail upon no changes',
            raises=exceptions.InvalidRequest,
            exception_message='must provide at least one value to add or remove',
        ),
        # TODO: wrong role type (gce)
    ])
    def test_edit_service_accounts_on_iam_role(self, label, add=None, remove=None, create_role_first=True, raises=None, exception_message=''):
        role_name = 'hvac'
        project_id = 'test-hvac-project-not-a-real-project'
        if create_role_first:
            self.client.auth.gcp.create_role(
                name=role_name,
                role_type='iam',
                project_id=project_id,
                bound_service_accounts=['hvac-integration-test@appspot.gserviceaccount.com'],
                mount_point=self.TEST_MOUNT_POINT,
            )
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.auth.gcp.edit_service_accounts_on_iam_role(
                    name=role_name,
                    add=add,
                    remove=remove,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            edit_sa_on_iam_response = self.client.auth.gcp.edit_service_accounts_on_iam_role(
                name=role_name,
                add=add,
                remove=remove,
                mount_point=self.TEST_MOUNT_POINT,
            )
            logging.debug('create_role_response: %s' % edit_sa_on_iam_response)
            if utils.skip_if_vault_version_lt('0.10.0'):
                expected_status_code = 204
            else:
                expected_status_code = 200  # TODO => figure out why this isn't a 204?
            self.assertEqual(
                first=edit_sa_on_iam_response.status_code,
                second=expected_status_code,
            )

    @parameterized.expand([
        param(
            'success add',
            add=['test-key:test-value'],
        ),
        param(
            'success remove',
            remove=['test-key:test-value'],
        ),
        param(
            'fail upon no changes',
            raises=exceptions.InvalidRequest,
            exception_message='must provide at least one value to add or remove',
        ),
        # TODO: wrong role type (iam)
    ])
    def test_edit_labels_on_gce_role(self, label, add=None, remove=None, create_role_first=True, raises=None, exception_message=''):
        role_name = 'hvac'
        project_id = 'test-hvac-project-not-a-real-project'
        if create_role_first:
            self.client.auth.gcp.create_role(
                name=role_name,
                role_type='gce',
                project_id=project_id,
                bound_service_accounts=['hvac-integration-test@appspot.gserviceaccount.com'],
                mount_point=self.TEST_MOUNT_POINT,
            )
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.auth.gcp.edit_labels_on_gce_role(
                    name=role_name,
                    add=add,
                    remove=remove,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            edit_labled_response = self.client.auth.gcp.edit_labels_on_gce_role(
                name=role_name,
                add=add,
                remove=remove,
                mount_point=self.TEST_MOUNT_POINT,
            )
            logging.debug('create_role_response: %s' % edit_labled_response)
            if utils.skip_if_vault_version_lt('0.10.0'):
                expected_status_code = 204
            else:
                expected_status_code = 200  # TODO => figure out why this isn't a 204?
            self.assertEqual(
                first=edit_labled_response.status_code,
                second=expected_status_code,
            )

    @parameterized.expand([
        param(
            'success',
        ),
        param(
            'nonexistent role',
            create_role_first=False,
            raises=exceptions.InvalidPath,
        ),
    ])
    def test_read_role(self, label, create_role_first=True, raises=None, exception_message=''):
        role_name = 'hvac'
        project_id = 'test-hvac-project-not-a-real-project'
        if create_role_first:
            self.client.auth.gcp.create_role(
                name=role_name,
                role_type='gce',
                project_id=project_id,
                bound_service_accounts=['hvac-integration-test@appspot.gserviceaccount.com'],
                mount_point=self.TEST_MOUNT_POINT,
            )
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.auth.gcp.read_role(
                    name=role_name,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            read_role_response = self.client.auth.gcp.read_role(
                name=role_name,
                mount_point=self.TEST_MOUNT_POINT,
            )
            logging.debug('create_role_response: %s' % read_role_response)
            self.assertEqual(
                first=project_id,
                second=read_role_response['project_id'],
            )

    @parameterized.expand([
        param(
            'success one role',
        ),
        param(
            'success multiple roles',
            num_roles_to_create=7,
        ),
        param(
            'no roles',
            num_roles_to_create=0,
            raises=exceptions.InvalidPath,
        ),
    ])
    def test_list_roles(self, label, num_roles_to_create=1, raises=None):
        project_id = 'test-hvac-project-not-a-real-project'
        roles_to_create = ['hvac%s' % n for n in range(0, num_roles_to_create)]
        logging.debug('roles_to_create: %s' % roles_to_create)
        for role_to_create in roles_to_create:
            create_role_response = self.client.auth.gcp.create_role(
                name=role_to_create,
                role_type='gce',
                project_id=project_id,
                bound_service_accounts=['hvac-integration-test@appspot.gserviceaccount.com'],
                mount_point=self.TEST_MOUNT_POINT,
            )
            logging.debug('create_role_response: %s' % create_role_response)

        if raises is not None:
            with self.assertRaises(raises):
                self.client.auth.gcp.list_roles(
                    mount_point=self.TEST_MOUNT_POINT,
                )
        else:
            list_roles_response = self.client.auth.gcp.list_roles(
                mount_point=self.TEST_MOUNT_POINT,
            )
            logging.debug('list_roles_response: %s' % list_roles_response)
            self.assertEqual(
                first=list_roles_response['keys'],
                second=roles_to_create,
            )

    @parameterized.expand([
        param(
            'success',
        ),
        param(
            'nonexistent role name',
            configure_role_first=False,
        ),
    ])
    def test_delete_role(self, label, configure_role_first=True, raises=None):
        role_name = 'hvac'
        project_id = 'test-hvac-project-not-a-real-project'
        if configure_role_first:
            create_role_response = self.client.auth.gcp.create_role(
                name=role_name,
                role_type='gce',
                project_id=project_id,
                bound_service_accounts=['hvac-integration-test@appspot.gserviceaccount.com'],
                mount_point=self.TEST_MOUNT_POINT,
            )
            logging.debug('create_role_response: %s' % create_role_response)

        if raises is not None:
            with self.assertRaises(raises):
                self.client.auth.gcp.delete_role(
                    role=role_name,
                    mount_point=self.TEST_MOUNT_POINT,
                )
        else:
            delete_role_response = self.client.auth.gcp.delete_role(
                role=role_name,
                mount_point=self.TEST_MOUNT_POINT,
            )
            logging.debug('delete_role_response: %s' % delete_role_response)
            self.assertEqual(
                first=delete_role_response.status_code,
                second=204,
            )
