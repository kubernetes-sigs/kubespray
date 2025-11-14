import pickle
import sys
import weakref

import pytest

from netaddr import IPAddress, IPNetwork, IPRange, IPSet, cidr_exclude


def test_ipset_basic_api():
    range1 = IPRange('192.0.2.1', '192.0.2.15')

    ip_list = [
        IPAddress('192.0.2.1'),
        '192.0.2.2/31',
        IPNetwork('192.0.2.4/31'),
        IPAddress('192.0.2.6'),
        IPAddress('192.0.2.7'),
        '192.0.2.8',
        '192.0.2.9',
        IPAddress('192.0.2.10'),
        IPAddress('192.0.2.11'),
        IPNetwork('192.0.2.12/30'),
    ]

    set1 = IPSet(range1.cidrs())

    set2 = IPSet(ip_list)

    assert set2 == IPSet(
        [
            '192.0.2.1/32',
            '192.0.2.2/31',
            '192.0.2.4/30',
            '192.0.2.8/29',
        ]
    )

    assert set1 == set2
    assert set2.pop() in set1
    assert set1 != set2


def test_ipset_empty():
    assert IPSet() == IPSet([])
    empty_set = IPSet([])
    assert IPSet([]) == empty_set
    assert len(empty_set) == 0


def test_ipset_constructor():
    assert IPSet(['192.0.2.0']) == IPSet(['192.0.2.0/32'])
    assert IPSet([IPAddress('192.0.2.0')]) == IPSet(['192.0.2.0/32'])
    assert IPSet([IPNetwork('192.0.2.0')]) == IPSet(['192.0.2.0/32'])
    assert IPSet(IPNetwork('1234::/32')) == IPSet(['1234::/32'])
    assert IPSet([IPNetwork('192.0.2.0/24')]) == IPSet(['192.0.2.0/24'])
    assert IPSet(IPSet(['192.0.2.0/32'])) == IPSet(['192.0.2.0/32'])
    assert IPSet(IPRange('10.0.0.0', '10.0.1.31')) == IPSet(['10.0.0.0/24', '10.0.1.0/27'])
    assert IPSet(IPRange('0.0.0.0', '255.255.255.255')) == IPSet(['0.0.0.0/0'])
    assert IPSet([IPRange('10.0.0.0', '10.0.1.31')]) == IPSet(IPRange('10.0.0.0', '10.0.1.31'))


def test_ipset_iteration():
    assert list(IPSet(['192.0.2.0/28', '::192.0.2.0/124'])) == [
        IPAddress('192.0.2.0'),
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
        IPAddress('::192.0.2.0'),
        IPAddress('::192.0.2.1'),
        IPAddress('::192.0.2.2'),
        IPAddress('::192.0.2.3'),
        IPAddress('::192.0.2.4'),
        IPAddress('::192.0.2.5'),
        IPAddress('::192.0.2.6'),
        IPAddress('::192.0.2.7'),
        IPAddress('::192.0.2.8'),
        IPAddress('::192.0.2.9'),
        IPAddress('::192.0.2.10'),
        IPAddress('::192.0.2.11'),
        IPAddress('::192.0.2.12'),
        IPAddress('::192.0.2.13'),
        IPAddress('::192.0.2.14'),
        IPAddress('::192.0.2.15'),
    ]


def test_ipset_member_insertion_and_deletion():
    s1 = IPSet()
    s1.add('192.0.2.0')
    assert s1 == IPSet(['192.0.2.0/32'])

    s1.remove('192.0.2.0')
    assert s1 == IPSet([])

    s1.add(IPRange('10.0.0.0', '10.0.0.255'))
    assert s1 == IPSet(['10.0.0.0/24'])

    s1.remove(IPRange('10.0.0.128', '10.10.10.10'))
    assert s1 == IPSet(['10.0.0.0/25'])


def test_ipset_membership():
    iprange = IPRange('192.0.1.255', '192.0.2.16')

    assert iprange.cidrs() == [
        IPNetwork('192.0.1.255/32'),
        IPNetwork('192.0.2.0/28'),
        IPNetwork('192.0.2.16/32'),
    ]

    ipset = IPSet(['192.0.2.0/28'])

    assert [(str(ip), ip in ipset) for ip in iprange] == [
        ('192.0.1.255', False),
        ('192.0.2.0', True),
        ('192.0.2.1', True),
        ('192.0.2.2', True),
        ('192.0.2.3', True),
        ('192.0.2.4', True),
        ('192.0.2.5', True),
        ('192.0.2.6', True),
        ('192.0.2.7', True),
        ('192.0.2.8', True),
        ('192.0.2.9', True),
        ('192.0.2.10', True),
        ('192.0.2.11', True),
        ('192.0.2.12', True),
        ('192.0.2.13', True),
        ('192.0.2.14', True),
        ('192.0.2.15', True),
        ('192.0.2.16', False),
    ]


