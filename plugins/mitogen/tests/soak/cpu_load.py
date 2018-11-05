#!/usr/bin/env python
"""
Put the machine's CPUs under pressure to increase the likelihood of scheduling
weirdness. Useful for exposing otherwise difficult to hit races in the library.
"""

import ctypes
import multiprocessing
import os
import time

LIBC = ctypes.CDLL('libc.so.6')
sched_yield = LIBC.sched_yield


def burn():
    while 1:
        a, b, c = os.urandom(3)
        n = int(((ord(a) << 16) |
                 (ord(b) << 8) |
                 (ord(c) << 0)) / 1.6)
        print(n)
        for x in xrange(n): pass
        sched_yield()

mul = 1.5
count = int(mul * multiprocessing.cpu_count())
print count

procs = [multiprocessing.Process(target=burn)
         for _ in range(count)]

for i, proc in enumerate(procs):
    print([i])
    proc.start()
