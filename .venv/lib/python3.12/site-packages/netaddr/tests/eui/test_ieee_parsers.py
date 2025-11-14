import contextlib
from io import StringIO

from netaddr.compat import _open_binary
from netaddr.eui.ieee import OUIIndexParser, IABIndexParser, FileIndexer


def test_oui_parser():
    outfile = StringIO()
    with contextlib.closing(_open_binary(__package__, 'sample_oui.txt')) as infile:
        iab_parser = OUIIndexParser(infile)
        iab_parser.attach(FileIndexer(outfile))
        iab_parser.parse()
    assert outfile.getvalue() == '51966,1,138\n'


def test_iab_parser():
    outfile = StringIO()
    with contextlib.closing(_open_binary(__package__, 'sample_iab.txt')) as infile:
        iab_parser = IABIndexParser(infile)
        iab_parser.attach(FileIndexer(outfile))
        iab_parser.parse()
    assert outfile.getvalue() == '84683452,1,181\n'
