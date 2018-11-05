
try:
    from io import StringIO
    from io import BytesIO
except ImportError:
    from StringIO import StringIO as StringIO
    from StringIO import StringIO as BytesIO

import unittest2

import mitogen.core
from mitogen.core import b


def roundtrip(v):
    msg = mitogen.core.Message.pickled(v)
    return mitogen.core.Message(data=msg.data).unpickle()


class BlobTest(unittest2.TestCase):
    klass = mitogen.core.Blob

    # Python 3 pickle protocol 2 does weird stuff depending on whether an empty
    # or nonempty bytes is being serialized. For non-empty, it yields a
    # _codecs.encode() call. For empty, it yields a bytes() call.

    def test_nonempty_bytes(self):
        v = mitogen.core.Blob(b('dave'))
        self.assertEquals(b('dave'), roundtrip(v))

    def test_empty_bytes(self):
        v = mitogen.core.Blob(b(''))
        self.assertEquals(b(''), roundtrip(v))


if __name__ == '__main__':
    unittest2.main()
