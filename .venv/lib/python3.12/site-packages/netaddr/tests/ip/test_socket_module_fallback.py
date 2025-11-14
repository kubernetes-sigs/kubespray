import pytest

from netaddr.fbsocket import inet_ntop, inet_pton, inet_ntoa, AF_INET, AF_INET6


@pytest.mark.parametrize(
    ('actual', 'expected'),
    [
        ('0:0:0:0:0:0:0:0', '::'),
        ('0:0:0:0:0:0:0:A', '::a'),
        ('A:0:0:0:0:0:0:0', 'a::'),
        ('A:0:A:0:0:0:0:0', 'a:0:a::'),
        ('A:0:0:0:0:0:0:A', 'a::a'),
        ('0:A:0:0:0:0:0:A', '0:a::a'),
        ('A:0:A:0:0:0:0:A', 'a:0:a::a'),
        ('0:0:0:A:0:0:0:A', '::a:0:0:0:a'),
        ('0:0:0:0:A:0:0:A', '::a:0:0:a'),
        ('A:0:0:0:0:A:0:A', 'a::a:0:a'),
        ('A:0:0:A:0:0:A:0', 'a::a:0:0:a:0'),
        ('A:0:A:0:A:0:A:0', 'a:0:a:0:a:0:a:0'),
        ('0:A:0:A:0:A:0:A', '0:a:0:a:0:a:0:a'),
        ('1080:0:0:0:8:800:200C:417A', '1080::8:800:200c:417a'),
        ('FEDC:BA98:7654:3210:FEDC:BA98:7654:3210', 'fedc:ba98:7654:3210:fedc:ba98:7654:3210'),
    ],
)
def test_inet_ntop_and_inet_pton_ipv6_conversion(actual, expected):
    assert inet_ntop(AF_INET6, inet_pton(AF_INET6, actual)) == expected


def test_inet_ntoa_ipv4_exceptions():
    with pytest.raises(TypeError):
        inet_ntoa(1)

    with pytest.raises(ValueError):
        inet_ntoa('\x00')


def test_inet_pton_ipv4_exceptions():
    with pytest.raises(OSError):
        inet_pton(AF_INET, '::0x07f')

    with pytest.raises(TypeError):
        inet_pton(AF_INET, 1)


def test_inet_pton_ipv6_exceptions():
    with pytest.raises(OSError):
        inet_pton(AF_INET6, '::0x07f')

    with pytest.raises(TypeError):
        inet_pton(AF_INET6, 1)
