import pickle
import random

from netaddr import (
    EUI,
    mac_unix,
    mac_unix_expanded,
    mac_cisco,
    mac_bare,
    mac_pgsql,
    eui64_unix,
    eui64_unix_expanded,
    eui64_cisco,
    eui64_bare,
    OUI,
    IAB,
    IPAddress,
)


def test_mac_address_properties():
    mac = EUI('00-1B-77-49-54-FD')
    assert repr(mac) == "EUI('00-1B-77-49-54-FD')"
    assert str(mac)
    assert str(mac.oui) == '00-1B-77'
    assert mac.ei == '49-54-FD'
    assert mac.version == 48


def test_mac_address_numerical_operations():
    mac = EUI('00-1B-77-49-54-FD')
    assert int(mac) == 117965411581
    assert hex(mac) == '0x1b774954fd'
    assert mac.bits() == '00000000-00011011-01110111-01001001-01010100-11111101'
    assert mac.bin == '0b1101101110111010010010101010011111101'


def test_eui_oct_format():
    assert oct(EUI('00-1B-77-49-54-FD')) == '0o1556722252375'


def test_eui_constructor():
    assert str(EUI('00-1B-77-49-54-FD')) == '00-1B-77-49-54-FD'
    assert str(EUI('00-1b-77-49-54-fd')) == '00-1B-77-49-54-FD'
    assert str(EUI('0:1b:77:49:54:fd')) == '00-1B-77-49-54-FD'
    assert str(EUI('001b:7749:54fd')) == '00-1B-77-49-54-FD'
    assert str(EUI('1b:7749:54fd')) == '00-1B-77-49-54-FD'
    assert str(EUI('1B:7749:54FD')) == '00-1B-77-49-54-FD'
    assert str(EUI('001b774954fd')) == '00-1B-77-49-54-FD'
    assert str(EUI('01B774954FD')) == '00-1B-77-49-54-FD'
    assert str(EUI('001B77:4954FD')) == '00-1B-77-49-54-FD'

    eui = EUI('00-90-96-AF-CC-39')

    assert eui == EUI('0-90-96-AF-CC-39')
    assert eui == EUI('00-90-96-af-cc-39')
    assert eui == EUI('00:90:96:AF:CC:39')
    assert eui == EUI('00:90:96:af:cc:39')
    assert eui == EUI('0090-96AF-CC39')
    assert eui == EUI('0090:96af:cc39')
    assert eui == EUI('009096-AFCC39')
    assert eui == EUI('009096:AFCC39')
    assert eui == EUI('009096AFCC39')
    assert eui == EUI('009096afcc39')
    assert EUI('01-00-00-00-00-00') == EUI('010000000000')
    assert EUI('01-00-00-00-00-00') == EUI('10000000000')
    assert EUI('01-00-00-01-00-00') == EUI('010000:010000')
    assert EUI('01-00-00-01-00-00') == EUI('10000:10000')


def test_eui_dialects():
    mac = EUI('00-1B-77-49-54-FD')
    assert str(mac) == '00-1B-77-49-54-FD'

    mac = EUI('00-1B-77-49-54-FD', dialect=mac_unix)
    assert str(mac) == '0:1b:77:49:54:fd'

    mac = EUI('00-1B-77-49-54-FD', dialect=mac_unix_expanded)
    assert str(mac) == '00:1b:77:49:54:fd'

    mac = EUI('00-1B-77-49-54-FD', dialect=mac_cisco)
    assert str(mac) == '001b.7749.54fd'

    mac = EUI('00-1B-77-49-54-FD', dialect=mac_bare)
    assert str(mac) == '001B774954FD'

    mac = EUI('00-1B-77-49-54-FD', dialect=mac_pgsql)
    assert str(mac) == '001b77:4954fd'


def test_eui_dialect_property_assignment():
    mac = EUI('00-1B-77-49-54-FD')
    assert str(mac) == '00-1B-77-49-54-FD'

    mac.dialect = mac_pgsql
    assert str(mac) == '001b77:4954fd'


def test_eui_copy_constructor_dialect_support():
    mac = EUI('00-1B-77-49-54-FD')
    copy = EUI(mac, dialect=mac_unix_expanded)
    assert str(copy) == '00:1b:77:49:54:fd'


def test_eui_format():
    mac = EUI('00-1B-77-49-54-FD')
    assert mac.format() == '00-1B-77-49-54-FD'
    assert mac.format(mac_pgsql) == '001b77:4954fd'
    assert mac.format(mac_unix_expanded) == '00:1b:77:49:54:fd'


