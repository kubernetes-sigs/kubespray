import pickle
import types
import random

import pytest

from netaddr import (
    IPAddress,
    IPNetwork,
    INET_ATON,
    INET_PTON,
    spanning_cidr,
    AddrFormatError,
    ZEROFILL,
    NOHOST,
)


def test_ipaddress_v4():
    ip = IPAddress('192.0.2.1')
    assert ip.version == 4
    assert repr(ip) == "IPAddress('192.0.2.1')"
    assert str(ip) == '192.0.2.1'
    assert ip.format() == '192.0.2.1'
    assert int(ip) == 3221225985
    assert hex(ip) == '0xc0000201'
    assert bytes(ip) == b'\xc0\x00\x02\x01'
    assert ip.bin == '0b11000000000000000000001000000001'
    assert ip.bits() == '11000000.00000000.00000010.00000001'
    assert ip.words == (192, 0, 2, 1)


@pytest.mark.parametrize(
    ('value', 'ipaddr', 'network', 'cidr', 'broadcast', 'netmask', 'hostmask', 'size'),
    [
        (
            '192.0.2.1',
            IPAddress('192.0.2.1'),
            IPAddress('192.0.2.1'),
            IPNetwork('192.0.2.1/32'),
            None,
            IPAddress('255.255.255.255'),
            IPAddress('0.0.0.0'),
            1,
        ),
        (
            '192.0.2.0/24',
            IPAddress('192.0.2.0'),
            IPAddress('192.0.2.0'),
            IPNetwork('192.0.2.0/24'),
            IPAddress('192.0.2.255'),
            IPAddress('255.255.255.0'),
            IPAddress('0.0.0.255'),
            256,
        ),
        (
            '192.0.3.112/22',
            IPAddress('192.0.3.112'),
            IPAddress('192.0.0.0'),
            IPNetwork('192.0.0.0/22'),
            IPAddress('192.0.3.255'),
            IPAddress('255.255.252.0'),
            IPAddress('0.0.3.255'),
            1024,
        ),
    ],
)
def test_ipnetwork_v4(value, ipaddr, network, cidr, broadcast, netmask, hostmask, size):
    net = IPNetwork(value)
    assert net.ip == ipaddr
    assert net.network == network
    assert net.cidr == cidr
    assert net.broadcast == broadcast
    assert net.netmask == netmask
    assert net.hostmask == hostmask
    assert net.size == size


def test_ipnetwork_list_operations_v4():
    ip = IPNetwork('192.0.2.16/29')
    assert len(ip) == 8

    ip_list = list(ip)
    assert len(ip_list) == 8

    assert ip_list == [
        IPAddress('192.0.2.16'),
        IPAddress('192.0.2.17'),
        IPAddress('192.0.2.18'),
        IPAddress('192.0.2.19'),
        IPAddress('192.0.2.20'),
        IPAddress('192.0.2.21'),
        IPAddress('192.0.2.22'),
        IPAddress('192.0.2.23'),
    ]


def test_ipnetwork_index_operations_v4():
    ip = IPNetwork('192.0.2.16/29')
    assert ip[0] == IPAddress('192.0.2.16')
    assert ip[1] == IPAddress('192.0.2.17')
    assert ip[-1] == IPAddress('192.0.2.23')


@pytest.mark.parametrize(
    ['start', 'stop', 'step'],
    [
        [None, None, -1],
        [-1, 0, -2],
        [-1, None, -1],
        [-1, None, -3],
        [0, None, 4],
        [0, -1, None],
        [0, 4, None],
        [1, None, 4],
        [1, 4, 2],
    ],
)
def test_ipnetwork_slice_operations_v4(start, stop, step):
    ip = IPNetwork('192.0.2.16/29')
    result = ip[start:stop:step]
    assert isinstance(result, types.GeneratorType)
    assert list(result) == list(ip)[start:stop:step]


