from ast import literal_eval
import pickle
import sys
import sys
import pytest

from netaddr import (
    iter_iprange,
    IPAddress,
    cidr_merge,
    IPNetwork,
    IPRange,
    ZEROFILL,
    AddrFormatError,
)


def test_ip_range():
    ip_list = list(iter_iprange('192.0.2.1', '192.0.2.14'))

    assert len(ip_list) == 14

    assert ip_list == [
        IPAddress('192.0.2.1'),
        IPAddress('192.0.2.2'),
        IPAddress('192.0.2.3'),
        IPAddress('192.0.2.4'),
        IPAddress('192.0.2.5'),
        IPAddress('192.0.2.6'),
        IPAddress('192.0.2.7'),
        IPAddress('192.0.2.8'),
        IPAddress('192.0.2.9'),
        IPAddress('192.0.2.10'),
        IPAddress('192.0.2.11'),
        IPAddress('192.0.2.12'),
        IPAddress('192.0.2.13'),
        IPAddress('192.0.2.14'),
    ]

    assert cidr_merge(ip_list) == [
        IPNetwork('192.0.2.1/32'),
        IPNetwork('192.0.2.2/31'),
        IPNetwork('192.0.2.4/30'),
        IPNetwork('192.0.2.8/30'),
        IPNetwork('192.0.2.12/31'),
        IPNetwork('192.0.2.14/32'),
    ]


def test_iprange():
    range1 = IPRange('192.0.2.1', '192.0.2.15')
    assert range1 == IPRange('192.0.2.1', '192.0.2.15')

    assert range1.cidrs() == [
        IPNetwork('192.0.2.1/32'),
        IPNetwork('192.0.2.2/31'),
        IPNetwork('192.0.2.4/30'),
        IPNetwork('192.0.2.8/29'),
    ]

    assert IPRange('192.0.2.0', '192.0.2.255') == IPNetwork('192.0.2.0/24')

    range2 = IPRange('192.0.2.1', '192.0.2.15')
    addrs = list(range2)

    assert addrs == [
        IPAddress('192.0.2.1'),
        IPAddress('192.0.2.2'),
        IPAddress('192.0.2.3'),
        IPAddress('192.0.2.4'),
        IPAddress('192.0.2.5'),
        IPAddress('192.0.2.6'),
        IPAddress('192.0.2.7'),
        IPAddress('192.0.2.8'),
        IPAddress('192.0.2.9'),
        IPAddress('192.0.2.10'),
        IPAddress('192.0.2.11'),
        IPAddress('192.0.2.12'),
        IPAddress('192.0.2.13'),
        IPAddress('192.0.2.14'),
        IPAddress('192.0.2.15'),
    ]
    assert range2 != addrs

    assert list(range2) == addrs

    subnets = range2.cidrs()
    assert subnets == [
        IPNetwork('192.0.2.1/32'),
        IPNetwork('192.0.2.2/31'),
        IPNetwork('192.0.2.4/30'),
        IPNetwork('192.0.2.8/29'),
    ]

    assert range2 != subnets

    assert range2.cidrs() == subnets


def test_iprange_boundaries():
    assert list(iter_iprange('192.0.2.0', '192.0.2.7')) == [
        IPAddress('192.0.2.0'),
        IPAddress('192.0.2.1'),
        IPAddress('192.0.2.2'),
        IPAddress('192.0.2.3'),
        IPAddress('192.0.2.4'),
        IPAddress('192.0.2.5'),
        IPAddress('192.0.2.6'),
        IPAddress('192.0.2.7'),
    ]

    assert list(iter_iprange('::ffff:192.0.2.0', '::ffff:192.0.2.7')) == [
        IPAddress('::ffff:192.0.2.0'),
        IPAddress('::ffff:192.0.2.1'),
        IPAddress('::ffff:192.0.2.2'),
        IPAddress('::ffff:192.0.2.3'),
        IPAddress('::ffff:192.0.2.4'),
        IPAddress('::ffff:192.0.2.5'),
        IPAddress('::ffff:192.0.2.6'),
        IPAddress('::ffff:192.0.2.7'),
    ]


def test_iprange_boolean_evaluation():
    assert bool(IPRange('0.0.0.0', '255.255.255.255'))
    assert bool(IPRange('0.0.0.0', '0.0.0.0'))


def test_iprange_sorting():
    ranges = (
        (IPAddress('::'), IPAddress('::')),
        (IPAddress('0.0.0.0'), IPAddress('255.255.255.255')),
        (IPAddress('::'), IPAddress('::255.255.255.255')),
        (IPAddress('0.0.0.0'), IPAddress('0.0.0.0')),
    )

    assert sorted(ranges) == [
        (IPAddress('0.0.0.0'), IPAddress('0.0.0.0')),
        (IPAddress('0.0.0.0'), IPAddress('255.255.255.255')),
        (IPAddress('::'), IPAddress('::')),
        (IPAddress('::'), IPAddress('::255.255.255.255')),
    ]


def test_iprange_constructor():
    iprange = IPRange('192.0.2.1', '192.0.2.254')

    assert iprange == IPRange('192.0.2.1', '192.0.2.254')
    assert '%s' % iprange == '192.0.2.1-192.0.2.254'
    assert IPRange('::ffff:192.0.2.1', '::ffff:192.0.2.254') == IPRange(
        '::ffff:192.0.2.1', '::ffff:192.0.2.254'
    )
    assert IPRange('192.0.2.1', '192.0.2.1') == IPRange('192.0.2.1', '192.0.2.1')
    assert IPRange('208.049.164.000', '208.050.066.255', flags=ZEROFILL) == IPRange(
        '208.49.164.0', '208.50.66.255'
    )

    with pytest.raises(AddrFormatError):
        IPRange('192.0.2.2', '192.0.2.1')

    with pytest.raises(AddrFormatError):
        IPRange('::', '0.0.0.1')

    with pytest.raises(AddrFormatError):
        IPRange('0.0.0.0', '::1')


