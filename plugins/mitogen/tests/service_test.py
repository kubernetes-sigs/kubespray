import unittest2

import mitogen.core
import mitogen.service
import testlib


class MyService(mitogen.service.Service):
    def __init__(self, router):
        super(MyService, self).__init__(router)
        self._counter = 0

    @mitogen.service.expose(policy=mitogen.service.AllowParents())
    def get_id(self):
        self._counter += 1
        return self._counter, id(self)

    @mitogen.service.expose(policy=mitogen.service.AllowParents())
    def privileged_op(self):
        return 'privileged!'

    @mitogen.service.expose(policy=mitogen.service.AllowAny())
    def unprivileged_op(self):
        return 'unprivileged!'



class MyService2(MyService):
    """
    A uniquely named service that lets us test framework activation and class
    activation separately.
    """


def call_service_in(context, service_name, method_name):
    return context.call_service(service_name, method_name)


class ActivationTest(testlib.RouterMixin, testlib.TestCase):
    def test_parent_can_activate(self):
        l1 = self.router.fork()
        counter, id_ = l1.call_service(MyService, 'get_id')
        self.assertEquals(1, counter)
        self.assertTrue(isinstance(id_, int))

    def test_sibling_cannot_activate_framework(self):
        l1 = self.router.fork()
        l2 = self.router.fork()
        exc = self.assertRaises(mitogen.core.CallError,
            lambda: l2.call(call_service_in, l1, MyService2.name(), 'get_id'))
        self.assertTrue(mitogen.core.Router.refused_msg in exc.args[0])

    def test_sibling_cannot_activate_service(self):
        l1 = self.router.fork()
        l2 = self.router.fork()
        l1.call_service(MyService, 'get_id')  # force framework activation
        exc = self.assertRaises(mitogen.core.CallError,
            lambda: l2.call(call_service_in, l1, MyService2.name(), 'get_id'))
        msg = mitogen.service.Activator.not_active_msg % (MyService2.name(),)
        self.assertTrue(msg in exc.args[0])

    def test_activates_only_once(self):
        l1 = self.router.fork()
        counter, id_ = l1.call_service(MyService, 'get_id')
        counter2, id_2 = l1.call_service(MyService, 'get_id')
        self.assertEquals(1, counter)
        self.assertEquals(2, counter2)
        self.assertEquals(id_, id_2)


class PermissionTest(testlib.RouterMixin, testlib.TestCase):
    def test_sibling_unprivileged_ok(self):
        l1 = self.router.fork()
        l1.call_service(MyService, 'get_id')
        l2 = self.router.fork()
        self.assertEquals('unprivileged!',
            l2.call(call_service_in, l1, MyService.name(), 'unprivileged_op'))

    def test_sibling_privileged_bad(self):
        l1 = self.router.fork()
        l1.call_service(MyService, 'get_id')
        l2 = self.router.fork()
        exc = self.assertRaises(mitogen.core.CallError, lambda:
            l2.call(call_service_in, l1, MyService.name(), 'privileged_op'))
        msg = mitogen.service.Invoker.unauthorized_msg % (
            u'privileged_op',
            MyService.name(),
        )
        self.assertTrue(msg in exc.args[0])


if __name__ == '__main__':
    unittest2.main()