def test_ipnetwork_sort_order():
    ip_list = list(IPNetwork('192.0.2.128/28'))
    random.shuffle(ip_list)
    assert sorted(ip_list) == [
        IPAddress('192.0.2.128'),
        IPAddress('192.0.2.129'),
        IPAddress('192.0.2.130'),
        IPAddress('192.0.2.131'),
        IPAddress('192.0.2.132'),
        IPAddress('192.0.2.133'),
        IPAddress('192.0.2.134'),
        IPAddress('192.0.2.135'),
        IPAddress('192.0.2.136'),
        IPAddress('192.0.2.137'),
        IPAddress('192.0.2.138'),
        IPAddress('192.0.2.139'),
        IPAddress('192.0.2.140'),
        IPAddress('192.0.2.141'),
        IPAddress('192.0.2.142'),
        IPAddress('192.0.2.143'),
    ]


def test_ipaddress_and_ipnetwork_canonical_sort_order_by_version():
    ip_list = [
        IPAddress('192.0.2.130'),
        IPNetwork('192.0.2.128/28'),
        IPAddress('::'),
        IPNetwork('192.0.3.0/24'),
        IPNetwork('192.0.2.0/24'),
        IPNetwork('fe80::/64'),
        IPAddress('10.0.0.1'),
    ]

    random.shuffle(ip_list)
    ip_list.sort()

    assert ip_list == [
        IPAddress('10.0.0.1'),
        IPNetwork('192.0.2.0/24'),
        IPNetwork('192.0.2.128/28'),
        IPAddress('192.0.2.130'),
        IPNetwork('192.0.3.0/24'),
        IPAddress('::'),
        IPNetwork('fe80::/64'),
    ]


def test_ipnetwork_v4_constructor():
    assert IPNetwork('192.168.0.15') == IPNetwork('192.168.0.15/32')


def test_ipaddress_integer_operations_v4():
    assert IPAddress('192.0.2.0') + 1 == IPAddress('192.0.2.1')
    assert 1 + IPAddress('192.0.2.0') == IPAddress('192.0.2.1')
    assert IPAddress('192.0.2.1') - 1 == IPAddress('192.0.2.0')
    assert IPAddress('192.0.0.0') + IPAddress('0.0.0.42') == IPAddress('192.0.0.42')
    assert IPAddress('192.0.0.42') - IPAddress('0.0.0.42') == IPAddress('192.0.0.0')

    with pytest.raises(IndexError):
        1 - IPAddress('192.0.2.1')

    ip = IPAddress('10.0.0.1')
    ip += 1
    assert ip == IPAddress('10.0.0.2')

    ip -= 1
    assert ip == IPAddress('10.0.0.1')

    ip += IPAddress('0.0.0.42')
    assert ip == IPAddress('10.0.0.43')

    ip -= IPAddress('0.0.0.43')
    assert ip == IPAddress('10.0.0.0')

    #   Negative increments around address range boundaries.
    ip = IPAddress('0.0.0.0')
    with pytest.raises(IndexError):
        ip += -1

    ip = IPAddress('255.255.255.255')
    with pytest.raises(IndexError):
        ip -= -1


def test_ipaddress_binary_operations_v4():
    assert IPAddress('192.0.2.15') & IPAddress('255.255.255.0') == IPAddress('192.0.2.0')
    assert IPAddress('255.255.0.0') | IPAddress('0.0.255.255') == IPAddress('255.255.255.255')
    assert IPAddress('255.255.0.0') ^ IPAddress('255.0.0.0') == IPAddress('0.255.0.0')
    assert IPAddress('1.2.3.4').packed == '\x01\x02\x03\x04'.encode('ascii')