def test_ipset_membership_largest():
    ipset = IPSet(['0.0.0.0/0'])

    assert IPAddress('10.0.0.1') in ipset
    assert IPAddress('0.0.0.0') in ipset
    assert IPAddress('255.255.255.0') in ipset
    assert IPNetwork('10.0.0.0/24') in ipset
    assert IPAddress('::1') not in ipset


def test_set_membership_smallest():
    ipset = IPSet(['10.0.0.42/32'])

    assert IPAddress('10.0.0.42') in ipset
    assert IPNetwork('10.0.0.42/32') in ipset

    assert IPAddress('10.0.0.41') not in ipset
    assert IPAddress('10.0.0.43') not in ipset
    assert IPNetwork('10.0.0.42/31') not in ipset


def test_ipset_unions():
    assert IPSet(['192.0.2.0']) == IPSet(['192.0.2.0/32'])
    assert IPSet(['192.0.2.0']) | IPSet(['192.0.2.1']) == IPSet(['192.0.2.0/31'])
    assert IPSet(['192.0.2.0']) | IPSet(['192.0.2.1']) | IPSet(['192.0.2.3']) == IPSet(
        ['192.0.2.0/31', '192.0.2.3/32']
    )
    assert IPSet(['192.0.2.0']) | IPSet(['192.0.2.1']) | IPSet(['192.0.2.3/30']) == IPSet(
        ['192.0.2.0/30']
    )
    assert IPSet(['192.0.2.0']) | IPSet(['192.0.2.1']) | IPSet(['192.0.2.3/31']) == IPSet(
        ['192.0.2.0/30']
    )
    assert IPSet(['192.0.2.0/24']) | IPSet(['192.0.3.0/24']) | IPSet(['192.0.4.0/24']) == IPSet(
        ['192.0.2.0/23', '192.0.4.0/24']
    )


def test_ipset_unions_intersections_differences():
    adj_cidrs = list(IPNetwork('192.0.2.0/24').subnet(28))
    even_cidrs = adj_cidrs[::2]
    evens = IPSet(even_cidrs)

    assert evens == IPSet(
        [
            '192.0.2.0/28',
            '192.0.2.32/28',
            '192.0.2.64/28',
            '192.0.2.96/28',
            '192.0.2.128/28',
            '192.0.2.160/28',
            '192.0.2.192/28',
            '192.0.2.224/28',
        ]
    )

    assert IPSet(['192.0.2.0/24']) & evens == IPSet(
        [
            '192.0.2.0/28',
            '192.0.2.32/28',
            '192.0.2.64/28',
            '192.0.2.96/28',
            '192.0.2.128/28',
            '192.0.2.160/28',
            '192.0.2.192/28',
            '192.0.2.224/28',
        ]
    )

    odds = IPSet(['192.0.2.0/24']) ^ evens
    assert odds == IPSet(
        [
            '192.0.2.16/28',
            '192.0.2.48/28',
            '192.0.2.80/28',
            '192.0.2.112/28',
            '192.0.2.144/28',
            '192.0.2.176/28',
            '192.0.2.208/28',
            '192.0.2.240/28',
        ]
    )

    assert evens | odds == IPSet(['192.0.2.0/24'])
    assert evens & odds == IPSet([])
    assert evens ^ odds == IPSet(['192.0.2.0/24'])


