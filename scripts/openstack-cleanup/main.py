#!/usr/bin/env python
import argparse
import openstack
import logging
import datetime
import time
from pprint import pprint

DATE_FORMAT = '%Y-%m-%dT%H:%M:%SZ'
PAUSE_SECONDS = 5

log = logging.getLogger('openstack-cleanup')

parser = argparse.ArgumentParser(description='Cleanup OpenStack VMs')

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
        print('This will delete VMs... (ctrl+c to cancel)')
        time.sleep(PAUSE_SECONDS)

    conn = openstack.connect()
    for server in conn.compute.servers():
        created_at = datetime.datetime.strptime(server.created_at, DATE_FORMAT)
        if created_at < oldest_allowed:
            print('Will delete server %(name)s' % server)
            if not args.dry_run:
                conn.compute.delete_server(server)


if __name__ == '__main__':
    # execute only if run as a script
    main()