def test_iterhosts_v4():
    assert list(IPNetwork('192.0.2.0/29').iter_hosts()) == [
        IPAddress('192.0.2.1'),
        IPAddress('192.0.2.2'),
        IPAddress('192.0.2.3'),
        IPAddress('192.0.2.4'),
        IPAddress('192.0.2.5'),
        IPAddress('192.0.2.6'),
    ]

    assert list(IPNetwork('192.168.0.0/31')) == [
        IPAddress('192.168.0.0'),
        IPAddress('192.168.0.1'),
    ]

    assert list(IPNetwork('192.168.0.0/31').iter_hosts()) == [
        IPAddress('192.168.0.0'),
        IPAddress('192.168.0.1'),
    ]
    assert list(IPNetwork('192.168.0.0/32').iter_hosts()) == [IPAddress('192.168.0.0')]


def test_ipaddress_boolean_evaluation_v4():
    assert not bool(IPAddress('0.0.0.0'))
    assert bool(IPAddress('0.0.0.1'))
    assert bool(IPAddress('255.255.255.255'))


def test_ipnetwork_boolean_evaluation_v4():
    assert bool(IPNetwork('0.0.0.0/0'))


def test_ipnetwork_equality_v4():
    assert IPNetwork('192.0.2.0/255.255.254.0') == IPNetwork('192.0.2.0/23')
    assert IPNetwork('192.0.2.65/255.255.254.0') == IPNetwork('192.0.2.0/23')
    assert IPNetwork('192.0.2.65/255.255.254.0') == IPNetwork('192.0.2.65/23')
    assert IPNetwork('192.0.2.65/255.255.255.0') != IPNetwork('192.0.2.0/23')
    assert IPNetwork('192.0.2.65/255.255.254.0') != IPNetwork('192.0.2.65/24')


def test_ip_network_membership_v4():
    for what, network, result in [
        (IPAddress('192.0.2.1'), IPNetwork('192.0.2.0/24'), True),
        (IPAddress('192.0.2.255'), IPNetwork('192.0.2.0/24'), True),
        (IPNetwork('192.0.2.0/24'), IPNetwork('192.0.2.0/23'), True),
        (IPNetwork('192.0.2.0/24'), IPNetwork('192.0.2.0/24'), True),
        (IPNetwork('192.0.2.0/23'), IPNetwork('192.0.2.0/24'), False),
    ]:
        assert (what in network) is result
        assert (str(what) in network) is result


def test_ip_network_equality_v4():
    assert IPNetwork('192.0.2.0/24') == IPNetwork('192.0.2.0/24')
    assert IPNetwork('192.0.2.0/24') is not IPNetwork('192.0.2.0/24')

    assert not IPNetwork('192.0.2.0/24') != IPNetwork('192.0.2.0/24')
    assert not IPNetwork('192.0.2.0/24') is IPNetwork('192.0.2.0/24')


def test_ipaddress_integer_constructor_v4():
    assert IPAddress(1) == IPAddress('0.0.0.1')
    assert IPAddress(1, 4) == IPAddress('0.0.0.1')
    assert IPAddress(1, 6) == IPAddress('::1')
    assert IPAddress(10) == IPAddress('0.0.0.10')


def test_ipaddress_integer_constructor_v6():
    assert IPAddress(0x1FFFFFFFF) == IPAddress('::1:ffff:ffff')
    assert IPAddress(0xFFFFFFFF, 6) == IPAddress('::255.255.255.255')
    assert IPAddress(0x1FFFFFFFF) == IPAddress('::1:ffff:ffff')
    assert IPAddress(2**128 - 1) == IPAddress('ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff')


def test_ipaddress_inet_aton_constructor_v4():
    assert IPAddress('0x7f.0x1', flags=INET_ATON) == IPAddress('127.0.0.1')
    assert IPAddress('0x7f.0x0.0x0.0x1', flags=INET_ATON) == IPAddress('127.0.0.1')
    assert IPAddress('0177.01', flags=INET_ATON) == IPAddress('127.0.0.1')
    assert IPAddress('0x7f.0.01', flags=INET_ATON) == IPAddress('127.0.0.1')

    # Partial addresses - pretty weird, but valid ...
    assert IPAddress('127', flags=INET_ATON) == IPAddress('0.0.0.127')
    assert IPAddress('127', flags=INET_ATON) == IPAddress('0.0.0.127')
    assert IPAddress('127.1', flags=INET_ATON) == IPAddress('127.0.0.1')
    assert IPAddress('127.0.1', flags=INET_ATON) == IPAddress('127.0.0.1')


