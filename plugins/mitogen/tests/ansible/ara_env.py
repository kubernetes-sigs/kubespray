#!/usr/bin/env python

"""
Print shell environment exports adding ARA plugins to the list of plugins
from ansible.cfg in the CWD.
"""

import os

import ara.setup
import ansible.constants as C

os.chdir(os.path.dirname(__file__))

print('export ANSIBLE_ACTION_PLUGINS=%s:%s' % (
    ':'.join(C.DEFAULT_ACTION_PLUGIN_PATH),
    ara.setup.action_plugins,
))

print('export ANSIBLE_CALLBACK_PLUGINS=%s:%s' % (
    ':'.join(C.DEFAULT_CALLBACK_PLUGIN_PATH),
    ara.setup.callback_plugins,
))

print('export ANSIBLE_LIBRARY=%s:%s' % (
    ':'.join(C.DEFAULT_MODULE_PATH),
    ara.setup.library,
))
