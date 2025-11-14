import pytest

from netaddr import INET_ATON, INET_PTON, AddrFormatError, ZEROFILL
from netaddr.strategy import ipv4


def test_strategy_ipv4():
    b = '11000000.00000000.00000010.00000001'
    i = 3221225985
    t = (192, 0, 2, 1)
    s = '192.0.2.1'
    bin_val = '0b11000000000000000000001000000001'
    p = b'\xc0\x00\x02\x01'

    assert ipv4.bits_to_int(b) == i
    assert ipv4.int_to_bits(i) == b
    assert ipv4.int_to_str(i) == s
    assert ipv4.int_to_words(i) == t
    assert ipv4.int_to_bin(i) == bin_val
    assert ipv4.int_to_bin(i) == bin_val
    assert ipv4.bin_to_int(bin_val) == i
    assert ipv4.words_to_int(t) == i
    assert ipv4.words_to_int(list(t)) == i
    assert ipv4.valid_bin(bin_val)
    assert ipv4.int_to_packed(i) == p
    assert ipv4.packed_to_int(p) == i


def test_strategy_inet_aton_behaviour():
    # inet_aton() is a very old system call and is very permissive with
    # regard to what is assume is a valid IPv4 address.

    assert ipv4.str_to_int('127', flags=INET_ATON) == 127
    assert ipv4.str_to_int('0x7f', flags=INET_ATON) == 127
    assert ipv4.str_to_int('0177', flags=INET_ATON) == 127
    assert ipv4.str_to_int('127.1', flags=INET_ATON) == 2130706433
    assert ipv4.str_to_int('0x7f.1', flags=INET_ATON) == 2130706433
    assert ipv4.str_to_int('0177.1', flags=INET_ATON) == 2130706433
    assert ipv4.str_to_int('127.0.0.1', flags=INET_ATON) == 2130706433


def test_str_to_int_correctly_rejects_ipv6_with_zerofill():
    with pytest.raises(AddrFormatError):
        ipv4.str_to_int('fe80::', flags=ZEROFILL)


def test_strategy_inet_pton_behaviour():
    # inet_pton() is a newer system call that supports both IPv4 and IPv6.
    # It is a lot more strict about what it deems to be a valid IPv4 address
    # and doesn't support many of the features found in inet_aton() such as
    # support for non- decimal octets, partial numbers of octets, etc.

    with pytest.raises(AddrFormatError):
        ipv4.str_to_int('127', flags=INET_PTON)

    with pytest.raises(AddrFormatError):
        ipv4.str_to_int('0x7f', flags=INET_PTON)

    with pytest.raises(AddrFormatError):
        ipv4.str_to_int('0177', flags=INET_PTON)

    with pytest.raises(AddrFormatError):
        ipv4.str_to_int('127.1', flags=INET_PTON)

    with pytest.raises(AddrFormatError):
        ipv4.str_to_int('0x7f.1', flags=INET_PTON)

    with pytest.raises(AddrFormatError):
        ipv4.str_to_int('0177.1', flags=INET_PTON)

    assert ipv4.str_to_int('127.0.0.1', flags=INET_PTON) == 2130706433


@pytest.mark.parametrize(
    ('address', 'flags', 'valid'),
    [
        ['', 0, False],
        ['192', 0, False],
        ['192', INET_ATON, True],
        ['127.0.0.1', 0, True],
    ],
)
def test_valid_str(address, flags, valid):
    assert ipv4.valid_str(address, flags) is valid


@pytest.mark.parametrize(
    'str_value',
    (
        [],
        (),
        {},
        True,
        False,
        192,
    ),
)
def test_valid_str_unexpected_types(str_value):
    with pytest.raises(TypeError):
        ipv4.valid_str(str_value)
