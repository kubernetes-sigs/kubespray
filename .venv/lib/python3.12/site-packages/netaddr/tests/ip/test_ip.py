import weakref

import pytest

from netaddr import INET_ATON, INET_PTON, IPAddress, IPNetwork, IPRange, NOHOST


def test_ip_classes_are_weak_referencable():
    weakref.ref(IPAddress('10.0.0.1'))
    weakref.ref(IPNetwork('10.0.0.1/8'))
    weakref.ref(IPRange('10.0.0.1', '10.0.0.10'))


@pytest.mark.parametrize('flags', [NOHOST, INET_ATON | INET_PTON])
def test_invalid_ipaddress_flags_are_rejected(flags):
    with pytest.raises(ValueError):
        IPAddress('1.2.3.4', flags=flags)


def test_invalid_ipnetwork_flags_are_rejected():
    with pytest.raises(ValueError):
        IPNetwork('1.2.0.0/16', flags=INET_PTON)
