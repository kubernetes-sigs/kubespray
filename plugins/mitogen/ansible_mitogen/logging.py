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
import logging
import os
import sys

import mitogen.core
import mitogen.utils

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class Handler(logging.Handler):
    """
    Use Mitogen's log format, but send the result to a Display method.
    """
    def __init__(self, normal_method):
        logging.Handler.__init__(self)
        self.formatter = mitogen.utils.log_get_formatter()
        self.normal_method = normal_method

    #: Set of target loggers that produce warnings and errors that spam the
    #: console needlessly. Their log level is forced to INFO. A better strategy
    #: may simply be to bury all target logs in DEBUG output, but not by
    #: overriding their log level as done here.
    NOISY_LOGGERS = frozenset([
        'dnf',  # issue #272; warns when a package is already installed.
    ])

    def emit(self, record):
        mitogen_name = getattr(record, 'mitogen_name', '')
        if mitogen_name == 'stderr':
            record.levelno = logging.ERROR
        if mitogen_name in self.NOISY_LOGGERS and record.levelno >= logging.WARNING:
            record.levelno = logging.DEBUG

        s = '[pid %d] %s' % (os.getpid(), self.format(record))
        if record.levelno >= logging.ERROR:
            display.error(s, wrap_text=False)
        elif record.levelno >= logging.WARNING:
            display.warning(s, formatted=True)
        else:
            self.normal_method(s)


def setup():
    """
    Install a handler for Mitogen's logger to redirect it into the Ansible
    display framework, and prevent propagation to the root logger.
    """
    logging.getLogger('ansible_mitogen').handlers = [Handler(display.vvv)]
    mitogen.core.LOG.handlers = [Handler(display.vvv)]
    mitogen.core.IOLOG.handlers = [Handler(display.vvvv)]
    mitogen.core.IOLOG.propagate = False

    if display.verbosity > 2:
        mitogen.core.LOG.setLevel(logging.DEBUG)
        logging.getLogger('ansible_mitogen').setLevel(logging.DEBUG)
    else:
        # Mitogen copies the active log level into new children, allowing them
        # to filter tiny messages before they hit the network, and therefore
        # before they wake the IO loop. Explicitly setting INFO saves ~4%
        # running against just the local machine.
        mitogen.core.LOG.setLevel(logging.ERROR)
        logging.getLogger('ansible_mitogen').setLevel(logging.ERROR)

    if display.verbosity > 3:
        mitogen.core.IOLOG.setLevel(logging.DEBUG)
        logging.getLogger('ansible_mitogen').setLevel(logging.DEBUG)
