
import os
import socket
import sys
import time

import unittest2

import mitogen
import mitogen.fork
import mitogen.master
import mitogen.service
import mitogen.unix

import testlib


class MyService(mitogen.service.Service):
    def __init__(self, latch, **kwargs):
        super(MyService, self).__init__(**kwargs)
        # used to wake up main thread once client has made its request
        self.latch = latch

    @mitogen.service.expose(policy=mitogen.service.AllowParents())
    def ping(self, msg):
        self.latch.put(None)
        return {
            'src_id': msg.src_id,
            'auth_id': msg.auth_id,
        }


class IsPathDeadTest(unittest2.TestCase):
    func = staticmethod(mitogen.unix.is_path_dead)
    path = '/tmp/stale-socket'

    def test_does_not_exist(self):
        self.assertTrue(self.func('/tmp/does-not-exist'))

    def make_socket(self):
        if os.path.exists(self.path):
            os.unlink(self.path)
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.bind(self.path)
        return s

    def test_conn_refused(self):
        s = self.make_socket()
        s.close()
        self.assertTrue(self.func(self.path))

    def test_is_alive(self):
        s = self.make_socket()
        s.listen(5)
        self.assertFalse(self.func(self.path))
        s.close()
        os.unlink(self.path)


class ListenerTest(testlib.RouterMixin, unittest2.TestCase):
    klass = mitogen.unix.Listener

    def test_constructor_basic(self):
        listener = self.klass(router=self.router)
        self.assertFalse(mitogen.unix.is_path_dead(listener.path))
        os.unlink(listener.path)


class ClientTest(unittest2.TestCase):
    klass = mitogen.unix.Listener

    def _try_connect(self, path):
        # give server a chance to setup listener
        for x in range(10):
            try:
                return mitogen.unix.connect(path)
            except socket.error:
                if x == 9:
                    raise
                time.sleep(0.1)

    def _test_simple_client(self, path):
        router, context = self._try_connect(path)
        self.assertEquals(0, context.context_id)
        self.assertEquals(1, mitogen.context_id)
        self.assertEquals(0, mitogen.parent_id)
        resp = context.call_service(service_name=MyService, method_name='ping')
        self.assertEquals(mitogen.context_id, resp['src_id'])
        self.assertEquals(0, resp['auth_id'])

    def _test_simple_server(self, path):
        router = mitogen.master.Router()
        latch = mitogen.core.Latch()
        try:
            try:
                listener = self.klass(path=path, router=router)
                pool = mitogen.service.Pool(router=router, services=[
                    MyService(latch=latch, router=router),
                ])
                latch.get()
                # give broker a chance to deliver service resopnse
                time.sleep(0.1)
            finally:
                pool.shutdown()
                router.broker.shutdown()
        finally:
            os._exit(0)

    def test_simple(self):
        path = mitogen.unix.make_socket_path()
        if os.fork():
            self._test_simple_client(path)
        else:
            mitogen.fork.on_fork()
            self._test_simple_server(path)


if __name__ == '__main__':
    unittest2.main()
