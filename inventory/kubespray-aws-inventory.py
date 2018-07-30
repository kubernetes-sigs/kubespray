#!/usr/bin/env python

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
      print json.dumps(data, indent=2)

  def parse_args(self):

    ## Check if CLUSTER_NAME is set, ignore it otherwise
    if "CLUSTER_NAME" in os.environ:
      self.cluster_name = os.environ['CLUSTER_NAME']
    else:
      self.cluster_name = False

    ## Support --list and --host flags. We largely ignore the host one.
    parser = argparse.ArgumentParser()
    parser.add_argument('--list', action='store_true', default=False, help='List instances')
    parser.add_argument('--host', action='store_true', help='Get all the variables about a specific instance')
    self.args = parser.parse_args()

  def search_tags(self):
    hosts = {}
    hosts['_meta'] = { 'hostvars': {} }

    ## Search ec2 three times to find nodes of each group type. Relies on kubespray-role key/value.
    for group in ["kube-master", "kube-node", "etcd"]:
      hosts[group] = []
      tag_key = "service_type"
      tag_value = [group]
      region = os.environ["REGION"]
      vpc_id = os.environ["VPC_ID"]

      ec2 = boto3.resource('ec2', region)

      ## Default filters
      running_filter = {'Name': 'instance-state-name', 'Values': ['running']}
      role_filter = {'Name': 'tag:'+tag_key, 'Values': tag_value}
      vpc_filter = {'Name': 'vpc-id', 'Values': [vpc_id]}
      filter_list = [running_filter, role_filter, vpc_filter]

      ## Filter on the CLUSTER_NAME envvar, if it's in use
      if self.cluster_name:
        filter_list.append({'Name': 'tag:KubernetesCluster', 'Values': [self.cluster_name]})

      ## Lookup instances
      instances = ec2.instances.filter(Filters=filter_list)

      for instance in instances:
        for tags in instance.tags:
          if tags["Key"] == 'Name':
            hosts[group].append(tags["Value"])
            hosts['_meta']['hostvars'][tags["Value"]] = {
               'ansible_ssh_host': instance.private_ip_address
            }

      hosts[group] = sorted(hosts[group])

    if not hosts['etcd']:
      hosts['etcd'] = {'children':['kube-master']}

    hosts['k8s-cluster'] = {'children':['kube-master', 'kube-node']}
    print json.dumps(hosts, sort_keys=True, indent=2)

SearchEC2Tags()
