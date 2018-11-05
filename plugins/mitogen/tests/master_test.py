import inspect

import unittest2

import testlib
import mitogen.master


class ScanCodeImportsTest(unittest2.TestCase):
    func = staticmethod(mitogen.master.scan_code_imports)

    if mitogen.core.PY3:
        level = 0
    else:
        level = -1

    SIMPLE_EXPECT = [
        (level, 'inspect', ()),
        (level, 'unittest2', ()),
        (level, 'testlib', ()),
        (level, 'mitogen.master', ()),
    ]

    def test_simple(self):
        source_path = inspect.getsourcefile(ScanCodeImportsTest)
        co = compile(open(source_path).read(), source_path, 'exec')
        self.assertEquals(list(self.func(co)), self.SIMPLE_EXPECT)


if __name__ == '__main__':
    unittest2.main()
