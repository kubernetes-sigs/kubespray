import pytest
from netaddr import valid_nmap_range, iter_nmap_range, IPAddress, AddrFormatError


def test_valid_nmap_range_with_valid_target_specs():
    assert valid_nmap_range('192.0.2.1')
    assert valid_nmap_range('192.0.2.0-31')
    assert valid_nmap_range('192.0.2-3.1-254')
    assert valid_nmap_range('0-255.0-255.0-255.0-255')
    assert valid_nmap_range('192.168.3-5,7.1')
    assert valid_nmap_range('192.168.3-5,7,10-12,13,14.1')
    assert valid_nmap_range('fe80::1')
    assert valid_nmap_range('::')
    assert valid_nmap_range('192.0.2.0/24')


def test_valid_nmap_range_with_invalid_target_specs():
    assert not valid_nmap_range('192.0.2.0/255.255.255.0')
    assert not valid_nmap_range(1)
    assert not valid_nmap_range('1')
    assert not valid_nmap_range([])
    assert not valid_nmap_range({})
    assert not valid_nmap_range('fe80::/64')
    assert not valid_nmap_range('255.255.255.256')
    assert not valid_nmap_range('0-255.0-255.0-255.0-256')
    assert not valid_nmap_range('0-255.0-255.0-255.-1-0')
    assert not valid_nmap_range('0-255.0-255.0-255.256-0')
    assert not valid_nmap_range('0-255.0-255.0-255.255-0')
    assert not valid_nmap_range('a.b.c.d-e')
    assert not valid_nmap_range('255.255.255.a-b')


def test_iter_nmap_range():
    assert list(iter_nmap_range('192.0.2.1')) == [IPAddress('192.0.2.1')]

    ip_list = list(iter_nmap_range('192.0.2.0-31'))
    assert len(ip_list) == 32
    assert ip_list == [
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
        IPAddress('192.0.2.16'),
        IPAddress('192.0.2.17'),
        IPAddress('192.0.2.18'),
        IPAddress('192.0.2.19'),
        IPAddress('192.0.2.20'),
        IPAddress('192.0.2.21'),
        IPAddress('192.0.2.22'),
        IPAddress('192.0.2.23'),
        IPAddress('192.0.2.24'),
        IPAddress('192.0.2.25'),
        IPAddress('192.0.2.26'),
        IPAddress('192.0.2.27'),
        IPAddress('192.0.2.28'),
        IPAddress('192.0.2.29'),
        IPAddress('192.0.2.30'),
        IPAddress('192.0.2.31'),
    ]

    assert len(list(iter_nmap_range('192.0.2-3.1-7'))) == 14

    assert list(iter_nmap_range('192.0.2.1-3,5,7-9')) == [
        IPAddress('192.0.2.1'),
        IPAddress('192.0.2.2'),
        IPAddress('192.0.2.3'),
        IPAddress('192.0.2.5'),
        IPAddress('192.0.2.7'),
        IPAddress('192.0.2.8'),
        IPAddress('192.0.2.9'),
    ]


def test_iter_nmap_range_with_multiple_targets_including_cidr():
    assert list(iter_nmap_range('192.168.0.0/29', '192.168.3-5,7.1', 'fe80::1')) == [
        IPAddress('192.168.0.0'),
        IPAddress('192.168.0.1'),
        IPAddress('192.168.0.2'),
        IPAddress('192.168.0.3'),
        IPAddress('192.168.0.4'),
        IPAddress('192.168.0.5'),
        IPAddress('192.168.0.6'),
        IPAddress('192.168.0.7'),
        IPAddress('192.168.3.1'),
        IPAddress('192.168.4.1'),
        IPAddress('192.168.5.1'),
        IPAddress('192.168.7.1'),
        IPAddress('fe80::1'),
    ]


def test_iter_nmap_range_invalid():
    with pytest.raises(AddrFormatError):
        list(iter_nmap_range('fe80::/64'))


def test_iter_nmap_range_remove_duplicates():
    assert list(iter_nmap_range('10.0.0.42,42-42')) == [IPAddress('10.0.0.42')]
