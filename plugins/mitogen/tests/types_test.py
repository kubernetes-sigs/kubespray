
try:
    from io import StringIO
    from io import BytesIO
except ImportError:
    from StringIO import StringIO as StringIO
    from StringIO import StringIO as BytesIO

import unittest2

import mitogen.core
from mitogen.core import b


class BlobTest(unittest2.TestCase):
    klass = mitogen.core.Blob

    def make(self):
        return self.klass(b('x') * 128)

    def test_repr(self):
        blob = self.make()
        self.assertEquals('[blob: 128 bytes]', repr(blob))

    def test_decays_on_constructor(self):
        blob = self.make()
        self.assertEquals(b('x')*128, mitogen.core.BytesType(blob))

    def test_decays_on_write(self):
        blob = self.make()
        io = BytesIO()
        io.write(blob)
        self.assertEquals(128, io.tell())
        self.assertEquals(b('x')*128, io.getvalue())

    def test_message_roundtrip(self):
        blob = self.make()
        msg = mitogen.core.Message.pickled(blob)
        blob2 = msg.unpickle()
        self.assertEquals(type(blob), type(blob2))
        self.assertEquals(repr(blob), repr(blob2))
        self.assertEquals(mitogen.core.BytesType(blob),
                          mitogen.core.BytesType(blob2))


class SecretTest(unittest2.TestCase):
    klass = mitogen.core.Secret

    def make(self):
        return self.klass('password')

    def test_repr(self):
        secret = self.make()
        self.assertEquals('[secret]', repr(secret))

    def test_decays_on_constructor(self):
        secret = self.make()
        self.assertEquals('password', mitogen.core.UnicodeType(secret))

    def test_decays_on_write(self):
        secret = self.make()
        io = StringIO()
        io.write(secret)
        self.assertEquals(8, io.tell())
        self.assertEquals('password', io.getvalue())

    def test_message_roundtrip(self):
        secret = self.make()
        msg = mitogen.core.Message.pickled(secret)
        secret2 = msg.unpickle()
        self.assertEquals(type(secret), type(secret2))
        self.assertEquals(repr(secret), repr(secret2))
        self.assertEquals(mitogen.core.b(secret),
                          mitogen.core.b(secret2))


if __name__ == '__main__':
    unittest2.main()
