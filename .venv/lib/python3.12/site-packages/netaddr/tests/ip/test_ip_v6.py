import pickle
import pytest
from netaddr import IPAddress, IPNetwork, ZEROFILL


def test_ipaddress_v6():
    ip = IPAddress('fe80::dead:beef')
    assert ip.version == 6
    assert repr(ip) == "IPAddress('fe80::dead:beef')"
    assert str(ip) == 'fe80::dead:beef'
    assert ip.format() == 'fe80::dead:beef'
    assert int(ip) == 338288524927261089654018896845083623151
    assert hex(ip) == '0xfe8000000000000000000000deadbeef'
    assert bytes(ip) == b'\xfe\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xde\xad\xbe\xef'
    assert (
        ip.bin
        == '0b11111110100000000000000000000000000000000000000000000000000000000000000000000000000000000000000011011110101011011011111011101111'
    )
    assert (
        ip.bits()
        == '1111111010000000:0000000000000000:0000000000000000:0000000000000000:0000000000000000:0000000000000000:1101111010101101:1011111011101111'
    )
    assert ip.words == (65152, 0, 0, 0, 0, 0, 57005, 48879)


@pytest.mark.parametrize(
    ('value', 'ipaddr', 'network', 'cidr', 'broadcast', 'netmask', 'hostmask', 'size'),
    [
        (
            'fe80::dead:beef/64',
            IPAddress('fe80::dead:beef'),
            IPAddress('fe80::'),
            IPNetwork('fe80::/64'),
            IPAddress('fe80::ffff:ffff:ffff:ffff'),
            IPAddress('ffff:ffff:ffff:ffff::'),
            IPAddress('::ffff:ffff:ffff:ffff'),
            18446744073709551616,
        ),
    ],
)
def test_ipnetwork_v6(value, ipaddr, network, cidr, broadcast, netmask, hostmask, size):
    net = IPNetwork(value)
    assert net.ip == ipaddr
    assert net.network == network
    assert net.cidr == cidr
    assert net.broadcast == broadcast
    assert net.netmask == netmask
    assert net.hostmask == hostmask
    assert net.size == size


def test_iterhosts_v6():
    assert list(IPNetwork('::ffff:192.0.2.0/125').iter_hosts()) == [
        IPAddress('::ffff:192.0.2.1'),
        IPAddress('::ffff:192.0.2.2'),
        IPAddress('::ffff:192.0.2.3'),
        IPAddress('::ffff:192.0.2.4'),
        IPAddress('::ffff:192.0.2.5'),
        IPAddress('::ffff:192.0.2.6'),
        IPAddress('::ffff:192.0.2.7'),
    ]


def test_ipnetwork_boolean_evaluation_v6():
    assert bool(IPNetwork('::/0'))


def test_ipnetwork_slice_v6():
    ip = IPNetwork('fe80::/10')
    assert ip[0] == IPAddress('fe80::')
    assert ip[-1] == IPAddress('febf:ffff:ffff:ffff:ffff:ffff:ffff:ffff')
    assert ip.size == 332306998946228968225951765070086144

    with pytest.raises(TypeError):
        list(ip[0:5:1])


def test_ip_network_membership_v6():
    for what, network, result in [
        (IPAddress('ffff::1'), IPNetwork('ffff::/127'), True),
        (IPNetwork('ffff::/127'), IPNetwork('ffff::/127'), True),
        (IPNetwork('fe80::/10'), IPNetwork('ffff::/127'), False),
    ]:
        assert (what in network) is result
        assert (str(what) in network) is result


def test_ip_network_equality_v6():
    assert IPNetwork('fe80::/10') == IPNetwork('fe80::/10')
    assert IPNetwork('fe80::/10') is not IPNetwork('fe80::/10')

    assert not IPNetwork('fe80::/10') != IPNetwork('fe80::/10')
    assert not IPNetwork('fe80::/10') is IPNetwork('fe80::/10')


def test_ipnetwork_constructor_v6():
    assert IPNetwork(IPNetwork('::192.0.2.0/120')) == IPNetwork('::192.0.2.0/120')
    assert IPNetwork('::192.0.2.0/120') == IPNetwork('::192.0.2.0/120')
    assert IPNetwork('::192.0.2.0/120', 6) == IPNetwork('::192.0.2.0/120')


def test_ipaddress_netmask_v6():
    assert IPAddress('::').netmask_bits() == 0
    assert IPAddress('8000::').netmask_bits() == 1
    assert IPAddress('ffff:ffff:ffff:ffff::').netmask_bits() == 64
    assert IPAddress('ffff:ffff:ffff:ffff:ffff:ffff:ffff::').netmask_bits() == 112
    assert IPAddress('ffff:ffff:ffff:ffff:ffff:ffff:ffff:fffe').netmask_bits() == 127
    assert IPAddress('ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff').netmask_bits() == 128

    assert IPAddress('fe80::1').netmask_bits() == 128


def test_objects_use_slots():
    assert not hasattr(IPNetwork('::/64'), '__dict__')
    assert not hasattr(IPAddress('::'), '__dict__')


def test_ipaddress_pickling_v6():
    ip = IPAddress('::ffff:192.0.2.1')
    assert ip == IPAddress('::ffff:192.0.2.1')

    assert ip.value == 281473902969345

    buf = pickle.dumps(ip)
    ip2 = pickle.loads(buf)
    assert ip2 == ip
    assert ip2.value == 281473902969345
    assert ip2.version == 6


def test_ipnetwork_pickling_v6():
    cidr = IPNetwork('::ffff:192.0.2.0/120')
    assert cidr == IPNetwork('::ffff:192.0.2.0/120')
    assert cidr.value == 281473902969344
    assert cidr.prefixlen == 120

    buf = pickle.dumps(cidr)
    cidr2 = pickle.loads(buf)

    assert cidr2 == cidr
    assert cidr2.value == 281473902969344
    assert cidr2.prefixlen == 120
    assert cidr2.version == 6


def test_ipv6_unicast_address_allocation_info():
    ip = IPNetwork('2001:1200::/23')

    assert ip.info.IPv6[0].allocation == 'Global Unicast'
    assert ip.info.IPv6[0].prefix == '2000::/3'
    assert ip.info.IPv6[0].reference == 'rfc4291'

    assert ip.info.IPv6_unicast[0].prefix == '2001:1200::/23'
    assert ip.info.IPv6_unicast[0].description == 'LACNIC'
    assert ip.info.IPv6_unicast[0].whois == 'whois.lacnic.net'
    assert ip.info.IPv6_unicast[0].status == 'ALLOCATED'


def test_rfc6164_subnets():
    # Tests for /127 subnet
    assert list(IPNetwork('1234::/127')) == [
        IPAddress('1234::'),
        IPAddress('1234::1'),
    ]
    assert list(IPNetwork('1234::/127').iter_hosts()) == [
        IPAddress('1234::'),
        IPAddress('1234::1'),
    ]
    assert IPNetwork('1234::/127').network == IPAddress('1234::')
    assert IPNetwork('1234::').broadcast is None

    # Tests for /128 subnet
    assert IPNetwork('1234::/128').network == IPAddress('1234::')
    assert IPNetwork('1234::/128').broadcast is None
    assert list(IPNetwork('1234::/128')) == [IPAddress('1234::')]
    assert list(IPNetwork('1234::/128').iter_hosts()) == [IPAddress('1234::')]


def test_ipaddress_ignores_zerofill_when_parsing_ipv6():
    assert IPAddress('fe80::', flags=ZEROFILL)
