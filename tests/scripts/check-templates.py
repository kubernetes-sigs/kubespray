#!/usr/bin/env python

import sys
from jinja2 import Environment

env = Environment()
for template in sys.argv[1:]:
    with open(template) as t:
        env.parse(t.read())
