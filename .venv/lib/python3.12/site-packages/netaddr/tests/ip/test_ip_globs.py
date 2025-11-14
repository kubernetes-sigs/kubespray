from netaddr import (
    IPGlob,
    IPNetwork,
    cidr_to_glob,
    glob_to_cidrs,
    glob_to_iptuple,
    iprange_to_globs,
    IPAddress,
    valid_glob,
    glob_to_iprange,
    IPRange,
)


def test_ipglob_basic():
    # TODO: do the same testing on IPGlob as IPRange.
    assert IPGlob('192.0.2.*') == IPNetwork('192.0.2.0/24')


def test_ipglob_boolean_evaluation():
    assert bool(IPGlob('*.*.*.*'))
    assert bool(IPGlob('0.0.0.0'))


def test_cidr_to_glob():
    assert cidr_to_glob('10.0.0.1/32') == '10.0.0.1'
    assert cidr_to_glob('192.0.2.0/24') == '192.0.2.*'
    assert cidr_to_glob('172.16.0.0/12') == '172.16-31.*.*'
    assert cidr_to_glob('0.0.0.0/0') == '*.*.*.*'


def test_glob_to_cidrs():
    assert glob_to_cidrs('10.0.0.1') == [IPNetwork('10.0.0.1/32')]
    assert glob_to_cidrs('192.0.2.*') == [IPNetwork('192.0.2.0/24')]
    assert glob_to_cidrs('172.16-31.*.*') == [IPNetwork('172.16.0.0/12')]
    assert glob_to_cidrs('*.*.*.*') == [IPNetwork('0.0.0.0/0')]


def test_glob_to_iptuple():
    assert glob_to_iptuple('*.*.*.*') == (IPAddress('0.0.0.0'), IPAddress('255.255.255.255'))


def test_iprange_to_globs():
    assert iprange_to_globs('192.0.2.0', '192.0.2.255') == ['192.0.2.*']
    assert iprange_to_globs('192.0.2.1', '192.0.2.15') == ['192.0.2.1-15']
    assert iprange_to_globs('192.0.2.255', '192.0.4.1') == [
        '192.0.2.255',
        '192.0.3.*',
        '192.0.4.0-1',
    ]
    assert iprange_to_globs('10.0.1.255', '10.0.255.255') == [
        '10.0.1.255',
        '10.0.2-3.*',
        '10.0.4-7.*',
        '10.0.8-15.*',
        '10.0.16-31.*',
        '10.0.32-63.*',
        '10.0.64-127.*',
        '10.0.128-255.*',
    ]


def test_glob_to_iprange():
    assert glob_to_iprange('192.0.2.*') == IPRange('192.0.2.0', '192.0.2.255')
    assert glob_to_iprange('192.0.2.1-15') == IPRange('192.0.2.1', '192.0.2.15')
    assert glob_to_iprange('192.0.1-3.*') == IPRange('192.0.1.0', '192.0.3.255')


def test_invalid_glob():
    assert not valid_glob('1.1.1.a')
    assert not valid_glob('1.1.1.1/32')
    assert not valid_glob('1.1.1.a-b')
    assert not valid_glob('1.1.a-b.*')
