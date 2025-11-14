from netaddr import IPAddress, IPNetwork


def test_ip_v4_to_ipv6_mapped():
    ip = IPAddress('192.0.2.15').ipv6()
    assert ip == IPAddress('::ffff:192.0.2.15')
    assert ip.is_ipv4_mapped()
    assert not ip.is_ipv4_compat()


def test_ip_v4_to_ipv4():
    assert IPAddress('192.0.2.15').ipv4() == IPAddress('192.0.2.15')


def test_ip_v4_to_ipv6_compatible():
    assert IPAddress('192.0.2.15').ipv6(ipv4_compatible=True) == IPAddress('::192.0.2.15')
    assert IPAddress('192.0.2.15').ipv6(ipv4_compatible=True).is_ipv4_compat()
    assert IPAddress('192.0.2.15').ipv6(True) == IPAddress('::192.0.2.15')

    ip = IPNetwork('192.0.2.1/23')
    assert ip.ipv4() == IPNetwork('192.0.2.1/23')
    assert ip.ipv6() == IPNetwork('::ffff:192.0.2.1/119')
    assert ip.ipv6(ipv4_compatible=True) == IPNetwork('::192.0.2.1/119')


def test_ip_v6_to_ipv4():
    assert IPNetwork('::ffff:192.0.2.1/119').ipv6(ipv4_compatible=True) == IPNetwork(
        '::192.0.2.1/119'
    )
    assert IPNetwork('::ffff:192.0.2.1/119').ipv4() == IPNetwork('192.0.2.1/23')
    assert IPNetwork('::192.0.2.1/119').ipv4() == IPNetwork('192.0.2.1/23')


def test_ip_v6_to_ipv6():
    assert IPNetwork('::ffff:192.0.2.1/119').ipv6() == IPNetwork('::ffff:192.0.2.1/119')
