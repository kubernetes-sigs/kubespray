#!/usr/bin/env python
#
# pip install fusepy
#
# This implementation could improve a /lot/, but the core library is missing
# some functionality (#213) to make that easy. Additionally it needs a set of
# Python bindings for FUSE that stupidly require use of a thread pool.

from __future__ import absolute_import, division
from __future__ import unicode_literals

import errno
import logging
import threading
import sys
import time

import fuse
import mitogen.master
import mitogen.utils

import __main__
import posix
import os


LOG = logging.getLogger(__name__)


def to_text(p):
    """
    On 3.x, fusepy returns paths as bytes.
    """
    if isinstance(p, bytes):
        return p.decode('utf-8')
    return p


def errno_wrap(modname, func, *args):
    try:
        return getattr(globals()[modname], func)(*args), None
    except (IOError, OSError):
        e = sys.exc_info()[1]
        if e.args[0] == errno.ENOENT:
            LOG.error('%r(**%r): %s', func, args, e)
        else:
            LOG.exception('While running %r(**%r)', func, args)
        return None, to_text(errno.errorcode[e.args[0]])


def errno_call(context, func, *args):
    result, errname = context.call(
        errno_wrap,
        func.__module__,
        func.__name__,
        *args
    )
    if errname:
        raise fuse.FuseOSError(getattr(errno, errname))
    return result


def _create(path, mode):
    fd = os.open(path, os.O_WRONLY)
    try:
        os.fchmod(fd, mode)
    finally:
        os.close(fd)


def _stat(path):
    st = os.lstat(path)
    keys = ('st_atime', 'st_gid', 'st_mode', 'st_mtime', 'st_size', 'st_uid')
    dct = dict((key, getattr(st, key)) for key in keys)
    dct['has_contents'] = os.path.exists(os.path.join(path, 'Contents'))
    return dct


def _listdir(path):
    return [
        (name, _stat(os.path.join(path, name)), 0)
        for name in os.listdir(path)
    ]


def _read(path, size, offset):
    fd = os.open(path, os.O_RDONLY)
    try:
        os.lseek(fd, offset, os.SEEK_SET)
        return os.read(fd, size)
    finally:
        os.close(fd)


def _truncate(path, length):
    fd = os.open(path, os.O_RDWR)
    try:
        os.truncate(fd, length)
    finally:
        os.close(fd)


def _write(path, data, offset):
    fd = os.open(path, os.O_RDWR)
    try:
        os.lseek(fd, offset, os.SEEK_SET)
        return os.write(fd, data)
    finally:
        os.close(fd)


def _evil_name(path):
    if not (os.path.basename(path).startswith('._') or
            path.endswith('.DS_Store')):
        return
    raise fuse.FuseOSError(errno.ENOENT)


def _chroot(path):
    os.chroot(path)


class Operations(fuse.Operations):  # fuse.LoggingMixIn, 
    def __init__(self, host, path='.'):
        self.host = host
        self.root = path
        self.ready = threading.Event()
        if not hasattr(self, 'encoding'):
            self.encoding = 'utf-8'

    def init(self, path):
        self.broker = mitogen.master.Broker(install_watcher=False)
        self.router = mitogen.master.Router(self.broker)
        self.host = self.router.ssh(hostname=self.host)
        self._context = self.router.sudo(via=self.host)
        #self._context.call(_chroot , '/home/dmw')
        self._stat_cache = {}
        self.ready.set()

    def destroy(self, path):
        self.broker.shutdown()

    @property
    def context(self):
        self.ready.wait()
        return self._context

    def chmod(self, path, mode):
        path = path.decode(self.encoding)
        _evil_name(path)
        return errno_call(self._context, os.chmod, path, mode)

    def chown(self, path, uid, gid):
        path = path.decode(self.encoding)
        _evil_name(path)
        return errno_call(self._context, os.chown, path, uid, gid)

    def create(self, path, mode):
        path = path.decode(self.encoding)
        _evil_name(path)
        return errno_call(self._context, _create, path, mode) or 0

    def getattr(self, path, fh=None):
        _evil_name(path)
        if path in self._stat_cache:
            now = time.time()
            then, st = self._stat_cache[path]
            if now < (then + 2.0):
                return st
        basedir = os.path.dirname(path)
        if path.endswith('/Contents') and basedir in self._stat_cache:
            now = time.time()
            then, st = self._stat_cache[basedir]
            if now < (then + 2.0) and not st['has_contents']:
                raise fuse.FuseOSError(errno.ENOENT)

        return errno_call(self._context, _stat, path)

    def mkdir(self, path, mode):
        path = path.decode(self.encoding)
        _evil_name(path)
        return errno_call(self._context, os.mkdir, path, mode)

    def read(self, path, size, offset, fh):
        path = path.decode(self.encoding)
        _evil_name(path)
        return errno_call(self._context, _read, path, size, offset)

    def readdir(self, path, fh):
        _evil_name(path)
        lst = errno_call(self._context, _listdir, path)
        now = time.time()
        for name, stat, _ in lst:
            self._stat_cache[os.path.join(path, name)] = (now, stat)
        return lst

    def readlink(self, path):
        _evil_name(path)
        return errno_call(self._context, os.readlink, path)

    def rename(self, old, new):
        old = old.decode(self.encoding)
        new = new.decode(self.encoding)
        return errno_call(self._context, os.rename, old, new)
        # TODO return self.sftp.rename(old, self.root + new)

    def rmdir(self, path):
        path = path.decode(self.encoding)
        _evil_name(path)
        return errno_call(self._context, os.rmdir, path)

    def symlink(self, target, source):
        target = target.decode(self.encoding)
        source = source.decode(self.encoding)
        _evil_name(path)
        return errno_call(self._context, os.symlink, source, target)

    def truncate(self, path, length, fh=None):
        path = path.decode(self.encoding)
        _evil_name(path)
        return errno_call(self._context, _truncate, path, length)

    def unlink(self, path):
        path = path.decode(self.encoding)
        _evil_name(path)
        return errno_call(self._context, os.unlink, path)

    def utimens(self, path, times=None):
        path = path.decode(self.encoding)
        _evil_name(path)
        return errno_call(self._context, os.utime, path, times)

    def write(self, path, data, offset, fh):
        path = path.decode(self.encoding)
        _evil_name(path)
        return errno_call(self._context, _write, path, data, offset)


@mitogen.main(log_level='DEBUG')
def main(router):
    if len(sys.argv) != 3:
        print('usage: %s <host> <mountpoint>' % sys.argv[0])
        sys.exit(1)

    blerp = fuse.FUSE(
        operations=Operations(sys.argv[1]),
        mountpoint=sys.argv[2],
        foreground=True,
        volname='%s (Mitogen)' % (sys.argv[1],),
    )