@pytest.mark.parametrize(
    'address',
    [
        '0177.01',
        '0x7f.0.01',
        '10',
        '10.1',
        '10.0.1',
        '010.0.0.1',
        '10.01.0.1',
        '10.0.00.1',
        '10.0.1.01',
    ],
)
def test_ipaddress_inet_pton_constructor_v4_rejects_invalid_input(address):
    with pytest.raises(AddrFormatError):
        IPAddress(address, flags=INET_PTON)

    with pytest.raises(AddrFormatError):
        IPAddress(address)


def test_ipaddress_inet_pton_constructor_v4_accepts_valid_input():
    assert IPAddress('10.0.0.1', flags=INET_PTON) == IPAddress('10.0.0.1')


def test_ipaddress_constructor_zero_filled_octets_v4():
    assert IPAddress('010.000.000.001', flags=INET_ATON) == IPAddress('8.0.0.1')
    assert IPAddress('010.000.000.001', flags=INET_ATON | ZEROFILL) == IPAddress('10.0.0.1')
    assert IPAddress('010.000.001', flags=INET_ATON | ZEROFILL) == IPAddress('10.0.0.1')

    with pytest.raises(AddrFormatError):
        assert IPAddress('010.000.001', flags=ZEROFILL)

    with pytest.raises(AddrFormatError):
        assert IPAddress('010.000.001', flags=INET_PTON | ZEROFILL)

    assert IPAddress('010.000.000.001', flags=INET_PTON | ZEROFILL) == IPAddress('10.0.0.1')


def test_ipnetwork_constructor_v4():
    assert IPNetwork('192.0.2.0/24') == IPNetwork('192.0.2.0/24')
    assert IPNetwork('192.0.2.0/255.255.255.0') == IPNetwork('192.0.2.0/24')
    assert IPNetwork('192.0.2.0/0.0.0.255') == IPNetwork('192.0.2.0/24')
    assert IPNetwork(IPNetwork('192.0.2.0/24')) == IPNetwork('192.0.2.0/24')
    assert IPNetwork(IPNetwork('192.0.2.0/24')) == IPNetwork('192.0.2.0/24')


def test_ipnetwork_bad_string_constructor():
    with pytest.raises(AddrFormatError):
        IPNetwork('foo')


def test_ipnetwork_expand_partial_v4():
    with pytest.raises(AddrFormatError):
        IPNetwork('10/8')
    assert IPNetwork('10/8', expand_partial=True) == IPNetwork('10.0.0.0/8')
    assert IPNetwork('10.20/16', expand_partial=True) == IPNetwork('10.20.0.0/16')
    assert IPNetwork('10.20.30/24', expand_partial=True) == IPNetwork('10.20.30.0/24')


def test_ipaddress_netmask_v4():
    assert IPAddress('0.0.0.0').netmask_bits() == 0
    assert IPAddress('128.0.0.0').netmask_bits() == 1
    assert IPAddress('255.0.0.0').netmask_bits() == 8
    assert IPAddress('255.255.0.0').netmask_bits() == 16
    assert IPAddress('255.255.255.0').netmask_bits() == 24
    assert IPAddress('255.255.255.254').netmask_bits() == 31
    assert IPAddress('255.255.255.255').netmask_bits() == 32

    assert IPAddress('1.1.1.1').netmask_bits() == 32


def test_ipaddress_hex_format():
    assert hex(IPAddress(0)) == '0x0'
    assert hex(IPAddress(0xFFFFFFFF)) == '0xffffffff'


def test_ipaddress_oct_format():
    assert oct(IPAddress(0xFFFFFFFF)) == '0o37777777777'
    assert oct(IPAddress(0)) == '0o0'


