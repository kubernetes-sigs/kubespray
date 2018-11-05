
# The service framework will fundamentally change (i.e. become much nicer, and
# hopefully lose those hard-coded magic numbers somehow), but meanwhile this is
# a taster of how it looks today.

import time

import mitogen
import mitogen.service
import mitogen.unix


class PingService(mitogen.service.Service):
    def dispatch(self, dct, msg):
        return 'Hello, world'


@mitogen.main()
def main(router):
    listener = mitogen.unix.Listener(router, path='/tmp/mitosock')
    service = PingService(router)
    service.run()
