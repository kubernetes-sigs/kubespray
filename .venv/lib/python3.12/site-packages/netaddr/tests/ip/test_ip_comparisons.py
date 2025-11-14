from netaddr import IPAddress, IPNetwork


def test_basic_comparisons():
    assert IPAddress('192.0.2.1') == IPAddress('192.0.2.1')
    assert not IPAddress('192.0.2.1') != IPAddress('192.0.2.1')

    assert IPAddress('192.0.2.2') > IPAddress('192.0.2.1')
    assert IPAddress('192.0.2.1') >= IPAddress('192.0.2.1')
    assert IPAddress('192.0.2.2') >= IPAddress('192.0.2.1')

    assert IPAddress('192.0.2.1') < IPAddress('192.0.2.2')
    assert IPAddress('192.0.2.1') <= IPAddress('192.0.2.1')
    assert IPAddress('192.0.2.1') <= IPAddress('192.0.2.2')


def test_advanced_comparisons():
    assert IPNetwork('192.0.2.0/24') == IPNetwork('192.0.2.112/24')

    assert IPNetwork('192.0.2.0/24').ip != IPNetwork('192.0.2.112/24').ip
    assert IPNetwork('192.0.2.0/24').ip < IPNetwork('192.0.2.112/24').ip

    assert IPNetwork('192.0.2.0/24').cidr == IPNetwork('192.0.2.112/24').cidr

    assert IPNetwork('192.0.2.0/24') != IPNetwork('192.0.3.0/24')

    assert IPNetwork('192.0.2.0/24') < IPNetwork('192.0.3.0/24')

    assert IPAddress('192.0.2.0') != IPNetwork('192.0.2.0/32')

    assert IPAddress('192.0.2.0') == IPNetwork('192.0.2.0/32')[0]
    assert IPAddress('192.0.2.0') == IPNetwork('192.0.2.0/32')[-1]

    assert IPAddress('192.0.2.0') == IPNetwork('192.0.2.0/32')[0]

    assert IPAddress('192.0.2.0') == IPNetwork('192.0.2.0/32').ip

    assert IPAddress('192.0.2.0') == IPNetwork('192.0.2.0/32').ip
