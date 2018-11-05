#!/usr/bin/python
# I am an Ansible Python JSONARGS module. I should receive an encoding string.

import json
import sys

json_arguments = """<<INCLUDE_ANSIBLE_MODULE_JSON_ARGS>>"""

print("{")
print("  \"changed\": false,")
print("  \"msg\": \"Here is my input\",")
print("  \"input\": [%s]" % (json_arguments,))
print("}")
