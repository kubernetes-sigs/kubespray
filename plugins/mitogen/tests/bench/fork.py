"""
Measure latency of .fork() setup/teardown.
"""

import mitogen
import time

@mitogen.main()
def main(router):
    t0 = time.time()
    for x in xrange(200):
        t = time.time()
        ctx = router.fork()
        ctx.shutdown(wait=True)
    print '++', 1000 * ((time.time() - t0) / (1.0+x))