def test_ipset_supersets_and_subsets():
    s1 = IPSet(['192.0.2.0/24', '192.0.4.0/24'])
    s2 = IPSet(['192.0.2.0', '192.0.4.0'])

    assert s1.issuperset(s2)
    assert s2.issubset(s1)
    assert not s2.issuperset(s1)
    assert not s1.issubset(s2)

    ipv4_addr_space = IPSet(['0.0.0.0/0'])
    private = IPSet(
        ['10.0.0.0/8', '172.16.0.0/12', '192.0.2.0/24', '192.168.0.0/16', '239.192.0.0/14']
    )
    reserved = IPSet(
        [
            '225.0.0.0/8',
            '226.0.0.0/7',
            '228.0.0.0/6',
            '234.0.0.0/7',
            '236.0.0.0/7',
            '238.0.0.0/8',
            '240.0.0.0/4',
        ]
    )
    unavailable = reserved | private
    available = ipv4_addr_space ^ unavailable

    assert [tuple(map(str, (cidr, cidr[0], cidr[-1]))) for cidr in available.iter_cidrs()] == [
        ('0.0.0.0/5', '0.0.0.0', '7.255.255.255'),
        ('8.0.0.0/7', '8.0.0.0', '9.255.255.255'),
        ('11.0.0.0/8', '11.0.0.0', '11.255.255.255'),
        ('12.0.0.0/6', '12.0.0.0', '15.255.255.255'),
        ('16.0.0.0/4', '16.0.0.0', '31.255.255.255'),
        ('32.0.0.0/3', '32.0.0.0', '63.255.255.255'),
        ('64.0.0.0/2', '64.0.0.0', '127.255.255.255'),
        ('128.0.0.0/3', '128.0.0.0', '159.255.255.255'),
        ('160.0.0.0/5', '160.0.0.0', '167.255.255.255'),
        ('168.0.0.0/6', '168.0.0.0', '171.255.255.255'),
        ('172.0.0.0/12', '172.0.0.0', '172.15.255.255'),
        ('172.32.0.0/11', '172.32.0.0', '172.63.255.255'),
        ('172.64.0.0/10', '172.64.0.0', '172.127.255.255'),
        ('172.128.0.0/9', '172.128.0.0', '172.255.255.255'),
        ('173.0.0.0/8', '173.0.0.0', '173.255.255.255'),
        ('174.0.0.0/7', '174.0.0.0', '175.255.255.255'),
        ('176.0.0.0/4', '176.0.0.0', '191.255.255.255'),
        ('192.0.0.0/23', '192.0.0.0', '192.0.1.255'),
        ('192.0.3.0/24', '192.0.3.0', '192.0.3.255'),
        ('192.0.4.0/22', '192.0.4.0', '192.0.7.255'),
        ('192.0.8.0/21', '192.0.8.0', '192.0.15.255'),
        ('192.0.16.0/20', '192.0.16.0', '192.0.31.255'),
        ('192.0.32.0/19', '192.0.32.0', '192.0.63.255'),
        ('192.0.64.0/18', '192.0.64.0', '192.0.127.255'),
        ('192.0.128.0/17', '192.0.128.0', '192.0.255.255'),
        ('192.1.0.0/16', '192.1.0.0', '192.1.255.255'),
        ('192.2.0.0/15', '192.2.0.0', '192.3.255.255'),
        ('192.4.0.0/14', '192.4.0.0', '192.7.255.255'),
        ('192.8.0.0/13', '192.8.0.0', '192.15.255.255'),
        ('192.16.0.0/12', '192.16.0.0', '192.31.255.255'),
        ('192.32.0.0/11', '192.32.0.0', '192.63.255.255'),
        ('192.64.0.0/10', '192.64.0.0', '192.127.255.255'),
        ('192.128.0.0/11', '192.128.0.0', '192.159.255.255'),
        ('192.160.0.0/13', '192.160.0.0', '192.167.255.255'),
        ('192.169.0.0/16', '192.169.0.0', '192.169.255.255'),
        ('192.170.0.0/15', '192.170.0.0', '192.171.255.255'),
        ('192.172.0.0/14', '192.172.0.0', '192.175.255.255'),
        ('192.176.0.0/12', '192.176.0.0', '192.191.255.255'),
        ('192.192.0.0/10', '192.192.0.0', '192.255.255.255'),
        ('193.0.0.0/8', '193.0.0.0', '193.255.255.255'),
        ('194.0.0.0/7', '194.0.0.0', '195.255.255.255'),
        ('196.0.0.0/6', '196.0.0.0', '199.255.255.255'),
        ('200.0.0.0/5', '200.0.0.0', '207.255.255.255'),
        ('208.0.0.0/4', '208.0.0.0', '223.255.255.255'),
        ('224.0.0.0/8', '224.0.0.0', '224.255.255.255'),
        ('232.0.0.0/7', '232.0.0.0', '233.255.255.255'),
        ('239.0.0.0/9', '239.0.0.0', '239.127.255.255'),
        ('239.128.0.0/10', '239.128.0.0', '239.191.255.255'),
        ('239.196.0.0/14', '239.196.0.0', '239.199.255.255'),
        ('239.200.0.0/13', '239.200.0.0', '239.207.255.255'),
        ('239.208.0.0/12', '239.208.0.0', '239.223.255.255'),
        ('239.224.0.0/11', '239.224.0.0', '239.255.255.255'),
    ]

    assert ipv4_addr_space ^ available == IPSet(
        [
            '10.0.0.0/8',
            '172.16.0.0/12',
            '192.0.2.0/24',
            '192.168.0.0/16',
            '225.0.0.0/8',
            '226.0.0.0/7',
            '228.0.0.0/6',
            '234.0.0.0/7',
            '236.0.0.0/7',
            '238.0.0.0/8',
            '239.192.0.0/14',
            '240.0.0.0/4',
        ]
    )


