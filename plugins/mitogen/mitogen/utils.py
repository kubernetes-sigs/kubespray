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

import datetime
import logging
import os
import sys

import mitogen
import mitogen.core
import mitogen.master


LOG = logging.getLogger('mitogen')
iteritems = getattr(dict, 'iteritems', dict.items)

if mitogen.core.PY3:
    iteritems = dict.items
else:
    iteritems = dict.iteritems


def disable_site_packages():
    for entry in sys.path[:]:
        if 'site-packages' in entry or 'Extras' in entry:
            sys.path.remove(entry)


def _formatTime(record, datefmt=None):
    dt = datetime.datetime.fromtimestamp(record.created)
    return dt.strftime(datefmt)


def log_get_formatter():
    datefmt = '%H:%M:%S.%f'
    fmt = '%(asctime)s %(levelname).1s %(name)s: %(message)s'
    formatter = logging.Formatter(fmt, datefmt)
    formatter.formatTime = _formatTime
    return formatter


def log_to_file(path=None, io=False, level='INFO'):
    log = logging.getLogger('')
    if path:
        fp = open(path, 'w', 1)
        mitogen.core.set_cloexec(fp.fileno())
    else:
        fp = sys.stderr

    level = os.environ.get('MITOGEN_LOG_LEVEL', level).upper()
    io = level == 'IO'
    if io:
        level = 'DEBUG'
        logging.getLogger('mitogen.io').setLevel(level)

    level = getattr(logging, level, logging.INFO)
    log.setLevel(level)

    # Prevent accidental duplicate log_to_file() calls from generating
    # duplicate output.
    for handler_ in reversed(log.handlers):
        if getattr(handler_, 'is_mitogen', None):
            log.handlers.remove(handler_)

    handler = logging.StreamHandler(fp)
    handler.is_mitogen = True
    handler.formatter = log_get_formatter()
    log.handlers.insert(0, handler)


def run_with_router(func, *args, **kwargs):
    broker = mitogen.master.Broker()
    router = mitogen.master.Router(broker)
    try:
        return func(router, *args, **kwargs)
    finally:
        broker.shutdown()
        broker.join()


def with_router(func):
    def wrapper(*args, **kwargs):
        return run_with_router(func, *args, **kwargs)
    if mitogen.core.PY3:
        wrapper.func_name = func.__name__
    else:
        wrapper.func_name = func.func_name
    return wrapper


PASSTHROUGH = (
    int, float, bool,
    type(None),
    mitogen.core.Context,
    mitogen.core.CallError,
    mitogen.core.Blob,
    mitogen.core.Secret,
)

def cast(obj):
    if isinstance(obj, dict):
        return dict((cast(k), cast(v)) for k, v in iteritems(obj))
    if isinstance(obj, (list, tuple)):
        return [cast(v) for v in obj]
    if isinstance(obj, PASSTHROUGH):
        return obj
    if isinstance(obj, mitogen.core.UnicodeType):
        return mitogen.core.UnicodeType(obj)
    if isinstance(obj, mitogen.core.BytesType):
        return mitogen.core.BytesType(obj)

    raise TypeError("Cannot serialize: %r: %r" % (type(obj), obj))