def test_iprange_indexing():
    iprange = IPRange('192.0.2.1', '192.0.2.254')

    assert len(iprange) == 254
    assert iprange.first == 3221225985
    assert iprange.last == 3221226238
    assert iprange[0] == IPAddress('192.0.2.1')
    assert iprange[-1] == IPAddress('192.0.2.254')

    with pytest.raises(IndexError):
        iprange[512]


def test_iprange_slicing():
    iprange = IPRange('192.0.2.1', '192.0.2.254')

    assert list(iprange[0:3]) == [
        IPAddress('192.0.2.1'),
        IPAddress('192.0.2.2'),
        IPAddress('192.0.2.3'),
    ]

    assert list(iprange[0:10:2]) == [
        IPAddress('192.0.2.1'),
        IPAddress('192.0.2.3'),
        IPAddress('192.0.2.5'),
        IPAddress('192.0.2.7'),
        IPAddress('192.0.2.9'),
    ]

    assert list(iprange[0:1024:512]) == [IPAddress('192.0.2.1')]


def test_iprange_ipv6_unsupported_slicing():
    with pytest.raises(TypeError):
        IPRange('::ffff:192.0.2.1', '::ffff:192.0.2.254')[0:10:2]


def test_iprange_membership():
    assert IPRange('192.0.2.5', '192.0.2.10') in IPRange('192.0.2.1', '192.0.2.254')
    assert IPRange('fe80::1', 'fe80::fffe') in IPRange('fe80::', 'fe80::ffff:ffff:ffff:ffff')
    assert IPRange('192.0.2.5', '192.0.2.10') not in IPRange('::', '::255.255.255.255')

    # Reported in https://github.com/netaddr/netaddr/issues/157
    net = IPNetwork('10.0.0.0/30')
    assert net in IPRange(net.first, net.last)


def test_more_iprange_sorting():
    ipranges = (
        IPRange('192.0.2.40', '192.0.2.50'),
        IPRange('192.0.2.20', '192.0.2.30'),
        IPRange('192.0.2.1', '192.0.2.254'),
    )

    assert sorted(ipranges) == [
        IPRange('192.0.2.1', '192.0.2.254'),
        IPRange('192.0.2.20', '192.0.2.30'),
        IPRange('192.0.2.40', '192.0.2.50'),
    ]

    ipranges = list(ipranges)
    ipranges.append(IPRange('192.0.2.45', '192.0.2.49'))

    assert sorted(ipranges) == [
        IPRange('192.0.2.1', '192.0.2.254'),
        IPRange('192.0.2.20', '192.0.2.30'),
        IPRange('192.0.2.40', '192.0.2.50'),
        IPRange('192.0.2.45', '192.0.2.49'),
    ]


def test_iprange_cidr_interoperability():
    assert IPRange('192.0.2.5', '192.0.2.10').cidrs() == [
        IPNetwork('192.0.2.5/32'),
        IPNetwork('192.0.2.6/31'),
        IPNetwork('192.0.2.8/31'),
        IPNetwork('192.0.2.10/32'),
    ]

    assert IPRange('fe80::', 'fe80::ffff:ffff:ffff:ffff').cidrs() == [IPNetwork('fe80::/64')]


def test_iprange_info_and_properties():
    iprange = IPRange('192.0.2.1', '192.0.2.254')

    assert literal_eval(str(iprange.info)) == {
        'IPv4': [
            {
                'date': '1993-05',
                'designation': 'Administered by ARIN',
                'prefix': '192/8',
                'status': 'Legacy',
                'whois': 'whois.arin.net',
            }
        ]
    }

    assert iprange.is_reserved()

    assert iprange.version == 4


def test_iprange_invalid_len_and_alternative():
    range1 = IPRange(IPAddress('::0'), IPAddress(sys.maxsize, 6))

    with pytest.raises(IndexError):
        len(range1)

    range2 = IPRange(IPAddress('::0'), IPAddress(sys.maxsize - 1, 6))
    assert len(range2) == sys.maxsize


def test_iprange_pickling_v4():
    iprange = IPRange('192.0.2.1', '192.0.2.254')
    assert iprange == IPRange('192.0.2.1', '192.0.2.254')
    assert iprange.first == 3221225985
    assert iprange.last == 3221226238
    assert iprange.version == 4

    buf = pickle.dumps(iprange)
    iprange2 = pickle.loads(buf)
    assert iprange2 == iprange
    assert id(iprange2) != id(iprange)
    assert iprange2.first == 3221225985
    assert iprange2.last == 3221226238
    assert iprange2.version == 4


def test_iprange_pickling_v6():
    iprange = IPRange('::ffff:192.0.2.1', '::ffff:192.0.2.254')

    assert iprange == IPRange('::ffff:192.0.2.1', '::ffff:192.0.2.254')
    assert iprange.first == 281473902969345
    assert iprange.last == 281473902969598
    assert iprange.version == 6

    buf = pickle.dumps(iprange)

    iprange2 = pickle.loads(buf)

    assert iprange2 == iprange
    assert iprange2.first == 281473902969345
    assert iprange2.last == 281473902969598
    assert iprange2.version == 6
