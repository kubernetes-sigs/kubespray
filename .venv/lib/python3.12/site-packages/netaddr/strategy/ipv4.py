# -----------------------------------------------------------------------------
#   Copyright (c) 2008 by David P. D. Moss. All rights reserved.
#
#   Released under the BSD license. See the LICENSE file for details.
# -----------------------------------------------------------------------------
"""IPv4 address logic."""

import sys as _sys
import struct as _struct

from socket import inet_aton as _inet_aton

#   Check whether we need to use fallback code or not.
if _sys.platform in ('win32', 'cygwin'):
    #   inet_pton() not available on Windows. inet_pton() under cygwin
    #   behaves exactly like inet_aton() and is therefore highly unreliable.
    from netaddr.fbsocket import inet_pton as _inet_pton, AF_INET
else:
    #   All other cases, use all functions from the socket module.
    from socket import inet_pton as _inet_pton, AF_INET

from netaddr.core import AddrFormatError, ZEROFILL, INET_ATON, INET_PTON

from netaddr.strategy import (
    valid_words as _valid_words,
    valid_bits as _valid_bits,
    bits_to_int as _bits_to_int,
    int_to_bits as _int_to_bits,
    valid_bin as _valid_bin,
    int_to_bin as _int_to_bin,
    bin_to_int as _bin_to_int,
)


#: The width (in bits) of this address type.
width = 32

#: The individual word size (in bits) of this address type.
word_size = 8

#: The format string to be used when converting words to string values.
word_fmt = '%d'

#: The separator character used between each word.
word_sep = '.'

#: The AF_* constant value of this address type.
family = AF_INET

#: A friendly string name address type.
family_name = 'IPv4'

#: The version of this address type.
version = 4

#: The number base to be used when interpreting word values as integers.
word_base = 10

#: The maximum integer value that can be represented by this address type.
max_int = 2**width - 1

#: The number of words in this address type.
num_words = width // word_size

#: The maximum integer value for an individual word in this address type.
max_word = 2**word_size - 1

#: A dictionary mapping IPv4 CIDR prefixes to the equivalent netmasks.
prefix_to_netmask = dict([(i, max_int ^ (2 ** (width - i) - 1)) for i in range(0, width + 1)])

#: A dictionary mapping IPv4 netmasks to their equivalent CIDR prefixes.
netmask_to_prefix = dict([(max_int ^ (2 ** (width - i) - 1), i) for i in range(0, width + 1)])

#: A dictionary mapping IPv4 CIDR prefixes to the equivalent hostmasks.
prefix_to_hostmask = dict([(i, (2 ** (width - i) - 1)) for i in range(0, width + 1)])

#: A dictionary mapping IPv4 hostmasks to their equivalent CIDR prefixes.
hostmask_to_prefix = dict([((2 ** (width - i) - 1), i) for i in range(0, width + 1)])


def valid_str(addr, flags=0):
    """
    :param addr: An IPv4 address in presentation (string) format.

    :param flags: decides which rules are applied to the interpretation of the
        addr value. Supported constants are INET_PTON and ZEROFILL. See the
        :class:`IPAddress` documentation for details.

    .. versionchanged:: 0.10.1
        ``flags`` is scheduled to default to :data:`INET_PTON` instead of :data:`INET_ATON`
        in the future.

    :return: ``True`` if IPv4 address is valid, ``False`` otherwise.

    .. versionchanged:: 1.0.0
        Returns ``False`` instead of raising :exc:`AddrFormatError` for empty strings.
    """
    if not isinstance(addr, str):
        raise TypeError('Invalid type: %s' % type(addr))
    try:
        str_to_int(addr, flags)
    except AddrFormatError:
        return False
    return True


def str_to_int(addr, flags=0):
    """
    :param addr: An IPv4 dotted decimal address in string form.

    :param flags: decides which rules are applied to the interpretation of the
        addr value. Supported constants are INET_PTON and ZEROFILL. See the
        :class:`IPAddress` documentation for details.

    :return: The equivalent unsigned integer for a given IPv4 address.
    """
    error = AddrFormatError('%r is not a valid IPv4 address string!' % (addr,))
    if ':' in addr:
        raise error
    pton_mode = flags & INET_PTON or not flags & INET_ATON
    if flags & ZEROFILL:
        addr = '.'.join(['%d' % int(i) for i in addr.split('.')])
    elif pton_mode and any(len(p) > 1 and p.startswith('0') for p in addr.split('.')):
        raise error

    try:
        if pton_mode:
            packed = _inet_pton(AF_INET, addr)
        else:
            packed = _inet_aton(addr)
    except OSError:
        raise error
    return _struct.unpack('>I', packed)[0]