def test_eui_custom_dialect():
    class mac_custom(mac_unix):
        word_fmt = '%.2X'

    mac = EUI('00-1B-77-49-54-FD', dialect=mac_custom)
    assert str(mac) == '00:1B:77:49:54:FD'


def test_eui64_dialects():
    mac = EUI('00-1B-77-49-54-FD-12-34')
    assert str(mac) == '00-1B-77-49-54-FD-12-34'

    mac = EUI('00-1B-77-49-54-FD-12-34', dialect=eui64_unix)
    assert str(mac) == '0:1b:77:49:54:fd:12:34'

    mac = EUI('00-1B-77-49-54-FD-12-34', dialect=eui64_unix_expanded)
    assert str(mac) == '00:1b:77:49:54:fd:12:34'

    mac = EUI('00-1B-77-49-54-FD-12-34', dialect=eui64_cisco)
    assert str(mac) == '001b.7749.54fd.1234'

    mac = EUI('00-1B-77-49-54-FD-12-34', dialect=eui64_bare)
    assert str(mac) == '001B774954FD1234'


def test_eui64_dialect_property_assignment():
    mac = EUI('00-1B-77-49-54-FD-12-34')
    assert str(mac) == '00-1B-77-49-54-FD-12-34'

    mac.dialect = eui64_cisco
    assert str(mac) == '001b.7749.54fd.1234'


def test_eui64_custom_dialect():
    class eui64_custom(eui64_unix):
        word_fmt = '%.2X'

    mac = EUI('00-1B-77-49-54-FD-12-34', dialect=eui64_custom)
    assert str(mac) == '00:1B:77:49:54:FD:12:34'


def test_eui_oui_information():
    mac = EUI('00-1B-77-49-54-FD')
    oui = mac.oui
    assert str(oui) == '00-1B-77'

    assert oui.registration().address == ['Lot 8, Jalan Hi-Tech 2/3', 'Kulim  Kedah  09000', 'MY']

    assert oui.registration().org == 'Intel Corporate'


def test_oui_constructor():
    oui = OUI(524336)
    assert str(oui) == '08-00-30'
    assert oui == OUI('08-00-30')

    assert oui.registration(0).address == ['2380 N. ROSE AVENUE', 'OXNARD  CA  93010', 'US']
    assert oui.registration(0).org == 'NETWORK RESEARCH CORPORATION'
    assert oui.registration(0).oui == '08-00-30'

    assert oui.registration(1).address == [
        'GPO BOX 2476V',
        'MELBOURNE  VIC  3001',
        'AU',
    ]
    assert oui.registration(1).org == 'ROYAL MELBOURNE INST OF TECH'
    assert oui.registration(1).oui == '08-00-30'

    assert oui.registration(2).address == ['CH-1211', 'GENEVE  SUISSE/SWITZ  023', 'CH']
    assert oui.registration(2).org == 'CERN'
    assert oui.registration(2).oui == '08-00-30'
    assert oui.reg_count == 3


def test_oui_hash():
    oui0 = OUI(0)
    oui1 = OUI(1)
    oui_dict = {oui0: None, oui1: None}

    assert list(oui_dict.keys()) == [OUI(0), OUI(1)]


def test_eui_iab():
    mac = EUI('00-50-C2-00-0F-01')
    assert mac.is_iab()

    iab = mac.iab
    assert str(iab) == '00-50-C2-00-00-00'
    assert iab == IAB('00-50-C2-00-00-00')

    reg_info = iab.registration()

    assert reg_info.address == [
        '1241 Superieor Ave E',
        'Cleveland  OH  44114',
        'US',
    ]

    assert reg_info.iab == '00-50-C2-00-00-00'
    assert reg_info.org == 'T.L.S. Corp.'


def test_eui64():
    eui = EUI('00-1B-77-FF-FE-49-54-FD')
    assert eui == EUI('00-1B-77-FF-FE-49-54-FD')
    assert eui.oui == OUI('00-1B-77')
    assert eui.ei == 'FF-FE-49-54-FD'
    assert eui.eui64() == EUI('00-1B-77-FF-FE-49-54-FD')


def test_mac_to_ipv6_link_local():
    mac = EUI('00-0F-1F-12-E7-33')
    ip = mac.ipv6_link_local()
    assert ip == IPAddress('fe80::20f:1fff:fe12:e733')
    assert ip.is_link_local()
    assert mac.eui64() == EUI('00-0F-1F-FF-FE-12-E7-33')


