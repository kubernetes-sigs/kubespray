"""
Used for stressing Latch.get/put. Swap the number of producer/consumer threads
below to try both -- there are many conditions in the Latch code that require
testing of both.
"""

import logging
import random
import threading
import time
import mitogen.core
import mitogen.utils

mitogen.utils.log_to_file()
mitogen.core.IOLOG.setLevel(logging.DEBUG)
mitogen.core._v = True
mitogen.core._vv = True

l = mitogen.core.Latch()
consumed = 0
produced = 0
crash = 0

def cons():
    global consumed, crash
    try:
        while 1:
            g = l.get()
            print('got=%s consumed=%s produced=%s crash=%s' % (g, consumed, produced, crash))
            consumed += 1
            time.sleep(g)
            for x in range(int(g * 1000)):
                pass
    except:
        crash += 1

def prod():
    global produced
    while 1:
        l.put(random.random()/10)
        produced += 1
        time.sleep(random.random()/10)

allc = [threading.Thread(target=cons) for x in range(64)]
allp = [threading.Thread(target=prod) for x in range(8)]
for th in allc+allp:
    th.setDaemon(True)
    th.start()

raw_input()
exit()