def test_combined_ipv4_and_ipv6_ipsets():
    s1 = IPSet(['192.0.2.0', '::192.0.2.0', '192.0.2.2', '::192.0.2.2'])
    s2 = IPSet(['192.0.2.2', '::192.0.2.2', '192.0.2.4', '::192.0.2.4'])

    assert s1 | s2 == IPSet(
        [
            '192.0.2.0/32',
            '192.0.2.2/32',
            '192.0.2.4/32',
            '::192.0.2.0/128',
            '::192.0.2.2/128',
            '::192.0.2.4/128',
        ]
    )

    assert s2 | s1 == IPSet(
        [
            '192.0.2.0/32',
            '192.0.2.2/32',
            '192.0.2.4/32',
            '::192.0.2.0/128',
            '::192.0.2.2/128',
            '::192.0.2.4/128',
        ]
    )

    assert s1 & s2 == IPSet(['192.0.2.2/32', '::192.0.2.2/128'])
    assert s1 - s2 == IPSet(['192.0.2.0/32', '::192.0.2.0/128'])
    assert s2 - s1 == IPSet(['192.0.2.4/32', '::192.0.2.4/128'])
    assert s1 ^ s2 == IPSet(['192.0.2.0/32', '192.0.2.4/32', '::192.0.2.0/128', '::192.0.2.4/128'])


def test_disjointed_ipsets():
    s1 = IPSet(['192.0.2.0', '192.0.2.1', '192.0.2.2'])
    s2 = IPSet(['192.0.2.2', '192.0.2.3', '192.0.2.4'])

    assert s1 & s2 == IPSet(['192.0.2.2/32'])
    assert not s1.isdisjoint(s2)

    s3 = IPSet(['192.0.2.0', '192.0.2.1'])
    s4 = IPSet(['192.0.2.3', '192.0.2.4'])

    assert s3 & s4 == IPSet([])
    assert s3.isdisjoint(s4)


def test_ipset_updates():
    s1 = IPSet(['192.0.2.0/25'])
    s2 = IPSet(['192.0.2.128/25'])

    s1.update(s2)
    assert s1 == IPSet(['192.0.2.0/24'])

    s1.update(['192.0.0.0/24', '192.0.1.0/24', '192.0.3.0/24'])
    assert s1 == IPSet(['192.0.0.0/22'])

    expected = IPSet(['192.0.1.0/24', '192.0.2.0/24'])

    s3 = IPSet(['192.0.1.0/24'])
    s3.update(IPRange('192.0.2.0', '192.0.2.255'))
    assert s3 == expected

    s4 = IPSet(['192.0.1.0/24'])
    s4.update([IPRange('192.0.2.0', '192.0.2.100'), IPRange('192.0.2.50', '192.0.2.255')])
    assert s4 == expected


def test_ipset_clear():
    ipset = IPSet(['10.0.0.0/16'])
    ipset.update(IPRange('10.1.0.0', '10.1.255.255'))
    assert ipset == IPSet(['10.0.0.0/15'])

    ipset.clear()
    assert ipset == IPSet([])


