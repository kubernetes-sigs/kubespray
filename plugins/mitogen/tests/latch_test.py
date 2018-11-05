
import sys
import threading

import unittest2

import mitogen.core

import testlib


class EmptyTest(testlib.TestCase):
    klass = mitogen.core.Latch

    def test_is_empty(self):
        latch = self.klass()
        self.assertTrue(latch.empty())

    def test_is_nonempty(self):
        latch = self.klass()
        latch.put(None)
        self.assertTrue(not latch.empty())


class GetTest(testlib.TestCase):
    klass = mitogen.core.Latch
    # TODO: test multiple waiters.

    def test_empty_noblock(self):
        latch = self.klass()
        exc = self.assertRaises(mitogen.core.TimeoutError,
            lambda: latch.get(block=False))

    def test_empty_zero_timeout(self):
        latch = self.klass()
        exc = self.assertRaises(mitogen.core.TimeoutError,
            lambda: latch.get(timeout=0))

    def test_nonempty(self):
        obj = object()
        latch = self.klass()
        latch.put(obj)
        self.assertEquals(obj, latch.get())

    def test_nonempty_noblock(self):
        obj = object()
        latch = self.klass()
        latch.put(obj)
        self.assertEquals(obj, latch.get(block=False))

    def test_nonempty_zero_timeout(self):
        obj = object()
        latch = self.klass()
        latch.put(obj)
        self.assertEquals(obj, latch.get(timeout=0))


class ThreadedGetTest(testlib.TestCase):
    klass = mitogen.core.Latch

    def setUp(self):
        super(ThreadedGetTest, self).setUp()
        self.results = []
        self.excs = []
        self.threads = []

    def _worker(self, func):
        try:
            self.results.append(func())
        except Exception:
            e = sys.exc_info()[1]
            self.results.append(None)
            self.excs.append(e)

    def start_one(self, func):
        thread = threading.Thread(target=self._worker, args=(func,))
        thread.start()
        self.threads.append(thread)

    def join(self):
        for th in self.threads:
            th.join(3.0)

    def test_one_thread(self):
        latch = self.klass()
        self.start_one(lambda: latch.get(timeout=3.0))
        latch.put('test')
        self.join()
        self.assertEquals(self.results, ['test'])
        self.assertEquals(self.excs, [])

    def test_five_threads(self):
        latch = self.klass()
        for x in range(5):
            self.start_one(lambda: latch.get(timeout=3.0))
        for x in range(5):
            latch.put(x)
        self.join()
        self.assertEquals(sorted(self.results), list(range(5)))
        self.assertEquals(self.excs, [])



class PutTest(testlib.TestCase):
    klass = mitogen.core.Latch

    def test_put(self):
        latch = self.klass()
        latch.put(None)
        self.assertEquals(None, latch.get())


class CloseTest(testlib.TestCase):
    klass = mitogen.core.Latch

    def test_empty_noblock(self):
        latch = self.klass()
        latch.close()
        self.assertRaises(mitogen.core.LatchError,
            lambda: latch.get(block=False))

    def test_empty_zero_timeout(self):
        latch = self.klass()
        latch.close()
        self.assertRaises(mitogen.core.LatchError,
            lambda: latch.get(timeout=0))

    def test_nonempty(self):
        obj = object()
        latch = self.klass()
        latch.put(obj)
        latch.close()
        self.assertRaises(mitogen.core.LatchError,
            lambda: latch.get())

    def test_nonempty_noblock(self):
        obj = object()
        latch = self.klass()
        latch.put(obj)
        latch.close()
        self.assertRaises(mitogen.core.LatchError,
            lambda: latch.get(block=False))

    def test_nonempty_zero_timeout(self):
        obj = object()
        latch = self.klass()
        latch.put(obj)
        latch.close()
        self.assertRaises(mitogen.core.LatchError,
            lambda: latch.get(timeout=0))

    def test_put(self):
        latch = self.klass()
        latch.close()
        self.assertRaises(mitogen.core.LatchError,
            lambda: latch.put(None))

    def test_double_close(self):
        latch = self.klass()
        latch.close()
        latch.close()


class ThreadedCloseTest(testlib.TestCase):
    klass = mitogen.core.Latch

    def setUp(self):
        super(ThreadedCloseTest, self).setUp()
        self.results = []
        self.excs = []
        self.threads = []

    def _worker(self, func):
        try:
            self.results.append(func())
        except Exception:
            e = sys.exc_info()[1]
            self.results.append(None)
            self.excs.append(e)

    def start_one(self, func):
        thread = threading.Thread(target=self._worker, args=(func,))
        thread.start()
        self.threads.append(thread)

    def join(self):
        for th in self.threads:
            th.join(3.0)

    def test_one_thread(self):
        latch = self.klass()
        self.start_one(lambda: latch.get(timeout=3.0))
        latch.close()
        self.join()
        self.assertEquals(self.results, [None])
        for exc in self.excs:
            self.assertTrue(isinstance(exc, mitogen.core.LatchError))

    def test_five_threads(self):
        latch = self.klass()
        for x in range(5):
            self.start_one(lambda: latch.get(timeout=3.0))
        latch.close()
        self.join()
        self.assertEquals(self.results, [None]*5)
        for exc in self.excs:
            self.assertTrue(isinstance(exc, mitogen.core.LatchError))



if __name__ == '__main__':
    unittest2.main()
