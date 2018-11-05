
# Verify _receive_one() quadratic behaviour fixed.

import subprocess
import time
import socket
import mitogen


@mitogen.main()
def main(router):
    c = router.fork()

    n = 1048576 * 127
    s = ' ' * n
    print('bytes in %.2fMiB string...' % (n/1048576.0),)

    t0 = time.time()
    for x in range(10):
        tt0 = time.time()
        assert n == c.call(len, s)
        print('took %dms' % (1000 * (time.time() - tt0),))
    t1 = time.time()
    print('total %dms / %dms avg / %.2fMiB/sec' % (
        1000 * (t1 - t0),
        (1000 * (t1 - t0)) / (x + 1),
        ((n * (x + 1)) / (t1 - t0)) / 1048576.0,
    ))
