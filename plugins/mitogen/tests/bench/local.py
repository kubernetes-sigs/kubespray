"""
Measure latency of .local() setup.
"""

import mitogen
import time


@mitogen.main()
def main(router):
    for x in range(1000):
        t = time.time()
        f = router.local()# debug=True)
        tt = time.time()
        print(x, 1000 * (tt - t))

    print(f)
    print('EEK', f.call(socket.gethostname))
    print('MY PID', os.getpid())
    print('EEKERY', f.call(os.getpid))
