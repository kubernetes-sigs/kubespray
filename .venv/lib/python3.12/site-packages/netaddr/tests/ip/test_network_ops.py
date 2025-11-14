import types

from netaddr import IPNetwork, cidr_merge


def test_ipnetwork_cidr_merge():
    ip_list = (
        list(IPNetwork('fe80::/120'))
        + [
            IPNetwork('192.0.2.0/24'),
            IPNetwork('192.0.4.0/25'),
            IPNetwork('192.0.4.128/25'),
        ]
        + list(map(str, IPNetwork('192.0.3.0/24')))
    )
    assert len(ip_list) == 515

    assert cidr_merge(ip_list) == [
        IPNetwork('192.0.2.0/23'),
        IPNetwork('192.0.4.0/24'),
        IPNetwork('fe80::/120'),
    ]


def test_subnetting():
    ip = IPNetwork('172.24.0.0/23')
    assert isinstance(ip.subnet(28), types.GeneratorType)

    subnets = list(ip.subnet(28))
    assert len(subnets) == 32

    assert subnets == [
        IPNetwork('172.24.0.0/28'),
        IPNetwork('172.24.0.16/28'),
        IPNetwork('172.24.0.32/28'),
        IPNetwork('172.24.0.48/28'),
        IPNetwork('172.24.0.64/28'),
        IPNetwork('172.24.0.80/28'),
        IPNetwork('172.24.0.96/28'),
        IPNetwork('172.24.0.112/28'),
        IPNetwork('172.24.0.128/28'),
        IPNetwork('172.24.0.144/28'),
        IPNetwork('172.24.0.160/28'),
        IPNetwork('172.24.0.176/28'),
        IPNetwork('172.24.0.192/28'),
        IPNetwork('172.24.0.208/28'),
        IPNetwork('172.24.0.224/28'),
        IPNetwork('172.24.0.240/28'),
        IPNetwork('172.24.1.0/28'),
        IPNetwork('172.24.1.16/28'),
        IPNetwork('172.24.1.32/28'),
        IPNetwork('172.24.1.48/28'),
        IPNetwork('172.24.1.64/28'),
        IPNetwork('172.24.1.80/28'),
        IPNetwork('172.24.1.96/28'),
        IPNetwork('172.24.1.112/28'),
        IPNetwork('172.24.1.128/28'),
        IPNetwork('172.24.1.144/28'),
        IPNetwork('172.24.1.160/28'),
        IPNetwork('172.24.1.176/28'),
        IPNetwork('172.24.1.192/28'),
        IPNetwork('172.24.1.208/28'),
        IPNetwork('172.24.1.224/28'),
        IPNetwork('172.24.1.240/28'),
    ]


def test_supernetting():
    ip = IPNetwork('192.0.2.114')
    supernets = ip.supernet(22)

    assert supernets == [
        IPNetwork('192.0.0.0/22'),
        IPNetwork('192.0.2.0/23'),
        IPNetwork('192.0.2.0/24'),
        IPNetwork('192.0.2.0/25'),
        IPNetwork('192.0.2.64/26'),
        IPNetwork('192.0.2.96/27'),
        IPNetwork('192.0.2.112/28'),
        IPNetwork('192.0.2.112/29'),
        IPNetwork('192.0.2.112/30'),
        IPNetwork('192.0.2.114/31'),
    ]
