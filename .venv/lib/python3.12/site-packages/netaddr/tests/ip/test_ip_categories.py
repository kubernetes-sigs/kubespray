import pytest

from netaddr import IPAddress

# Excluding is_ipv4_compat as we'll likely be dropping it
unicast = 1 << 0
multicast = 1 << 1
loopback = 1 << 2
link_local = 1 << 4
reserved = 1 << 5
ipv4_mapped = 1 << 6
hostmask = 1 << 7
netmask = 1 << 8
ipv4_private_use = 1 << 9
global_ = 1 << 10
ipv6_unique_local = 1 << 11

flags = {
    'unicast': unicast,
    'multicast': multicast,
    'loopback': loopback,
    'link_local': link_local,
    'reserved': reserved,
    'ipv4_mapped': ipv4_mapped,
    'hostmask': hostmask,
    'netmask': netmask,
    'ipv4_private_use': ipv4_private_use,
    'global': global_,
    'ipv6_unique_local': ipv6_unique_local,
}


@pytest.mark.parametrize(
    'text_address,categories',
    [
        # IPv4
        ['0.0.0.0', reserved | hostmask | netmask | unicast],
        ['0.0.1.255', hostmask | reserved | unicast | hostmask],
        ['0.255.255.255', reserved | hostmask | unicast],
        ['10.0.0.1', ipv4_private_use | unicast],
        ['62.125.24.5', global_ | unicast],
        ['100.64.0.0', unicast],
        ['127.0.0.0', reserved | loopback | unicast | reserved],
        ['127.0.0.1', loopback | reserved | unicast],
        ['172.24.0.1', ipv4_private_use | unicast],
        ['127.255.255.255', reserved | hostmask | loopback | unicast],
        ['169.254.0.0', link_local | unicast],
        ['192.0.0.0', netmask | unicast],
        ['192.0.0.8', unicast],
        ['192.0.0.9', global_ | unicast],
        ['192.0.0.10', global_ | unicast],
        ['192.0.0.11', unicast],
        ['192.0.0.170', unicast],
        ['192.0.0.171', unicast],
        ['192.0.2.0', reserved | unicast],
        ['192.0.2.1', reserved | unicast],
        ['192.0.2.255', reserved | unicast],
        ['192.31.196.0', global_ | unicast],
        ['192.52.193.0', global_ | unicast],
        ['192.88.99.0', global_ | reserved | unicast],
        ['192.88.99.255', global_ | reserved | unicast],
        ['192.168.0.1', ipv4_private_use | unicast],
        ['192.175.48.0', global_ | unicast],
        ['198.18.0.0', unicast],
        ['198.19.255.255', unicast],
        ['198.51.100.0', reserved | unicast],
        ['203.0.113.0', reserved | unicast],
        ['233.252.0.0', global_ | reserved | multicast],
        ['233.252.0.255', global_ | reserved | multicast],
        ['239.192.0.1', global_ | multicast],
        ['253.0.0.1', reserved | unicast],
        ['255.255.254.0', netmask | reserved | unicast],
        # IPv6
        ['::', hostmask | netmask | reserved | unicast],
        ['::1', loopback | hostmask | reserved | unicast],
        ['::ffff:0.0.0.0', ipv4_mapped | reserved | unicast],
        ['::ffff:1.1.1.1', ipv4_mapped | reserved | unicast],
        ['64:ff9b::', global_ | reserved | unicast],
        ['64:ff9b:1::', reserved | unicast],
        ['100::', reserved | unicast],
        ['2001::', unicast],
        ['2001:1::1', global_ | unicast],
        ['2001:1::2', global_ | unicast],
        ['2001:2::', unicast],
        ['2001:3::', global_ | unicast],
        ['2001:4:112::', global_ | unicast],
        ['2001:10::', unicast],
        ['2001:20::', global_ | unicast],
        ['2001:30::', global_ | unicast],
        ['2001:db8::', unicast],
        ['2002::', unicast],
        ['2620:4f:8000::', global_ | unicast],
        ['fc00::1', ipv6_unique_local | unicast],
        ['fe80::1', unicast | link_local],
        ['ff00::1', global_ | reserved | multicast],
    ],
)
def test_ip_categories(text_address, categories):
    address = IPAddress(text_address)
    methods = [
        getattr(address, name)
        for name in dir(address)
        if name.startswith('is_') and name != 'is_ipv4_compat'
    ]
    for method in methods:
        name = method.__name__.replace('is_', '')
        flag = flags[name]
        got_value = method()
        expected_value = bool(categories & flag)
        assert got_value == expected_value, 'Expected is_%s() value to be %s' % (
            name,
            expected_value,
        )
        categories &= ~flag

    # Just one final check to make sure we haven't missed any flags
    assert categories == 0
