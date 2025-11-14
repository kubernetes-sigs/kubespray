import platform

import pytest

from netaddr import AddrFormatError
from netaddr.strategy import ipv6
from netaddr.tests import IS_MUSL


def test_strategy_ipv6():
    b = '0000000000000000:0000000000000000:0000000000000000:0000000000000000:0000000000000000:0000000000000000:1111111111111111:1111111111111110'
    i = 4294967294
    t = (0, 0, 0, 0, 0, 0, 0xFFFF, 0xFFFE)
    s = '::255.255.255.254'
    p = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff\xff\xfe'

    assert ipv6.bits_to_int(b) == i
    assert ipv6.int_to_bits(i) == b

    # musl renders IPv4-compatible IPv6 addresses like any other IPv6 address.
    assert ipv6.int_to_str(i) == s if not IS_MUSL else '::ffff:fffe'
    assert ipv6.str_to_int(s) == i

    assert ipv6.int_to_words(i) == t
    assert ipv6.words_to_int(t) == i
    assert ipv6.words_to_int(list(t)) == i

    assert ipv6.int_to_packed(i) == p
    assert ipv6.packed_to_int(p) == 4294967294


@pytest.mark.parametrize(
    'str_value',
    (
        '2001:0db8:0000:0000:0000:0000:1428:57ab',
        '2001:0db8:0000:0000:0000::1428:57ab',
        '2001:0db8:0:0:0:0:1428:57ab',
        '2001:0db8:0:0::1428:57ab',
        '2001:0db8::1428:57ab',
        '2001:0DB8:0000:0000:0000:0000:1428:57AB',
        '2001:DB8::1428:57AB',
    ),
)
def test_strategy_ipv6_equivalent_variants(str_value):
    assert ipv6.str_to_int(str_value) == 42540766411282592856903984951992014763


@pytest.mark.parametrize(
    'str_value',
    (
        #   Long forms.
        'FEDC:BA98:7654:3210:FEDC:BA98:7654:3210',
        '1080:0:0:0:8:800:200C:417A',  #   a unicast address
        'FF01:0:0:0:0:0:0:43',  #   a multicast address
        '0:0:0:0:0:0:0:1',  #   the loopback address
        '0:0:0:0:0:0:0:0',  #   the unspecified addresses
        #   Short forms.
        '1080::8:800:200C:417A',  #   a unicast address
        'FF01::43',  #   a multicast address
        '::1',  #   the loopback address
        '::',  #   the unspecified addresses
        #   IPv4 compatible forms.
        '::192.0.2.1',
        '::ffff:192.0.2.1',
        '0:0:0:0:0:0:192.0.2.1',
        '0:0:0:0:0:FFFF:192.0.2.1',
        '0:0:0:0:0:0:13.1.68.3',
        '0:0:0:0:0:FFFF:129.144.52.38',
        '::13.1.68.3',
        '::FFFF:129.144.52.38',
        #   Other tests.
        '1::',
        '::ffff',
        'ffff::',
        'ffff::ffff',
        '0:1:2:3:4:5:6:7',
        '8:9:a:b:c:d:e:f',
        '0:0:0:0:0:0:0:0',
        'ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff',
    ),
)
def test_strategy_ipv6_valid_str(str_value):
    assert ipv6.valid_str(str_value)


@pytest.mark.parametrize(
    'str_value',
    (
        '',
        'g:h:i:j:k:l:m:n',  # bad chars.
        '0:0:0:0:0:0:0:0:0',  # too long,
    ),
)
def test_strategy_ipv6_is_not_valid_str(str_value):
    assert not ipv6.valid_str(str_value)


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
        ipv6.valid_str(str_value)


@pytest.mark.parametrize(
    ('long_form', 'short_form'),
    (
        ('FEDC:BA98:7654:3210:FEDC:BA98:7654:3210', 'fedc:ba98:7654:3210:fedc:ba98:7654:3210'),
        ('1080:0:0:0:8:800:200C:417A', '1080::8:800:200c:417a'),  # unicast address
        ('FF01:0:0:0:0:0:0:43', 'ff01::43'),  # multicast address
        ('0:0:0:0:0:0:0:1', '::1'),  # loopback address
        ('0:0:0:0:0:0:0:0', '::'),  # unspecified addresses
    ),
)
def test_strategy_ipv6_string_compaction(long_form, short_form):
    int_val = ipv6.str_to_int(long_form)
    calc_short_form = ipv6.int_to_str(int_val)
    assert calc_short_form == short_form


def test_strategy_ipv6_mapped_and_compatible_ipv4_string_formatting():
    # musl renders IPv4-compatible IPv6 addresses like any other IPv6 address.
    assert ipv6.int_to_str(0xFFFFFF) == '::0.255.255.255' if not IS_MUSL else '::ff:ffff'
    assert ipv6.int_to_str(0xFFFFFFFF) == '::255.255.255.255' if not IS_MUSL else '::ffff:ffff'

    assert ipv6.int_to_str(0x1FFFFFFFF) == '::1:ffff:ffff'
    assert ipv6.int_to_str(0xFFFFFFFFFFFF) == '::ffff:255.255.255.255'
    assert ipv6.int_to_str(0xFFFEFFFFFFFF) == '::fffe:ffff:ffff'
    assert ipv6.int_to_str(0xFFFFFFFFFFFF) == '::ffff:255.255.255.255'
    assert ipv6.int_to_str(0xFFFFFFFFFFF1) == '::ffff:255.255.255.241'
    assert ipv6.int_to_str(0xFFFFFFFFFFFE) == '::ffff:255.255.255.254'
    assert ipv6.int_to_str(0xFFFFFFFFFF00) == '::ffff:255.255.255.0'
    assert ipv6.int_to_str(0xFFFFFFFF0000) == '::ffff:255.255.0.0'
    assert ipv6.int_to_str(0xFFFFFF000000) == '::ffff:255.0.0.0'
    assert ipv6.int_to_str(0xFFFF000000) == '::ff:ff00:0'
    assert ipv6.int_to_str(0x1FFFF00000000) == '::1:ffff:0:0'
    # So this is strange. Even though on Windows we get decimal notation in a lot of the addresses above,
    # in case of 0.0.0.0 we get hex instead. Worth investigating, putting
    # the conditional assert here for now to make this visible.
    if platform.system() == 'Windows':
        assert ipv6.int_to_str(0xFFFF00000000) == '::ffff:0:0'
    else:
        assert ipv6.int_to_str(0xFFFF00000000) == '::ffff:0.0.0.0'


def test_strategy_ipv6_str_to_int_behaviour_legacy_mode():
    assert ipv6.str_to_int('::127') == 295

    with pytest.raises(AddrFormatError):
        ipv6.str_to_int('::0x7f')

    assert ipv6.str_to_int('::0177') == 375

    with pytest.raises(AddrFormatError):
        ipv6.str_to_int('::127.1')

    with pytest.raises(AddrFormatError):
        ipv6.str_to_int('::0x7f.1')

    with pytest.raises(AddrFormatError):
        ipv6.str_to_int('::0177.1')

    assert ipv6.str_to_int('::127.0.0.1') == 2130706433
