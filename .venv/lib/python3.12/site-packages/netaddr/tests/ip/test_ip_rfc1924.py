import pytest

from netaddr import AddrFormatError
from netaddr.ip.rfc1924 import ipv6_to_base85, base85_to_ipv6


def test_RFC_1924():
    ip_addr = '1080::8:800:200c:417a'
    base85 = ipv6_to_base85(ip_addr)
    assert base85 == '4)+k&C#VzJ4br>0wv%Yp'
    assert base85_to_ipv6(base85) == '1080::8:800:200c:417a'

    #   RFC specifies that "leading zeroes are never omitted"
    ipv6_to_base85('::1') == '00000000000000000001'

    with pytest.raises(AddrFormatError):
        base85_to_ipv6('not 20 chars')
