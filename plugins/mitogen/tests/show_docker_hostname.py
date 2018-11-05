#!/usr/bin/env python

"""
For use by the Travis scripts, just print out the hostname of the Docker
daemon from the environment.
"""

import testlib
print(testlib.get_docker_host())
