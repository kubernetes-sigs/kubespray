
from __future__ import absolute_import
import os.path
import subprocess
import tempfile
import unittest2

import mock

import ansible_mitogen.target
import testlib


LOGGER_NAME = ansible_mitogen.target.LOG.name


class NamedTemporaryDirectory(object):
    def __enter__(self):
        self.path = tempfile.mkdtemp()
        return self.path

    def __exit__(self, _1, _2, _3):
        subprocess.check_call(['rm', '-rf', self.path])


class ApplyModeSpecTest(unittest2.TestCase):
    func = staticmethod(ansible_mitogen.target.apply_mode_spec)

    def test_simple(self):
        spec = 'u+rwx,go=x'
        self.assertEquals(int('0711', 8), self.func(spec, 0))

        spec = 'g-rw'
        self.assertEquals(int('0717', 8), self.func(spec, int('0777', 8)))


class IsGoodTempDirTest(unittest2.TestCase):
    func = staticmethod(ansible_mitogen.target.is_good_temp_dir)

    def test_creates(self):
        with NamedTemporaryDirectory() as temp_path:
            bleh = os.path.join(temp_path, 'bleh')
            self.assertFalse(os.path.exists(bleh))
            self.assertTrue(self.func(bleh))
            self.assertTrue(os.path.exists(bleh))

    def test_file_exists(self):
        with NamedTemporaryDirectory() as temp_path:
            bleh = os.path.join(temp_path, 'bleh')
            with open(bleh, 'w') as fp:
                fp.write('derp')
            self.assertTrue(os.path.isfile(bleh))
            self.assertFalse(self.func(bleh))
            self.assertEquals(open(bleh).read(), 'derp')

    def test_unwriteable(self):
        with NamedTemporaryDirectory() as temp_path:
            os.chmod(temp_path, 0)
            self.assertFalse(self.func(temp_path))
            os.chmod(temp_path, int('0700', 8))

    @mock.patch('os.chmod')
    def test_weird_filesystem(self, os_chmod):
        os_chmod.side_effect = OSError('nope')
        with NamedTemporaryDirectory() as temp_path:
            self.assertFalse(self.func(temp_path))

    @mock.patch('os.access')
    def test_noexec(self, os_access):
        os_access.return_value = False
        with NamedTemporaryDirectory() as temp_path:
            self.assertFalse(self.func(temp_path))



if __name__ == '__main__':
    unittest2.main()
