#!/usr/bin/env python

import json
import os
import sys

if (not os.environ.get('MITOGEN_GCLOUD_GROUP')) or any('--host' in s for s in sys.argv):
    sys.stdout.write('{}')
    sys.exit(0)

import googleapiclient.discovery


def main():
    project = 'mitogen-load-testing'
    zone = 'europe-west1-d'
    group_name = 'micro-debian9'

    client = googleapiclient.discovery.build('compute', 'v1')
    resp = client.instances().list(project=project, zone=zone).execute()

    ips = []
    for inst in resp['items']:
        if inst['status'] == 'RUNNING' and inst['name'].startswith(group_name):
            ips.extend(
                #bytes(config['natIP'])
                bytes(interface['networkIP'])
                for interface in inst['networkInterfaces']
                #for config in interface['accessConfigs']
            )

    sys.stderr.write('Addresses: %s\n' % (ips,))
    gname = os.environ['MITOGEN_GCLOUD_GROUP']
    groups = {
        gname: {
            'hosts': ips
        }
    }

    for i in 1, 10, 20, 50, 100:
        groups['%s-%s' % (gname, i)] = {
            'hosts': ips[:i]
        }

    sys.stdout.write(json.dumps(groups, indent=4))


if __name__ == '__main__':
    main()
