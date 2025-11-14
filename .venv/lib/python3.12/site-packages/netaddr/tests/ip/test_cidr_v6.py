from netaddr import iprange_to_cidrs, IPNetwork, cidr_merge, all_matching_cidrs


def test_iprange_to_cidrs_worst_case_v6():
    networks = iprange_to_cidrs('::ffff:1', '::ffff:255.255.255.254')
    assert networks == [
        IPNetwork('::255.255.0.1/128'),
        IPNetwork('::255.255.0.2/127'),
        IPNetwork('::255.255.0.4/126'),
        IPNetwork('::255.255.0.8/125'),
        IPNetwork('::255.255.0.16/124'),
        IPNetwork('::255.255.0.32/123'),
        IPNetwork('::255.255.0.64/122'),
        IPNetwork('::255.255.0.128/121'),
        IPNetwork('::255.255.1.0/120'),
        IPNetwork('::255.255.2.0/119'),
        IPNetwork('::255.255.4.0/118'),
        IPNetwork('::255.255.8.0/117'),
        IPNetwork('::255.255.16.0/116'),
        IPNetwork('::255.255.32.0/115'),
        IPNetwork('::255.255.64.0/114'),
        IPNetwork('::255.255.128.0/113'),
        IPNetwork('::1:0:0/96'),
        IPNetwork('::2:0:0/95'),
        IPNetwork('::4:0:0/94'),
        IPNetwork('::8:0:0/93'),
        IPNetwork('::10:0:0/92'),
        IPNetwork('::20:0:0/91'),
        IPNetwork('::40:0:0/90'),
        IPNetwork('::80:0:0/89'),
        IPNetwork('::100:0:0/88'),
        IPNetwork('::200:0:0/87'),
        IPNetwork('::400:0:0/86'),
        IPNetwork('::800:0:0/85'),
        IPNetwork('::1000:0:0/84'),
        IPNetwork('::2000:0:0/83'),
        IPNetwork('::4000:0:0/82'),
        IPNetwork('::8000:0:0/82'),
        IPNetwork('::c000:0:0/83'),
        IPNetwork('::e000:0:0/84'),
        IPNetwork('::f000:0:0/85'),
        IPNetwork('::f800:0:0/86'),
        IPNetwork('::fc00:0:0/87'),
        IPNetwork('::fe00:0:0/88'),
        IPNetwork('::ff00:0:0/89'),
        IPNetwork('::ff80:0:0/90'),
        IPNetwork('::ffc0:0:0/91'),
        IPNetwork('::ffe0:0:0/92'),
        IPNetwork('::fff0:0:0/93'),
        IPNetwork('::fff8:0:0/94'),
        IPNetwork('::fffc:0:0/95'),
        IPNetwork('::fffe:0:0/96'),
        IPNetwork('::ffff:0.0.0.0/97'),
        IPNetwork('::ffff:128.0.0.0/98'),
        IPNetwork('::ffff:192.0.0.0/99'),
        IPNetwork('::ffff:224.0.0.0/100'),
        IPNetwork('::ffff:240.0.0.0/101'),
        IPNetwork('::ffff:248.0.0.0/102'),
        IPNetwork('::ffff:252.0.0.0/103'),
        IPNetwork('::ffff:254.0.0.0/104'),
        IPNetwork('::ffff:255.0.0.0/105'),
        IPNetwork('::ffff:255.128.0.0/106'),
        IPNetwork('::ffff:255.192.0.0/107'),
        IPNetwork('::ffff:255.224.0.0/108'),
        IPNetwork('::ffff:255.240.0.0/109'),
        IPNetwork('::ffff:255.248.0.0/110'),
        IPNetwork('::ffff:255.252.0.0/111'),
        IPNetwork('::ffff:255.254.0.0/112'),
        IPNetwork('::ffff:255.255.0.0/113'),
        IPNetwork('::ffff:255.255.128.0/114'),
        IPNetwork('::ffff:255.255.192.0/115'),
        IPNetwork('::ffff:255.255.224.0/116'),
        IPNetwork('::ffff:255.255.240.0/117'),
        IPNetwork('::ffff:255.255.248.0/118'),
        IPNetwork('::ffff:255.255.252.0/119'),
        IPNetwork('::ffff:255.255.254.0/120'),
        IPNetwork('::ffff:255.255.255.0/121'),
        IPNetwork('::ffff:255.255.255.128/122'),
        IPNetwork('::ffff:255.255.255.192/123'),
        IPNetwork('::ffff:255.255.255.224/124'),
        IPNetwork('::ffff:255.255.255.240/125'),
        IPNetwork('::ffff:255.255.255.248/126'),
        IPNetwork('::ffff:255.255.255.252/127'),
        IPNetwork('::ffff:255.255.255.254/128'),
    ]


def test_rfc_4291():
    assert str(IPNetwork('2001:0DB8:0000:CD30:0000:0000:0000:0000/60')) == '2001:db8:0:cd30::/60'
    assert str(IPNetwork('2001:0DB8::CD30:0:0:0:0/60')) == '2001:db8:0:cd30::/60'
    assert str(IPNetwork('2001:0DB8:0:CD30::/60')) == '2001:db8:0:cd30::/60'


def test_whole_network_cidr_merge_v6():
    assert cidr_merge(['::/0', 'fe80::1']) == [IPNetwork('::/0')]
    assert cidr_merge(['::/0', '::']) == [IPNetwork('::/0')]
    assert cidr_merge(['::/0', '::192.0.2.0/124', 'ff00::101']) == [IPNetwork('::/0')]
    assert cidr_merge(['0.0.0.0/0', '0.0.0.0', '::/0', '::']) == [
        IPNetwork('0.0.0.0/0'),
        IPNetwork('::/0'),
    ]


def test_all_matching_cidrs_v6():
    assert all_matching_cidrs('::ffff:192.0.2.1', ['::ffff:192.0.2.0/96']) == [
        IPNetwork('::ffff:192.0.2.0/96')
    ]
    assert all_matching_cidrs('::192.0.2.1', ['::192.0.2.0/96']) == [IPNetwork('::192.0.2.0/96')]
    assert all_matching_cidrs('::192.0.2.1', ['192.0.2.0/23']) == []
    assert all_matching_cidrs('::192.0.2.1', ['192.0.2.0/24', '::192.0.2.0/120']) == [
        IPNetwork('::192.0.2.0/120')
    ]
    assert all_matching_cidrs(
        '::192.0.2.1', [IPNetwork('192.0.2.0/24'), IPNetwork('::192.0.2.0/120')]
    ) == [IPNetwork('::192.0.2.0/120')]
