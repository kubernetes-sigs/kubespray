# https://github.com/dw/mitogen/issues/297

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.plugins.vars import BaseVarsPlugin
import os

class VarsModule(BaseVarsPlugin):
    def __init__(self, *args):
        super(VarsModule, self).__init__(*args)
        os.environ['EVIL_VARS_PLUGIN'] = 'YIPEEE'

    def get_vars(self, loader, path, entities, cache=True):
        super(VarsModule, self).get_vars(loader, path, entities)
        return {}
