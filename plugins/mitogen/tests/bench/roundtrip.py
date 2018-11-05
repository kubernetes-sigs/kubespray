"""
Measure latency of local RPC.
"""

import mitogen
import time

def do_nothing():
    pass

@mitogen.main()
def main(router):
    f = router.fork()
    t0 = time.time()
    for x in range(1000):
        f.call(do_nothing)
    print '++', int(1e6 * ((time.time() - t0) / (1.0+x))), 'usec'