def test_ipset_cidr_fracturing():
    s1 = IPSet(['0.0.0.0/0'])
    s1.remove('255.255.255.255')
    assert s1 == IPSet(
        [
            '0.0.0.0/1',
            '128.0.0.0/2',
            '192.0.0.0/3',
            '224.0.0.0/4',
            '240.0.0.0/5',
            '248.0.0.0/6',
            '252.0.0.0/7',
            '254.0.0.0/8',
            '255.0.0.0/9',
            '255.128.0.0/10',
            '255.192.0.0/11',
            '255.224.0.0/12',
            '255.240.0.0/13',
            '255.248.0.0/14',
            '255.252.0.0/15',
            '255.254.0.0/16',
            '255.255.0.0/17',
            '255.255.128.0/18',
            '255.255.192.0/19',
            '255.255.224.0/20',
            '255.255.240.0/21',
            '255.255.248.0/22',
            '255.255.252.0/23',
            '255.255.254.0/24',
            '255.255.255.0/25',
            '255.255.255.128/26',
            '255.255.255.192/27',
            '255.255.255.224/28',
            '255.255.255.240/29',
            '255.255.255.248/30',
            '255.255.255.252/31',
            '255.255.255.254/32',
        ]
    )

    cidrs = s1.iter_cidrs()
    assert len(cidrs) == 32
    assert list(cidrs) == [
        IPNetwork('0.0.0.0/1'),
        IPNetwork('128.0.0.0/2'),
        IPNetwork('192.0.0.0/3'),
        IPNetwork('224.0.0.0/4'),
        IPNetwork('240.0.0.0/5'),
        IPNetwork('248.0.0.0/6'),
        IPNetwork('252.0.0.0/7'),
        IPNetwork('254.0.0.0/8'),
        IPNetwork('255.0.0.0/9'),
        IPNetwork('255.128.0.0/10'),
        IPNetwork('255.192.0.0/11'),
        IPNetwork('255.224.0.0/12'),
        IPNetwork('255.240.0.0/13'),
        IPNetwork('255.248.0.0/14'),
        IPNetwork('255.252.0.0/15'),
        IPNetwork('255.254.0.0/16'),
        IPNetwork('255.255.0.0/17'),
        IPNetwork('255.255.128.0/18'),
        IPNetwork('255.255.192.0/19'),
        IPNetwork('255.255.224.0/20'),
        IPNetwork('255.255.240.0/21'),
        IPNetwork('255.255.248.0/22'),
        IPNetwork('255.255.252.0/23'),
        IPNetwork('255.255.254.0/24'),
        IPNetwork('255.255.255.0/25'),
        IPNetwork('255.255.255.128/26'),
        IPNetwork('255.255.255.192/27'),
        IPNetwork('255.255.255.224/28'),
        IPNetwork('255.255.255.240/29'),
        IPNetwork('255.255.255.248/30'),
        IPNetwork('255.255.255.252/31'),
        IPNetwork('255.255.255.254/32'),
    ]

    assert cidrs == cidr_exclude('0.0.0.0/0', '255.255.255.255')

    s1.remove('0.0.0.0')

    assert s1 == IPSet(
        [
            '0.0.0.1/32',
            '0.0.0.2/31',
            '0.0.0.4/30',
            '0.0.0.8/29',
            '0.0.0.16/28',
            '0.0.0.32/27',
            '0.0.0.64/26',
            '0.0.0.128/25',
            '0.0.1.0/24',
            '0.0.2.0/23',
            '0.0.4.0/22',
            '0.0.8.0/21',
            '0.0.16.0/20',
            '0.0.32.0/19',
            '0.0.64.0/18',
            '0.0.128.0/17',
            '0.1.0.0/16',
            '0.2.0.0/15',
            '0.4.0.0/14',
            '0.8.0.0/13',
            '0.16.0.0/12',
            '0.32.0.0/11',
            '0.64.0.0/10',
            '0.128.0.0/9',
            '1.0.0.0/8',
            '2.0.0.0/7',
            '4.0.0.0/6',
            '8.0.0.0/5',
            '16.0.0.0/4',
            '32.0.0.0/3',
            '64.0.0.0/2',
            '128.0.0.0/2',
            '192.0.0.0/3',
            '224.0.0.0/4',
            '240.0.0.0/5',
            '248.0.0.0/6',
            '252.0.0.0/7',
            '254.0.0.0/8',
            '255.0.0.0/9',
            '255.128.0.0/10',
            '255.192.0.0/11',
            '255.224.0.0/12',
            '255.240.0.0/13',
            '255.248.0.0/14',
            '255.252.0.0/15',
            '255.254.0.0/16',
            '255.255.0.0/17',
            '255.255.128.0/18',
            '255.255.192.0/19',
            '255.255.224.0/20',
            '255.255.240.0/21',
            '255.255.248.0/22',
            '255.255.252.0/23',
            '255.255.254.0/24',
            '255.255.255.0/25',
            '255.255.255.128/26',
            '255.255.255.192/27',
            '255.255.255.224/28',
            '255.255.255.240/29',
            '255.255.255.248/30',
            '255.255.255.252/31',
            '255.255.255.254/32',
        ]
    )

    assert len(list(s1.iter_cidrs())) == 62

    s1.add('255.255.255.255')
    s1.add('0.0.0.0')

    assert s1 == IPSet(['0.0.0.0/0'])