def test_iab():
    eui = EUI('00-50-C2-05-C0-00')

    assert eui.is_iab()
    assert str(eui.oui) == '00-50-C2'
    assert str(eui.iab) == '00-50-C2-05-C0-00'
    assert eui.ei == '05-C0-00'
    assert int(eui.oui) == 0x0050C2
    assert int(eui.iab) == 0x0050C205C

    assert IAB(eui.value) == eui.iab


def test_new_iab():
    eui = EUI('40-D8-55-13-10-00')

    assert eui.is_iab()
    assert str(eui.oui) == '40-D8-55'
    assert str(eui.iab) == '40-D8-55-13-10-00'
    assert eui.ei == '13-10-00'
    assert int(eui.oui) == 0x40D855
    assert int(eui.iab) == 0x40D855131

    assert IAB(eui.value) == eui.iab


def test_eui48_vs_eui64():
    eui48 = EUI('01-00-00-01-00-00')
    assert int(eui48) == 1099511693312

    eui64 = EUI('00-00-01-00-00-01-00-00')
    assert int(eui64) == 1099511693312
    assert eui48 != eui64


def test_eui_sort_order():
    eui_list = [
        EUI(0, 64),
        EUI(0),
        EUI(0xFFFFFFFFFFFF, dialect=mac_unix),
        EUI(0x1000000000000),
    ]

    random.shuffle(eui_list)
    eui_list.sort()

    assert [(str(eui), eui.version) for eui in eui_list] == [
        ('00-00-00-00-00-00', 48),
        ('ff:ff:ff:ff:ff:ff', 48),
        ('00-00-00-00-00-00-00-00', 64),
        ('00-01-00-00-00-00-00-00', 64),
    ]


def test_eui_pickle_support():
    eui1 = EUI('00-00-00-01-02-03')
    eui2 = pickle.loads(pickle.dumps(eui1))
    assert eui1 == eui2

    eui1 = EUI('00-00-00-01-02-03', dialect=mac_cisco)
    eui2 = pickle.loads(pickle.dumps(eui1))
    assert eui1 == eui2
    assert eui1.dialect == eui2.dialect

    oui1 = EUI('00-00-00-01-02-03').oui
    oui2 = pickle.loads(pickle.dumps(oui1))
    assert oui1 == oui2
    assert oui1.records == oui2.records

    iab1 = EUI('00-50-C2-00-1F-FF').iab
    iab2 = pickle.loads(pickle.dumps(iab1))
    assert iab1 == iab2
    assert iab1.record == iab2.record


def test_mac_to_eui64_conversion():
    mac = EUI('00-1B-77-49-54-FD')
    assert mac == EUI('00-1B-77-49-54-FD')

    eui = mac.eui64()
    assert eui == EUI('00-1B-77-FF-FE-49-54-FD')
    eui.eui64() == EUI('00-1B-77-FF-FE-49-54-FD')

    assert int(eui) == 7731765737772285
    assert eui.packed == b'\x00\x1bw\xff\xfeIT\xfd'
    assert eui.bin == '0b11011011101111111111111111110010010010101010011111101'
    assert eui.bits() == '00000000-00011011-01110111-11111111-11111110-01001001-01010100-11111101'


def test_mac_to_ipv6():
    mac = EUI('00-1B-77-49-54-FD')
    eui = mac.eui64()
    assert mac == EUI('00-1B-77-49-54-FD')
    assert eui == EUI('00-1B-77-FF-FE-49-54-FD')

    assert mac.modified_eui64() == EUI('02-1B-77-FF-FE-49-54-FD')
    assert mac.ipv6_link_local() == IPAddress('fe80::21b:77ff:fe49:54fd')
    assert eui.ipv6_link_local() == IPAddress('fe80::21b:77ff:fe49:54fd')

    assert mac.ipv6(0x12340000000000000000000000000000) == IPAddress('1234::21b:77ff:fe49:54fd')
    assert eui.ipv6(0x12340000000000000000000000000000) == IPAddress('1234::21b:77ff:fe49:54fd')


def test_eui64_constructor():
    addr_colons = EUI('00:1B:77:49:54:FD:BB:34')
    assert addr_colons == EUI('00-1B-77-49-54-FD-BB-34')

    addr_no_delimiter = EUI('001B774954FDBB34')
    assert addr_no_delimiter == EUI('00-1B-77-49-54-FD-BB-34')
