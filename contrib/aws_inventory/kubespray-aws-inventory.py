#!/usr/bin/env python

from __future__ import print_function
import boto3
import os
import argparse
import json

class SearchEC2Tags(object):

  def __init__(self):
    self.parse_args()
    if self.args.list:
      self.search_tags()
    if self.args.host:
      data = {}
      print(json.dumps(data, indent=2))

  def parse_args(self):

    ##Check if VPC_VISIBILITY is set, if not default to private
    if "VPC_VISIBILITY" in os.environ:
      self.vpc_visibility = os.environ['VPC_VISIBILITY']
    else:
      self.vpc_visibility = "private"

    ##Support --list and --host flags. We largely ignore the host one.
    parser = argparse.ArgumentParser()
    parser.add_argument('--list', action='store_true', default=False, help='List instances')
    parser.add_argument('--host', action='store_true', help='Get all the variables about a specific instance')
    self.args = parser.parse_args()

  def search_tags(self):
    hosts = {}
    hosts['_meta'] = { 'hostvars': {} }

    ##Search ec2 three times to find nodes of each group type. Relies on kubespray-role key/value.
    for group in ["kube_control_plane", "kube_node", "etcd"]:
      hosts[group] = []
      tag_key = "kubespray-role"
      tag_value = ["*"+group+"*"]
      region = os.environ['REGION']

      ec2 = boto3.resource('ec2', region)
      filters = [{'Name': 'tag:'+tag_key, 'Values': tag_value}, {'Name': 'instance-state-name', 'Values': ['running']}]
      cluster_name = os.getenv('CLUSTER_NAME')
      if cluster_name:
        filters.append({'Name': 'tag-key', 'Values': ['kubernetes.io/cluster/'+cluster_name]})
      instances = ec2.instances.filter(Filters=filters)
      for instance in instances:

        ##Suppose default vpc_visibility is private
        dns_name = instance.private_dns_name
        ansible_host = {
          'ansible_ssh_host': instance.private_ip_address
        }

        ##Override when vpc_visibility actually is public
        if self.vpc_visibility == "public":
          dns_name = instance.public_dns_name
          ansible_host = {
            'ansible_ssh_host': instance.public_ip_address
          }

        ##Set when instance actually has node_labels
        node_labels_tag = list(filter(lambda t: t['Key'] == 'kubespray-node-labels', instance.tags))
        if node_labels_tag:
          ansible_host['node_labels'] = dict([ label.strip().split('=') for label in node_labels_tag[0]['Value'].split(',') ])

        hosts[group].append(dns_name)
        hosts['_meta']['hostvars'][dns_name] = ansible_host

    hosts['k8s_cluster'] = {'children':['kube_control_plane', 'kube_node']}
    print(json.dumps(hosts, sort_keys=True, indent=2))

SearchEC2Tags()