def test_ipset_with_iprange():
    s1 = IPSet(['10.0.0.0/25', '10.0.0.128/25'])
    assert s1.iprange() == IPRange('10.0.0.0', '10.0.0.255')

    assert s1.iscontiguous()

    s1.remove('10.0.0.16')
    assert s1 == IPSet(
        [
            '10.0.0.0/28',
            '10.0.0.17/32',
            '10.0.0.18/31',
            '10.0.0.20/30',
            '10.0.0.24/29',
            '10.0.0.32/27',
            '10.0.0.64/26',
            '10.0.0.128/25',
        ]
    )

    assert not s1.iscontiguous()

    with pytest.raises(ValueError):
        s1.iprange()

    assert list(s1.iter_ipranges()) == [
        IPRange('10.0.0.0', '10.0.0.15'),
        IPRange('10.0.0.17', '10.0.0.255'),
    ]

    s2 = IPSet(['0.0.0.0/0'])
    assert s2.iscontiguous()
    assert s2.iprange() == IPRange('0.0.0.0', '255.255.255.255')
    #
    s3 = IPSet()
    assert s3.iscontiguous()
    assert s3.iprange() is None

    s4 = IPSet(IPRange('10.0.0.0', '10.0.0.8'))
    assert s4.iscontiguous()


def test_ipset_pickling():
    ip_data = IPSet(['10.0.0.0/16', 'fe80::/64'])
    buf = pickle.dumps(ip_data)
    ip_data_unpickled = pickle.loads(buf)
    assert ip_data == ip_data_unpickled


def test_ipset_comparison():
    s1 = IPSet(['fc00::/2'])
    s2 = IPSet(['fc00::/3'])

    assert s1 > s2
    assert not s1 < s2
    assert s1 != s2


def test_ipset_adding_and_removing_members_ip_addresses_as_ints():
    s1 = IPSet(['10.0.0.0/25'])

    s1.add('10.0.0.0/24')
    assert s1 == IPSet(['10.0.0.0/24'])

    integer1 = int(IPAddress('10.0.0.1'))
    integer2 = int(IPAddress('fe80::'))
    integer3 = int(IPAddress('10.0.0.2'))

    s2 = IPSet([integer1, integer2])
    assert s2 == IPSet(['10.0.0.1/32', 'fe80::/128'])

    s2.add(integer3)
    assert s2 == IPSet(['10.0.0.1/32', '10.0.0.2/32', 'fe80::/128'])

    s2.remove(integer2)
    assert s2 == IPSet(['10.0.0.1/32', '10.0.0.2/32'])

    s2.update([integer2])
    assert s2 == IPSet(['10.0.0.1/32', '10.0.0.2/32', 'fe80::/128'])


