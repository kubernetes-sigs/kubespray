import pytest

from netaddr.ip import IPNetwork
from netaddr.contrib.subnet_splitter import SubnetSplitter


def test_ip_splitter():
    splitter = SubnetSplitter('172.24.0.0/16')
    assert splitter.available_subnets() == [IPNetwork('172.24.0.0/16')]

    assert splitter.extract_subnet(23, count=4) == [
        IPNetwork('172.24.0.0/23'),
        IPNetwork('172.24.2.0/23'),
        IPNetwork('172.24.4.0/23'),
        IPNetwork('172.24.6.0/23'),
    ]

    assert splitter.available_subnets() == [
        IPNetwork('172.24.8.0/21'),
        IPNetwork('172.24.16.0/20'),
        IPNetwork('172.24.32.0/19'),
        IPNetwork('172.24.64.0/18'),
        IPNetwork('172.24.128.0/17'),
    ]

    assert splitter.extract_subnet(28, count=10) == [
        IPNetwork('172.24.8.0/28'),
        IPNetwork('172.24.8.16/28'),
        IPNetwork('172.24.8.32/28'),
        IPNetwork('172.24.8.48/28'),
        IPNetwork('172.24.8.64/28'),
        IPNetwork('172.24.8.80/28'),
        IPNetwork('172.24.8.96/28'),
        IPNetwork('172.24.8.112/28'),
        IPNetwork('172.24.8.128/28'),
        IPNetwork('172.24.8.144/28'),
    ]

    splitter.available_subnets() == [
        IPNetwork('172.24.8.128/25'),
        IPNetwork('172.24.9.0/24'),
        IPNetwork('172.24.10.0/23'),
        IPNetwork('172.24.12.0/22'),
        IPNetwork('172.24.16.0/20'),
        IPNetwork('172.24.32.0/19'),
        IPNetwork('172.24.64.0/18'),
        IPNetwork('172.24.128.0/17'),
    ]


def test_ip_splitter_remove_same_input_range():
    s = SubnetSplitter('172.24.0.0/16')
    assert s.available_subnets() == [IPNetwork('172.24.0.0/16')]

    assert s.extract_subnet(16, count=1) == [
        IPNetwork('172.24.0.0/16'),
    ]

    assert s.available_subnets() == []


def test_ip_splitter_remove_more_than_input_range():
    s = SubnetSplitter('172.24.0.0/16')
    assert s.available_subnets() == [IPNetwork('172.24.0.0/16')]

    with pytest.raises(ValueError):
        s.extract_subnet(16, count=2)


def test_ip_splitter_remove_prefix_larger_than_input_range():
    s = SubnetSplitter('172.24.0.0/16')
    assert s.available_subnets() == [IPNetwork('172.24.0.0/16')]
    assert s.extract_subnet(15, count=1) == []
    assert s.available_subnets() == [IPNetwork('172.24.0.0/16')]
