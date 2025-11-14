from netaddr import IPAddress


def test_reverse_dns_v4():
    assert IPAddress('172.24.0.13').reverse_dns == '13.0.24.172.in-addr.arpa.'


def test_reverse_dns_v6():
    assert IPAddress('fe80::feeb:daed').reverse_dns == (
        'd.e.a.d.b.e.e.f.0.0.0.0.0.0.0.0.' '0.0.0.0.0.0.0.0.0.0.0.0.0.8.e.f.' 'ip6.arpa.'
    )
