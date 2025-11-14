#!/usr/bin/env python
# -----------------------------------------------------------------------------
#   Copyright (c) 2008 by David P. D. Moss. All rights reserved.
#
#   Released under the BSD license. See the LICENSE file for details.
# -----------------------------------------------------------------------------
"""an interactive shell for the netaddr library"""

import argparse
import sys

import netaddr
from netaddr import AddrFormatError, IPAddress, IPNetwork

SHELL_NAMESPACE = {
    **{name: getattr(netaddr, name) for name in dir(netaddr) if name in netaddr.__all__},
    #   aliases to save some typing ...
    'IP': netaddr.IPAddress,
    'CIDR': netaddr.IPNetwork,
    'MAC': netaddr.EUI,
}

ASCII_ART_LOGO = r"""               __            __    __
   ____  ___  / /_____ _____/ /___/ /____
  / __ \/ _ \/ __/ __ `/ __  / __  / ___/
 / / / /  __/ /_/ /_/ / /_/ / /_/ / /
/_/ /_/\___/\__/\__,_/\__,_/\__,_/_/
"""


def main():
    print(ASCII_ART_LOGO)

    parser = argparse.ArgumentParser(
        prog='netaddr', description='The netaddr CLI tool', epilog='Share and enjoy!'
    )
    subparsers = parser.add_subparsers(dest='command')
    subparsers.default = 'shell'
    shell_parser = subparsers.add_parser(
        'shell', help='Start an interactive shell (the default subcommand)'
    )
    parser_info = subparsers.add_parser('info', help='Display information about an IP network')
    parser_info.add_argument('network', help='The IP network to display')
    args = parser.parse_args()

    if args.command == 'shell':
        shell()
    elif args.command == 'info':
        info(args.network)
    else:
        print(f'Unknown command {args.command}, should not happen')
        sys.exit(1)


def shell() -> None:
    banner = r"""netaddr shell %s - %s
""" % (netaddr.__version__, __doc__)
    exit_msg = '\nShare and enjoy!'

    try:
        from IPython.terminal.embed import InteractiveShellEmbed

        def shell(namespace, banner, exit_msg):
            InteractiveShellEmbed(banner1=banner, exit_msg=exit_msg, user_ns=SHELL_NAMESPACE)()
    except ImportError:
        notice = 'Using built-in Python REPL. You can install IPython for better experience.'
        print()
        import code

        def shell(namespace, banner, exit_msg):
            code.interact('\n'.join([banner, notice, '']), local=namespace, exitmsg=exit_msg)

    shell(locals(), banner, exit_msg)


def info(network_input: str) -> None:
    try:
        network = IPNetwork(network_input).cidr
    except AddrFormatError as e:
        print(f'{network_input} is not a valid network')
        sys.exit(1)

    print('IP network information')
    print()

    first_usable, last_usable = network._usable_range()
    output = {
        'CIDR': str(network),
        'Network IP': network.network,
        'Network IP (binary)': network.network.bits(),
        'Network IP (decimal)': int(network.network),
        'Network IP (hex)': hex(network.network),
        'Subnet mask': network.netmask,
        'Subnet mask (binary)': network.netmask.bits(),
        'Broadcast IP': network.broadcast if network.version == 4 else 'N/A',
        'Range': f'{IPAddress(network.first)}-{IPAddress(network.last)}',
        'Total addresses': network.size,
        'Usable range': f'{IPAddress(first_usable)}-{IPAddress(last_usable)}',
        'Usable addresses': last_usable - first_usable + 1,
    }
    label_width = max(len(label) for label in output) + 4
    for label, value in output.items():
        print(f'{label}{" " * (label_width - len(label))} {value}')


if __name__ == '__main__':
    main()
