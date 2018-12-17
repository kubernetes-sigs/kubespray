import logging
from unittest import TestCase
from unittest import skipIf

from parameterized import parameterized, param

from hvac import exceptions
from hvac.tests import utils


class TestTransit(utils.HvacIntegrationTestCase, TestCase):
    TEST_MOUNT_POINT = 'transit-integration-test'

    def setUp(self):
        super(TestTransit, self).setUp()
        self.client.enable_secret_backend(
            backend_type='transit',
            mount_point=self.TEST_MOUNT_POINT,
        )

    def tearDown(self):
        self.client.disable_secret_backend(mount_point=self.TEST_MOUNT_POINT)
        super(TestTransit, self).tearDown()

    @parameterized.expand([
        param(
            'success',
        ),
    ])
    def test_create_key(self, label, raises=False, exception_message=''):
        key_name = 'testkey'
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.secrets.transit.create_key(
                    name=key_name,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            create_key_response = self.client.secrets.transit.create_key(
                name=key_name,
                mount_point=self.TEST_MOUNT_POINT,
            )
            logging.debug('create_key_response: %s' % create_key_response)
            self.assertEqual(
                first=create_key_response.status_code,
                second=204,
            )

    @parameterized.expand([
        param(
            'success',
        ),
    ])
    def test_read_key(self, label, raises=False, exception_message=''):
        key_name = 'testkey'
        create_key_response = self.client.secrets.transit.create_key(
            name=key_name,
            mount_point=self.TEST_MOUNT_POINT,
        )
        logging.debug('create_key_response: %s' % create_key_response)
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.secrets.transit.read_key(
                    name=key_name,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            read_key_response = self.client.secrets.transit.read_key(
                name=key_name,
                mount_point=self.TEST_MOUNT_POINT,
            )
            logging.debug('read_key_response: %s' % read_key_response)
            self.assertEqual(
                first=read_key_response['data']['name'],
                second=key_name,
            )

    @parameterized.expand([
        param(
            'success',
        ),
    ])
    def test_list_keys(self, label, raises=False, exception_message=''):
        key_name = 'testkey'
        create_key_response = self.client.secrets.transit.create_key(
            name=key_name,
            mount_point=self.TEST_MOUNT_POINT,
        )
        logging.debug('create_key_response: %s' % create_key_response)
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.secrets.transit.list_keys(
                    mount_point=self.TEST_MOUNT_POINT,
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            list_keys_response = self.client.secrets.transit.list_keys(
                mount_point=self.TEST_MOUNT_POINT,
            )
            logging.debug('list_keys_response: %s' % list_keys_response)
            self.assertEqual(
                first=list_keys_response['data']['keys'],
                second=[key_name],
            )

    @parameterized.expand([
        param(
            'success',
        ),
    ])
    def test_delete_key(self, label, raises=False, exception_message=''):
        key_name = 'testkey'
        create_key_response = self.client.secrets.transit.create_key(
            name=key_name,
            mount_point=self.TEST_MOUNT_POINT,
        )
        logging.debug('create_key_response: %s' % create_key_response)
        update_key_configuration_response = self.client.secrets.transit.update_key_configuration(
            name=key_name,
            deletion_allowed=True,
            mount_point=self.TEST_MOUNT_POINT,
        )
        logging.debug('update_key_configuration_response: %s' % update_key_configuration_response)
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.secrets.transit.delete_key(
                    name=key_name,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            delete_key_response = self.client.secrets.transit.delete_key(
                name=key_name,
                mount_point=self.TEST_MOUNT_POINT,
            )
            logging.debug('delete_key_response: %s' % delete_key_response)
            self.assertEqual(
                first=delete_key_response.status_code,
                second=204,
            )

    @parameterized.expand([
        param(
            'success',
        ),
    ])
    def test_rotate_key(self, label, raises=False, exception_message=''):
        key_name = 'testkey'
        create_key_response = self.client.secrets.transit.create_key(
            name=key_name,
            mount_point=self.TEST_MOUNT_POINT,
        )
        logging.debug('create_key_response: %s' % create_key_response)
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.secrets.transit.rotate_key(
                    name=key_name,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            rotate_key_response = self.client.secrets.transit.rotate_key(
                name=key_name,
                mount_point=self.TEST_MOUNT_POINT,
            )
            logging.debug('rotate_key_response: %s' % rotate_key_response)
            self.assertEqual(
                first=rotate_key_response.status_code,
                second=204,
            )

    @parameterized.expand([
        param(
            'success',
        ),
        param(
            'invalid key type',
            key_type='kitty-cat-key',
            raises=exceptions.ParamValidationError,
            exception_message='invalid key_type argument provided',
        ),
    ])
    def test_export_key(self, label, key_type='hmac-key', raises=False, exception_message=''):
        key_name = 'testkey'
        create_key_response = self.client.secrets.transit.create_key(
            name=key_name,
            exportable=True,
            mount_point=self.TEST_MOUNT_POINT,
        )
        logging.debug('create_key_response: %s' % create_key_response)
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.secrets.transit.export_key(
                    name=key_name,
                    key_type=key_type,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            export_key_response = self.client.secrets.transit.export_key(
                name=key_name,
                key_type=key_type,
                mount_point=self.TEST_MOUNT_POINT,
            )
            logging.debug('export_key_response: %s' % export_key_response)
            self.assertEqual(
                first=len(export_key_response['data']['keys']),
                second=1,
            )
            self.assertEqual(
                first=export_key_response['data']['name'],
                second=key_name,
            )

    @parameterized.expand([
        param(
            'success',
        ),
    ])
    def test_encrypt_data(self, label, plaintext='hi itsame hvac', raises=False, exception_message=''):
        key_name = 'testkey'
        plaintext = utils.base64ify(plaintext)
        create_key_response = self.client.secrets.transit.create_key(
            name=key_name,
            mount_point=self.TEST_MOUNT_POINT,
        )
        logging.debug('create_key_response: %s' % create_key_response)
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.secrets.transit.encrypt_data(
                    name=key_name,
                    plaintext=plaintext,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            encrypt_data_response = self.client.secrets.transit.encrypt_data(
                name=key_name,
                plaintext=plaintext,
                mount_point=self.TEST_MOUNT_POINT,
            )
            logging.debug('encrypt_data_response: %s' % encrypt_data_response)
            self.assertIn(
                member='ciphertext',
                container=encrypt_data_response['data'],
            )

    @parameterized.expand([
        param(
            'success',
        ),
    ])
    def test_decrypt_data(self, label, plaintext='hi itsame hvac', raises=False, exception_message=''):
        key_name = 'testkey'
        plaintext = utils.base64ify(plaintext)
        create_key_response = self.client.secrets.transit.create_key(
            name=key_name,
            mount_point=self.TEST_MOUNT_POINT,
        )
        logging.debug('create_key_response: %s' % create_key_response)
        encrypt_data_response = self.client.secrets.transit.encrypt_data(
            name=key_name,
            plaintext=plaintext,
            mount_point=self.TEST_MOUNT_POINT,
        )
        logging.debug('encrypt_data_response: %s' % encrypt_data_response)
        ciphertext = encrypt_data_response['data']['ciphertext']
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.secrets.transit.decrypt_data(
                    name=key_name,
                    ciphertext=ciphertext,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            decrypt_data_response = self.client.secrets.transit.decrypt_data(
                name=key_name,
                ciphertext=ciphertext,
                mount_point=self.TEST_MOUNT_POINT,
            )
            logging.debug('decrypt_data_response: %s' % decrypt_data_response)
            self.assertIn(
                member=plaintext,
                container=decrypt_data_response['data']['plaintext'],
            )

    @parameterized.expand([
        param(
            'success',
        ),
    ])
    def test_rewrap_data(self, label, plaintext='hi itsame hvac', raises=False, exception_message=''):
        key_name = 'testkey'
        plaintext = utils.base64ify(plaintext)
        create_key_response = self.client.secrets.transit.create_key(
            name=key_name,
            mount_point=self.TEST_MOUNT_POINT,
        )
        logging.debug('create_key_response: %s' % create_key_response)
        encrypt_data_response = self.client.secrets.transit.encrypt_data(
            name=key_name,
            plaintext=plaintext,
            mount_point=self.TEST_MOUNT_POINT,
        )
        logging.debug('encrypt_data_response: %s' % encrypt_data_response)
        ciphertext = encrypt_data_response['data']['ciphertext']
        rotate_key_response = self.client.secrets.transit.rotate_key(
            name=key_name,
            mount_point=self.TEST_MOUNT_POINT,
        )
        logging.debug('rotate_key_response: %s' % rotate_key_response)
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.secrets.transit.rewrap_data(
                    name=key_name,
                    ciphertext=ciphertext,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            rewrap_data_response = self.client.secrets.transit.rewrap_data(
                name=key_name,
                ciphertext=ciphertext,
                mount_point=self.TEST_MOUNT_POINT,
            )
            logging.debug('rewrap_data_response: %s' % rewrap_data_response)
            self.assertIn(
                member='ciphertext',
                container=rewrap_data_response['data'],
            )

    @parameterized.expand([
        param(
            'success',
        ),
        param(
            'invalid key type',
            key_type='kitty-cat-key',
            raises=exceptions.ParamValidationError,
            exception_message='invalid key_type argument provided',
        ),
    ])
    def test_generate_data_key(self, label, key_type='plaintext', raises=False, exception_message=''):
        key_name = 'testkey'
        create_key_response = self.client.secrets.transit.create_key(
            name=key_name,
            mount_point=self.TEST_MOUNT_POINT,
        )
        logging.debug('create_key_response: %s' % create_key_response)
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.secrets.transit.generate_data_key(
                    name=key_name,
                    key_type=key_type,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            gen_data_key_response = self.client.secrets.transit.generate_data_key(
                name=key_name,
                key_type=key_type,
                mount_point=self.TEST_MOUNT_POINT,
            )
            logging.debug('gen_data_key_response: %s' % gen_data_key_response)
            self.assertIn(
                member='ciphertext',
                container=gen_data_key_response['data'],
            )

    @parameterized.expand([
        param(
            'success',
        ),
    ])
    def test_generate_random_bytes(self, label, n_bytes=32, raises=False, exception_message=''):
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.secrets.transit.generate_random_bytes(
                    n_bytes=n_bytes,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            gen_bytes_response = self.client.secrets.transit.generate_random_bytes(
                n_bytes=n_bytes,
                mount_point=self.TEST_MOUNT_POINT,
            )
            logging.debug('gen_data_key_response: %s' % gen_bytes_response)
            self.assertIn(
                member='random_bytes',
                container=gen_bytes_response['data'],
            )

    @parameterized.expand([
        param(
            'success',
        ),
        param(
            'invalid algorithm',
            algorithm='meow2-256',
            raises=exceptions.ParamValidationError,
            exception_message='invalid algorithm argument provided',
        ),
        param(
            'invalid output_format',
            output_format='kitty64',
            raises=exceptions.ParamValidationError,
            exception_message='invalid output_format argument provided',
        ),
    ])
    def test_hash_data(self, label, hash_input='hash this ish', algorithm='sha2-256', output_format='hex', raises=False, exception_message=''):
        hash_input = utils.base64ify(hash_input)
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.secrets.transit.hash_data(
                    hash_input=hash_input,
                    algorithm=algorithm,
                    output_format=output_format,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            hash_data_response = self.client.secrets.transit.hash_data(
                hash_input=hash_input,
                algorithm=algorithm,
                output_format=output_format,
                mount_point=self.TEST_MOUNT_POINT,
            )
            logging.debug('hash_data_response: %s' % hash_data_response)
            self.assertIn(
                member='sum',
                container=hash_data_response['data'],
            )

    @parameterized.expand([
        param(
            'success',
        ),
        param(
            'invalid algorithm',
            algorithm='meow2-256',
            raises=exceptions.ParamValidationError,
            exception_message='invalid algorithm argument provided',
        ),
    ])
    def test_generate_hmac(self, label, hash_input='hash this ish', algorithm='sha2-256', raises=False, exception_message=''):
        hash_input = utils.base64ify(hash_input)
        key_name = 'testkey'
        create_key_response = self.client.secrets.transit.create_key(
            name=key_name,
            mount_point=self.TEST_MOUNT_POINT,
        )
        logging.debug('create_key_response: %s' % create_key_response)
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.secrets.transit.generate_hmac(
                    name=key_name,
                    hash_input=hash_input,
                    algorithm=algorithm,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            generate_hmac_response = self.client.secrets.transit.generate_hmac(
                name=key_name,
                hash_input=hash_input,
                algorithm=algorithm,
                mount_point=self.TEST_MOUNT_POINT,
            )
            logging.debug('generate_hmac_response: %s' % generate_hmac_response)
            self.assertIn(
                member='hmac',
                container=generate_hmac_response['data'],
            )

    @parameterized.expand([
        param(
            'success',
        ),
        param(
            'invalid algorithm',
            hash_algorithm='meow2-256',
            raises=exceptions.ParamValidationError,
            exception_message='invalid hash_algorithm argument provided',
        ),
        param(
            'invalid signature_algorithm',
            signature_algorithm='pre-shared kitty cats',
            raises=exceptions.ParamValidationError,
            exception_message='invalid signature_algorithm argument provided',
        ),
    ])
    def test_sign_data(self, label, hash_input='hash this ish', hash_algorithm='sha2-256', signature_algorithm='pss',
                       raises=False, exception_message=''):
        hash_input = utils.base64ify(hash_input)
        key_name = 'testkey'
        key_type = 'ed25519'
        create_key_response = self.client.secrets.transit.create_key(
            name=key_name,
            key_type=key_type,
            mount_point=self.TEST_MOUNT_POINT,
        )
        logging.debug('create_key_response: %s' % create_key_response)
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.secrets.transit.sign_data(
                    name=key_name,
                    hash_input=hash_input,
                    hash_algorithm=hash_algorithm,
                    signature_algorithm=signature_algorithm,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            sign_data_response = self.client.secrets.transit.sign_data(
                name=key_name,
                hash_input=hash_input,
                hash_algorithm=hash_algorithm,
                signature_algorithm=signature_algorithm,
                mount_point=self.TEST_MOUNT_POINT,
            )
            logging.debug('sign_data_response: %s' % sign_data_response)
            self.assertIn(
                member='signature',
                container=sign_data_response['data'],
            )

    @parameterized.expand([
        param(
            'success',
        ),
        param(
            'invalid algorithm',
            hash_algorithm='meow2-256',
            raises=exceptions.ParamValidationError,
            exception_message='invalid hash_algorithm argument provided',
        ),
        param(
            'invalid signature_algorithm',
            signature_algorithm='pre-shared kitty cats',
            raises=exceptions.ParamValidationError,
            exception_message='invalid signature_algorithm argument provided',
        ),
    ])
    def test_verify_signed_data(self, label, hash_input='hash this ish', hash_algorithm='sha2-256', signature_algorithm='pss',
                                raises=False, exception_message=''):
        hash_input = utils.base64ify(hash_input)
        key_name = 'testkey'
        key_type = 'ed25519'
        create_key_response = self.client.secrets.transit.create_key(
            name=key_name,
            key_type=key_type,
            mount_point=self.TEST_MOUNT_POINT,
        )
        logging.debug('create_key_response: %s' % create_key_response)
        sign_data_response = self.client.secrets.transit.sign_data(
            name=key_name,
            hash_input=hash_input,
            hash_algorithm='sha2-256',
            signature_algorithm='pss',
            mount_point=self.TEST_MOUNT_POINT,
        )
        logging.debug('sign_data_response: %s' % sign_data_response)
        signature = sign_data_response['data']['signature']
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.secrets.transit.verify_signed_data(
                    name=key_name,
                    hash_input=hash_input,
                    signature=signature,
                    hash_algorithm=hash_algorithm,
                    signature_algorithm=signature_algorithm,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            verify_signed_data_response = self.client.secrets.transit.verify_signed_data(
                name=key_name,
                hash_input=hash_input,
                signature=signature,
                hash_algorithm=hash_algorithm,
                signature_algorithm=signature_algorithm,
                mount_point=self.TEST_MOUNT_POINT,
            )
            logging.debug('verify_signed_data_response: %s' % verify_signed_data_response)
            self.assertTrue(
                expr=verify_signed_data_response['data']['valid'],
            )

    @parameterized.expand([
        param(
            'success',
        ),
        param(
            'allow_plaintext_backup false',
            allow_plaintext_backup=False,
            raises=exceptions.InternalServerError,
            exception_message='plaintext backup is disallowed on the policy',
        ),
    ])
    @skipIf(utils.skip_if_vault_version_lt('0.9.1'), "transit key export/restore added in Vault versions >=0.9.1")
    def test_backup_key(self, label, allow_plaintext_backup=True, raises=False, exception_message=''):
        key_name = 'testkey'
        create_key_response = self.client.secrets.transit.create_key(
            name=key_name,
            mount_point=self.TEST_MOUNT_POINT,
        )
        logging.debug('create_key_response: %s' % create_key_response)
        update_key_configuration_response = self.client.secrets.transit.update_key_configuration(
            name=key_name,
            exportable=True,
            allow_plaintext_backup=allow_plaintext_backup,
            mount_point=self.TEST_MOUNT_POINT,
        )
        logging.debug('update_key_configuration_response: %s' % update_key_configuration_response)
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.secrets.transit.backup_key(
                    name=key_name,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            backup_key_response = self.client.secrets.transit.backup_key(
                name=key_name,
                mount_point=self.TEST_MOUNT_POINT,
            )
            logging.debug('backup_key_response: %s' % backup_key_response)
            self.assertIn(
                member='backup',
                container=backup_key_response['data'],
            )

    @parameterized.expand([
        param(
            'success',
        ),
        param(
            'success with force',
            force=True,
        ),
        param(
            'existing key without force',
            name=None,
            raises=exceptions.InternalServerError,
            exception_message='already exists',
        ),
    ])
    @skipIf(utils.skip_if_vault_version_lt('0.9.1'), "transit key export/restore added in Vault versions >=0.9.1")
    def test_restore_key(self, label, name='new_test_ky', force=False, raises=False, exception_message=''):
        key_name = 'testkey'
        create_key_response = self.client.secrets.transit.create_key(
            name=key_name,
            mount_point=self.TEST_MOUNT_POINT,
        )
        logging.debug('create_key_response: %s' % create_key_response)
        update_key_configuration_response = self.client.secrets.transit.update_key_configuration(
            name=key_name,
            exportable=True,
            allow_plaintext_backup=True,
            mount_point=self.TEST_MOUNT_POINT,
        )
        logging.debug('update_key_configuration_response: %s' % update_key_configuration_response)
        backup_key_response = self.client.secrets.transit.backup_key(
            name=key_name,
            mount_point=self.TEST_MOUNT_POINT,
        )
        logging.debug('backup_key_response: %s' % backup_key_response)
        backup = backup_key_response['data']['backup']
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.secrets.transit.restore_key(
                    backup=backup,
                    name=name,
                    force=force,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            restore_key_response = self.client.secrets.transit.restore_key(
                backup=backup,
                name=name,
                force=force,
                mount_point=self.TEST_MOUNT_POINT,
            )
            logging.debug('restore_key_response: %s' % restore_key_response)
            self.assertEqual(
                first=restore_key_response.status_code,
                second=204,
            )

    @parameterized.expand([
        param(
            'success',
        ),
    ])
    @skipIf(utils.skip_if_vault_version_lt('0.11.4'), "transit key trimming added in Vault versions >=0.11.4")
    def test_trim_key(self, label, min_version=2, raises=False, exception_message=''):
        key_name = 'testkey'
        create_key_response = self.client.secrets.transit.create_key(
            name=key_name,
            mount_point=self.TEST_MOUNT_POINT,
        )
        logging.debug('create_key_response: %s' % create_key_response)
        for _ in range(0, 10):
            rotate_key_response = self.client.secrets.transit.rotate_key(
                name=key_name,
                mount_point=self.TEST_MOUNT_POINT,
            )
            logging.debug('rotate_key_response: %s' % rotate_key_response)

        update_key_configuration_response = self.client.secrets.transit.update_key_configuration(
            name=key_name,
            min_decryption_version=3,
            min_encryption_version=9,
            mount_point=self.TEST_MOUNT_POINT,
        )
        logging.debug('update_key_configuration_response: %s' % update_key_configuration_response)

        read_key_response = self.client.secrets.transit.read_key(
            name=key_name,
            mount_point=self.TEST_MOUNT_POINT,
        )
        logging.debug('read_key_response: %s' % read_key_response)
        if raises:
            with self.assertRaises(raises) as cm:
                self.client.secrets.transit.trim_key(
                    name=key_name,
                    min_version=min_version,
                    mount_point=self.TEST_MOUNT_POINT,
                )
            self.assertIn(
                member=exception_message,
                container=str(cm.exception),
            )
        else:
            trim_key_response = self.client.secrets.transit.trim_key(
                name=key_name,
                min_version=min_version,
                mount_point=self.TEST_MOUNT_POINT,
            )
            logging.debug('trim_key_response: %s' % trim_key_response)
            self.assertEqual(
                first=trim_key_response.status_code,
                second=204,
            )
