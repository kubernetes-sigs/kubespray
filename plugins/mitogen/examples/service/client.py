
import socket

import mitogen.master
import mitogen.unix
import mitogen.service
import mitogen.utils


PING = 500


mitogen.utils.log_to_file()

router, parent = mitogen.unix.connect('/tmp/mitosock')
with router:
    print(mitogen.service.call(parent, CONNECT_BY_ID, {}))
