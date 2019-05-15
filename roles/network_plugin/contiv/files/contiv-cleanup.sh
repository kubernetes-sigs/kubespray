#!/bin/bash
set -e
echo "Starting cleanup"
ovs-vsctl list-br | grep contiv | xargs -I % ovs-vsctl del-br %
for p in $(ifconfig | grep vport | awk '{print $1}');
do
	ip link delete $p type veth
done
touch /tmp/cleanup.done
sleep 60