def test_ipset_operations_with_combined_ipv4_and_ipv6():
    s1 = IPSet(['192.0.2.0', '::192.0.2.0', '192.0.2.2', '::192.0.2.2'])
    s2 = IPSet(['192.0.2.2', '::192.0.2.2', '192.0.2.4', '::192.0.2.4'])
    s3 = IPSet(['0.0.0.1', '10.0.0.64/30', '255.255.255.1'])
    s4 = IPSet(['10.0.0.64', '10.0.0.66'])
    s4b = IPSet(['10.0.0.64', '10.0.0.66', '111.111.111.111'])
    s5 = IPSet(['10.0.0.65', '10.0.0.67'])
    s6 = IPSet(['2405:8100::/32'])

    assert bool(s6)
    assert not bool(IPSet())

    #   set intersection
    assert s2 & s1 == IPSet(['192.0.2.2/32', '::192.0.2.2/128'])
    assert s3 & s4 == IPSet(['10.0.0.64/32', '10.0.0.66/32'])
    assert s4 & s3 == IPSet(['10.0.0.64/32', '10.0.0.66/32'])
    assert s3 & s5 == IPSet(['10.0.0.65/32', '10.0.0.67/32'])
    assert s5 & s3 == IPSet(['10.0.0.65/32', '10.0.0.67/32'])

    #   set difference
    assert s3 - s4 == IPSet(['0.0.0.1/32', '10.0.0.65/32', '10.0.0.67/32', '255.255.255.1/32'])
    assert s4 - s3 == IPSet([])
    assert s3 - s4b == IPSet(['0.0.0.1/32', '10.0.0.65/32', '10.0.0.67/32', '255.255.255.1/32'])
    assert s3 - s5 == IPSet(['0.0.0.1/32', '10.0.0.64/32', '10.0.0.66/32', '255.255.255.1/32'])
    assert s5 - s3 == IPSet([])

    #   set symmetric difference
    assert s2 ^ s1 == IPSet(['192.0.2.0/32', '192.0.2.4/32', '::192.0.2.0/128', '::192.0.2.4/128'])
    assert IPSet([]) ^ IPSet([]) == IPSet([])
    assert IPSet(['0.0.0.1/32']) ^ IPSet([]) == IPSet(['0.0.0.1/32'])
    assert IPSet(['0.0.0.1/32']) ^ IPSet(['0.0.0.1/32']) == IPSet([])
    assert s3 ^ s4 == IPSet(['0.0.0.1/32', '10.0.0.65/32', '10.0.0.67/32', '255.255.255.1/32'])
    assert s4 ^ s3 == IPSet(['0.0.0.1/32', '10.0.0.65/32', '10.0.0.67/32', '255.255.255.1/32'])
    assert s3 ^ s4b == IPSet(
        ['0.0.0.1/32', '10.0.0.65/32', '10.0.0.67/32', '111.111.111.111/32', '255.255.255.1/32']
    )
    assert s3 ^ s5 == IPSet(['0.0.0.1/32', '10.0.0.64/32', '10.0.0.66/32', '255.255.255.1/32'])
    assert s5 ^ s3 == IPSet(['0.0.0.1/32', '10.0.0.64/32', '10.0.0.66/32', '255.255.255.1/32'])


def test_converting_ipsets_to_ipranges():
    assert list(IPSet().iter_ipranges()) == []
    assert list(IPSet([IPAddress('10.0.0.1')]).iter_ipranges()) == [IPRange('10.0.0.1', '10.0.0.1')]
    assert list(IPSet([IPAddress('10.0.0.1'), IPAddress('10.0.0.2')]).iter_ipranges()) == [
        IPRange('10.0.0.1', '10.0.0.2')
    ]


def test_len_on_ipset_failure_with_large_ipv6_addresses():
    s1 = IPSet(IPRange(IPAddress('::0'), IPAddress(sys.maxsize, 6)))
    with pytest.raises(IndexError):
        len(s1)

    s2 = IPSet(IPRange(IPAddress('::0'), IPAddress(sys.maxsize - 1, 6)))
    assert len(s2) == sys.maxsize


def test_ipset_ipv4_and_ipv4_separation():
    assert list(IPSet([IPAddress(1, 4), IPAddress(1, 6)]).iter_ipranges()) == [
        IPRange('0.0.0.1', '0.0.0.1'),
        IPRange('::1', '::1'),
    ]


def test_ipset_exceptions():
    s1 = IPSet(['10.0.0.1'])

    #   IPSet objects are not hashable.
    with pytest.raises(TypeError):
        hash(s1)

    #   Bad update argument type.
    with pytest.raises(TypeError):
        s1.update(42)


def test_ipset_comparison_with_int_is_invalid():
    s1 = IPSet(['10.0.0.1'])
    assert not s1 == 42
    s1 != 42


def test_ipset_converts_to_cidr_networks_v4():
    s1 = IPSet(IPNetwork('10.1.2.3/8'))
    s1.add(IPNetwork('192.168.1.2/16'))
    assert list(s1.iter_cidrs()) == [
        IPNetwork('10.0.0.0/8'),
        IPNetwork('192.168.0.0/16'),
    ]


def test_ipset_converts_to_cidr_networks_v6():
    s1 = IPSet(IPNetwork('fe80::4242/64'))
    s1.add(IPNetwork('fe90::4343/64'))
    assert list(s1.iter_cidrs()) == [
        IPNetwork('fe80::/64'),
        IPNetwork('fe90::/64'),
    ]


def test_ipset_is_weak_referencable():
    weakref.ref(IPSet())