def int_to_str(int_val, dialect=None):
    """
    :param int_val: An unsigned integer.

    :param dialect: (unused) Any value passed in is ignored.

    :return: The IPv4 presentation (string) format address equivalent to the
        unsigned integer provided.
    """
    if 0 <= int_val <= max_int:
        return '%d.%d.%d.%d' % (
            int_val >> 24,
            (int_val >> 16) & 0xFF,
            (int_val >> 8) & 0xFF,
            int_val & 0xFF,
        )
    else:
        raise ValueError('%r is not a valid 32-bit unsigned integer!' % (int_val,))


def int_to_arpa(int_val):
    """
    :param int_val: An unsigned integer.

    :return: The reverse DNS lookup for an IPv4 address in network byte
        order integer form.
    """
    words = ['%d' % i for i in int_to_words(int_val)]
    words.reverse()
    words.extend(['in-addr', 'arpa', ''])
    return '.'.join(words)


def int_to_packed(int_val):
    """
    :param int_val: the integer to be packed.

    :return: a packed string that is equivalent to value represented by an
    unsigned integer.
    """
    return _struct.pack('>I', int_val)


def packed_to_int(packed_int):
    """
    :param packed_int: a packed string containing an unsigned integer.
        It is assumed that string is packed in network byte order.

    :return: An unsigned integer equivalent to value of network address
        represented by packed binary string.
    """
    return _struct.unpack('>I', packed_int)[0]


def valid_words(words):
    return _valid_words(words, word_size, num_words)


def int_to_words(int_val):
    """
    :param int_val: An unsigned integer.

    :return: An integer word (octet) sequence that is equivalent to value
        represented by an unsigned integer.
    """
    if not 0 <= int_val <= max_int:
        raise ValueError(
            '%r is not a valid integer value supported by' 'this address type!' % (int_val,)
        )
    return (int_val >> 24, (int_val >> 16) & 0xFF, (int_val >> 8) & 0xFF, int_val & 0xFF)


def words_to_int(words):
    """
    :param words: A list or tuple containing integer octets.

    :return: An unsigned integer that is equivalent to value represented
        by word (octet) sequence.
    """
    if not valid_words(words):
        raise ValueError('%r is not a valid octet list for an IPv4 address!' % (words,))
    return _struct.unpack('>I', _struct.pack('4B', *words))[0]


def valid_bits(bits):
    return _valid_bits(bits, width, word_sep)


def bits_to_int(bits):
    return _bits_to_int(bits, width, word_sep)


def int_to_bits(int_val, word_sep=None):
    if word_sep is None:
        word_sep = globals()['word_sep']
    return _int_to_bits(int_val, word_size, num_words, word_sep)


def valid_bin(bin_val):
    return _valid_bin(bin_val, width)


def int_to_bin(int_val):
    return _int_to_bin(int_val, width)


def bin_to_int(bin_val):
    return _bin_to_int(bin_val, width)


def expand_partial_address(addr):
    """
    Expands a partial IPv4 address into a full 4-octet version.

    :param addr: an partial or abbreviated IPv4 address

    :return: an expanded IP address in presentation format (x.x.x.x)

    >>> expand_partial_address('1.2')
    '1.2.0.0'

    .. versionadded:: 1.1.0
    """
    tokens = []

    error = AddrFormatError('invalid partial IPv4 address: %r!' % addr)

    if isinstance(addr, str):
        if ':' in addr:
            #   Ignore IPv6 ...
            raise error

        try:
            if '.' in addr:
                tokens = ['%d' % int(o) for o in addr.split('.')]
            else:
                tokens = ['%d' % int(addr)]
        except ValueError:
            raise error

        if 1 <= len(tokens) <= 4:
            for i in range(4 - len(tokens)):
                tokens.append('0')
        else:
            raise error

    if not tokens:
        raise error

    return '%s.%s.%s.%s' % tuple(tokens)
