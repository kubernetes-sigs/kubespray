"""
Print the size of a typical SSH command line and the bootstrap code sent to new
contexts.
"""

import inspect
import sys
import zlib

import mitogen.fakessh
import mitogen.master
import mitogen.minify
import mitogen.parent
import mitogen.select
import mitogen.service
import mitogen.ssh
import mitogen.sudo

router = mitogen.master.Router()
context = mitogen.parent.Context(router, 0)
stream = mitogen.ssh.Stream(router, 0, max_message_size=0, hostname='foo')

print('SSH command size: %s' % (len(' '.join(stream.get_boot_command())),))
print('Preamble size: %s (%.2fKiB)' % (
    len(stream.get_preamble()),
    len(stream.get_preamble()) / 1024.0,
))
if '--dump' in sys.argv:
    print(zlib.decompress(stream.get_preamble()))
    exit()


print(
    '               '
    ' '
    '  Original   '
    '  '
    '     Minimized     '
    '  '
    '    Compressed     '
)

for mod in (
        mitogen.parent,
        mitogen.ssh,
        mitogen.sudo,
        mitogen.select,
        mitogen.service,
        mitogen.fakessh,
        mitogen.master,
    ):
    original = inspect.getsource(mod)
    original_size = len(original)
    minimized = mitogen.minify.minimize_source(original)
    minimized_size = len(minimized)
    compressed = zlib.compress(minimized, 9)
    compressed_size = len(compressed)
    print(
        '%-15s'
        ' '
        '%5i %4.1fKiB'
        '  '
        '%5i %4.1fKiB %.1f%%'
        '  '
        '%5i %4.1fKiB %.1f%%'
    % (
        mod.__name__,
        original_size,
        original_size / 1024.0,
        minimized_size,
        minimized_size / 1024.0,
        100 * minimized_size / float(original_size),
        compressed_size,
        compressed_size / 1024.0,
        100 * compressed_size / float(original_size),
    ))
