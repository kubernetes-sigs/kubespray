import os

import mitogen

import unittest2

import testlib


class ConstructorTest(testlib.RouterMixin, unittest2.TestCase):
    def test_okay(self):
        docker_path = testlib.data_path('stubs/docker.py')
        context = self.router.docker(
            container='container_name',
            docker_path=docker_path,
        )
        stream = self.router.stream_by_id(context.context_id)

        argv = eval(context.call(os.getenv, 'ORIGINAL_ARGV'))
        self.assertEquals(argv[0], docker_path)
        self.assertEquals(argv[1], 'exec')
        self.assertEquals(argv[2], '--interactive')
        self.assertEquals(argv[3], 'container_name')
        self.assertEquals(argv[4], stream.python_path)


if __name__ == '__main__':
    unittest2.main()
