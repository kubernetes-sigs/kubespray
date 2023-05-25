#!/usr/bin/env python
import argparse
import openstack
import logging
import datetime
import time

DATE_FORMAT = '%Y-%m-%dT%H:%M:%SZ'
PAUSE_SECONDS = 5

log = logging.getLogger('openstack-cleanup')

parser = argparse.ArgumentParser(description='Cleanup OpenStack resources')

parser.add_argument('-v', '--verbose', action='store_true',
                    help='Increase verbosity')
parser.add_argument('--hours', type=int, default=4,
                    help='Age (in hours) of VMs to cleanup (default: 4h)')
parser.add_argument('--dry-run', action='store_true',
                    help='Do not delete anything')

args = parser.parse_args()

oldest_allowed = datetime.datetime.now() - datetime.timedelta(hours=args.hours)


def main():
    if args.dry_run:
        print('Running in dry-run mode')
    else:
        print('This will delete resources... (ctrl+c to cancel)')
        time.sleep(PAUSE_SECONDS)

    conn = openstack.connect()

    print('Servers...')
    map_if_old(conn.compute.delete_server,
               conn.compute.servers())

    print('Security groups...')
    map_if_old(conn.network.delete_security_group,
               conn.network.security_groups())

    print('Ports...')
    try:
        map_if_old(conn.network.delete_port,
                   conn.network.ports())
    except openstack.exceptions.ConflictException as ex:
        # Need to find subnet-id which should be removed from a router
        for sn in conn.network.subnets():
            try:
                fn_if_old(conn.network.delete_subnet, sn)
            except openstack.exceptions.ConflictException:
                for r in conn.network.routers():
                    print("Deleting subnet %s from router %s", sn, r)
                    try:
                        conn.network.remove_interface_from_router(
                            r, subnet_id=sn.id)
                    except Exception as ex:
                        print("Failed to delete subnet from router as %s", ex)

        for ip in conn.network.ips():
            fn_if_old(conn.network.delete_ip, ip)
                
        # After removing unnecessary subnet from router, retry to delete ports
        map_if_old(conn.network.delete_port,
                   conn.network.ports())

    print('Subnets...')
    map_if_old(conn.network.delete_subnet,
               conn.network.subnets())

    print('Networks...')
    for n in conn.network.networks():
        if not n.is_router_external:
            fn_if_old(conn.network.delete_network, n)


# runs the given fn to all elements of the that are older than allowed
def map_if_old(fn, items):
    for item in items:
        fn_if_old(fn, item)


# run the given fn function only if the passed item is older than allowed
def fn_if_old(fn, item):
    created_at = datetime.datetime.strptime(item.created_at, DATE_FORMAT)
    if item.name == "default":  # skip default security group
        return
    if created_at < oldest_allowed:
        print('Will delete %(name)s (%(id)s)' % item)
        if not args.dry_run:
            fn(item)


if __name__ == '__main__':
    # execute only if run as a script
    main()
