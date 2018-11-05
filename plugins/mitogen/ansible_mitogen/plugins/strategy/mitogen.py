# Copyright 2017, David Wilson
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its contributors
# may be used to endorse or promote products derived from this software without
# specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

from __future__ import absolute_import
import os.path
import sys

#
# This is not the real Strategy implementation module, it simply exists as a
# proxy to the real module, which is loaded using Python's regular import
# mechanism, to prevent Ansible's PluginLoader from making up a fake name that
# results in ansible_mitogen plugin modules being loaded twice: once by
# PluginLoader with a name like "ansible.plugins.strategy.mitogen", which is
# stuffed into sys.modules even though attempting to import it will trigger an
# ImportError, and once under its canonical name, "ansible_mitogen.strategy".
#
# Therefore we have a proxy module that imports it under the real name, and
# sets up the duff PluginLoader-imported module to just contain objects from
# the real module, so duplicate types don't exist in memory, and things like
# debuggers and isinstance() work predictably.
#

BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../../..')
)

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import ansible_mitogen.strategy
import ansible.plugins.strategy.linear


class StrategyModule(ansible_mitogen.strategy.StrategyMixin,
                     ansible.plugins.strategy.linear.StrategyModule):
    pass
