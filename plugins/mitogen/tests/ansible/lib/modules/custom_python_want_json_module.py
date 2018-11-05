#!/usr/bin/python
# I am an Ansible Python WANT_JSON module. I should receive an encoding string.

import json
import sys

WANT_JSON = 1


def usage():
    sys.stderr.write('Usage: %s <input.json>\n' % (sys.argv[0],))
    sys.exit(1)

if len(sys.argv) < 2:
    usage()

# Also must slurp in our own source code, to verify the encoding string was
# added.
with open(sys.argv[0]) as fp:
    me = fp.read()

try:
    with open(sys.argv[1]) as fp:
        input_json = fp.read()
except IOError:
    usage()

print("{")
print("  \"changed\": false,")
print("  \"msg\": \"Here is my input\",")
print("  \"source\": [%s]," % (json.dumps(me),))
print("  \"input\": [%s]" % (input_json,))
print("}")
