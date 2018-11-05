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

"""
Classes to detect each case from [0] and prepare arguments necessary for the
corresponding Runner class within the target, including preloading requisite
files/modules known missing.

[0] "Ansible Module Architecture", developing_program_flow_modules.html
"""

from __future__ import absolute_import
from __future__ import unicode_literals

import mitogen.core


def parse_script_interpreter(source):
    """
    Parse the script interpreter portion of a UNIX hashbang using the rules
    Linux uses.

    :param str source: String like "/usr/bin/env python".

    :returns:
        Tuple of `(interpreter, arg)`, where `intepreter` is the script
        interpreter and `arg` is its sole argument if present, otherwise
        :py:data:`None`.
    """
    # Find terminating newline. Assume last byte of binprm_buf if absent.
    nl = source.find(b'\n', 0, 128)
    if nl == -1:
        nl = min(128, len(source))

    # Split once on the first run of whitespace. If no whitespace exists,
    # bits just contains the interpreter filename.
    bits = source[0:nl].strip().split(None, 1)
    if len(bits) == 1:
        return mitogen.core.to_text(bits[0]), None
    return mitogen.core.to_text(bits[0]), mitogen.core.to_text(bits[1])


def parse_hashbang(source):
    """
    Parse a UNIX "hashbang line" using the syntax supported by Linux.

    :param str source: String like "#!/usr/bin/env python".

    :returns:
        Tuple of `(interpreter, arg)`, where `intepreter` is the script
        interpreter and `arg` is its sole argument if present, otherwise
        :py:data:`None`.
    """
    # Linux requires first 2 bytes with no whitespace, pretty sure it's the
    # same everywhere. See binfmt_script.c.
    if not source.startswith(b'#!'):
        return None, None

    return parse_script_interpreter(source[2:])
