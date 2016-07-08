#!/usr/bin/env python

# A simple dynamic replacemant of 'kargo prepare'
# Generates ansible inventory from a list of IPs in 'nodes' file.

import argparse
import json

def read_nodes_from_file(filename):
    f = open(filename, 'r')
    content = [x.strip('\n') for x in f.readlines()]
    return content

def nodes_to_hash(nodes_list, masters):
    nodes = {
          'all': {
              'hosts': [],
          },
          'etcd': {
              'hosts': [],
          },
          'kube-master': {
              'hosts': [],
          },
          'kube-node': {
              'hosts': [],
          },
          'k8s-cluster': {
              'children': ['kube-node', 'kube-master']
          }
        }

    for node_ip in nodes_list:
        nodes['all']['hosts'].append("%s" % node_ip)
        nodes['kube-node']['hosts'].append("%s" % node_ip)
        if i <= masters:
            nodes['kube-master']['hosts'].append("%s" % node_ip)
        if i <= 3:
            nodes['etcd']['hosts'].append("%s" % node_ip)

    return nodes

def main():
    parser = argparse.ArgumentParser(description='Ansible dynamic inventory')
    parser.add_argument('--nodes', help='File with list of nodes, one IP per line', default='nodes')
    parser.add_argument('--masters', type=int, help='Number of master nodes, will be taken from the top of list', default=2)
    parser.add_argument('--list', action='store_true')
    parser.add_argument('--host', default=False)
    args = parser.parse_args()

    nodes_list = read_nodes_from_file(args.nodes)

    if len(nodes_list) < 3:
        print "Error: requires at least 3 nodes"
        return

    nodes = nodes_to_hash(nodes_list, args.masters)

    if args.host:
        print "{}"
    else:
        print json.dumps(nodes)

if __name__ == "__main__":
    main()