def test_multicast_info():
    ip = IPAddress('224.0.1.173')
    assert ip.info.IPv4[0].designation == 'Multicast'
    assert ip.info.IPv4[0].prefix == '224/8'
    assert ip.info.IPv4[0].status == 'Reserved'
    assert ip.info.Multicast[0].address == '224.0.1.173'


def test_ipaddress_pickling_v4():
    ip = IPAddress(3221225985)
    assert ip == IPAddress('192.0.2.1')

    buf = pickle.dumps(ip)
    ip2 = pickle.loads(buf)

    assert ip2 == ip
    assert id(ip2) != id(ip)
    assert ip2.value == 3221225985
    assert ip2.version == 4


def test_ipnetwork_pickling_v4():
    cidr = IPNetwork('192.0.2.0/24')
    assert cidr == IPNetwork('192.0.2.0/24')

    buf = pickle.dumps(cidr)
    cidr2 = pickle.loads(buf)

    assert cidr2 == cidr
    assert id(cidr2) != id(cidr)
    assert cidr2.value == 3221225984
    assert cidr2.prefixlen == 24
    assert cidr2.version == 4


def test_ipnetwork_incrementing_by_int():
    ip = IPNetwork('192.0.2.0/28')
    results = []
    for i in range(16):
        results.append(str(ip))
        ip += 1

    assert results == [
        '192.0.2.0/28',
        '192.0.2.16/28',
        '192.0.2.32/28',
        '192.0.2.48/28',
        '192.0.2.64/28',
        '192.0.2.80/28',
        '192.0.2.96/28',
        '192.0.2.112/28',
        '192.0.2.128/28',
        '192.0.2.144/28',
        '192.0.2.160/28',
        '192.0.2.176/28',
        '192.0.2.192/28',
        '192.0.2.208/28',
        '192.0.2.224/28',
        '192.0.2.240/28',
    ]


def test_rfc3021_subnets():
    # Tests for /31 subnet
    assert IPNetwork('192.0.2.0/31').network == IPAddress('192.0.2.0')
    assert IPNetwork('192.0.2.0/31').broadcast is None
    assert list(IPNetwork('192.0.2.0/31').iter_hosts()) == [
        IPAddress('192.0.2.0'),
        IPAddress('192.0.2.1'),
    ]

    # Tests for /32 subnet
    assert IPNetwork('192.0.2.0/32').network == IPAddress('192.0.2.0')
    assert IPNetwork('192.0.2.0/32').broadcast is None
    assert list(IPNetwork('192.0.2.0/32').iter_hosts()) == [IPAddress('192.0.2.0')]


def test_ipnetwork_change_prefixlen():
    ip = IPNetwork('192.168.0.0/16')
    assert ip.prefixlen == 16
    ip.prefixlen = 8
    assert ip.prefixlen == 8

    ip = IPNetwork('dead:beef::/16')
    assert ip.prefixlen == 16
    ip.prefixlen = 64
    assert ip.prefixlen == 64


def test_ipnetwork_change_netmask():
    ip = IPNetwork('192.168.0.0/16')
    ip.netmask = '255.0.0.0'
    assert ip.prefixlen == 8

    ip = IPNetwork('dead:beef::/16')
    ip.netmask = 'ffff:ffff:ffff:ffff::'
    assert ip.prefixlen == 64


def test_spanning_cidr_handles_strings():
    # This that a regression introduced in 0fda41a is fixed. The regression caused an error when str
    # addresses were passed to the function.
    addresses = [
        IPAddress('10.0.0.1'),
        IPAddress('10.0.0.2'),
        '10.0.0.3',
        '10.0.0.4',
    ]
    assert spanning_cidr(addresses) == IPNetwork('10.0.0.0/29')
    assert spanning_cidr(reversed(addresses)) == IPNetwork('10.0.0.0/29')


def test_ipnetwork_nohost():
    assert IPNetwork(IPNetwork('192.168.0.1/24'), flags=NOHOST).ip == IPAddress('192.168.0.0')
