from netaddr import IPNetwork


def test_is_unicast():
    assert IPNetwork('192.0.2.0/24').is_unicast()
    assert IPNetwork('fe80::1/48').is_unicast()


def test_is_multicast():
    assert IPNetwork('239.192.0.1/24').is_multicast()
    assert IPNetwork('ff00::/8').is_multicast()


def test_is_reserved():
    assert IPNetwork('240.0.0.0/24').is_reserved()
    assert IPNetwork('0::/48').is_reserved()


def test_is_loopback():
    assert IPNetwork('127.0.0.0/8').is_loopback()
    assert IPNetwork('::1/128').is_loopback()
