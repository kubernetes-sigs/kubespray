from netaddr.strategy import eui48


def test_strategy_eui48():
    b = '00000000-00001111-00011111-00010010-11100111-00110011'
    i = 64945841971
    t = (0x0, 0x0F, 0x1F, 0x12, 0xE7, 0x33)
    s = '00-0F-1F-12-E7-33'
    p = b'\x00\x0f\x1f\x12\xe73'

    assert eui48.bits_to_int(b) == i
    assert eui48.int_to_bits(i) == b

    assert eui48.int_to_str(i) == s
    assert eui48.str_to_int(s) == i

    assert eui48.int_to_words(i) == t
    assert eui48.words_to_int(t) == i
    assert eui48.words_to_int(list(t)) == i

    assert eui48.int_to_packed(i) == p
    assert eui48.packed_to_int(p) == i


def test_strategy_eui48_alternate_dialect():
    b = '00000000:00001111:00011111:00010010:11100111:00110011'
    i = 64945841971
    t = (0x0, 0x0F, 0x1F, 0x12, 0xE7, 0x33)
    s = '0:f:1f:12:e7:33'

    assert eui48.bits_to_int(b, eui48.mac_unix) == i
    assert eui48.int_to_bits(i, eui48.mac_unix) == b

    assert eui48.int_to_str(i, eui48.mac_unix) == s
    assert eui48.int_to_str(i, eui48.mac_cisco) == '000f.1f12.e733'
    assert eui48.int_to_str(i, eui48.mac_unix) == '0:f:1f:12:e7:33'
    assert eui48.int_to_str(i, eui48.mac_unix_expanded) == '00:0f:1f:12:e7:33'
    assert eui48.str_to_int(s) == i

    assert eui48.int_to_words(i, eui48.mac_unix) == t
    assert eui48.words_to_int(t, eui48.mac_unix) == i
    assert eui48.words_to_int(list(t), eui48.mac_unix) == i
