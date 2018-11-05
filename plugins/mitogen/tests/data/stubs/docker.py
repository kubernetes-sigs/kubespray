#!/usr/bin/env python

import sys
import os

os.environ['ORIGINAL_ARGV'] = repr(sys.argv)
os.execv(sys.executable, sys.argv[sys.argv.index('-c') - 1:])
