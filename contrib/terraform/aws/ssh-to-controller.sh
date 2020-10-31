#!/bin/bash

#
# I am frequently connecting to the servers in the cluster and I tweak settings to
# improve security or try to understand the innards of kubernetes. Because of this,
# I wanted a script to hide the complexities of the SSH command. 
#

#
# This script connects to the first controller node in the inventory file.
#
# CONFIGURATION IS NEEDED.
#
# * Set PKI_PRIVATE_PEM to the location of your PEM file used when creating the cluster.

# * Set KUBESPRAY_INSTALL_DIR to the root directory of the KubeSpray project. This variable
#   is used so that $KUBESPRAY_INSTALL_DIR/contrib/terraform/aws can be put into your path 
#   allowing this script to be run from any directory.
#

if [ -z $PKI_PRIVATE_PEM ]; then
    echo "Missing Environment Variable: PKI_PRIVATE_PEM"
    echo "  This variable should point to the PEM file for the BASTION server."
fi

if [ -z $KUBESPRAY_INSTALL_DIR ]; then
    echo "Missing Environment Variable: KUBESPRAY_INSTALL_DIR"
    echo "  This variable should point the root of the Kubespray project; where the LICENSE file is."
fi

INVENTORY="$KUBESPRAY_INSTALL_DIR/inventory/hosts"
CONF="$KUBESPRAY_INSTALL_DIR/ssh-bastion.conf"

if [ ! -f $INVENTORY ]; then
    echo "Missing file: $INVENTORY"
    echo "  This file should be created by the Terraform apply command."
fi

if [ ! -f $CONF ]; then
    echo "Missing file: $CONF"
    echo "  This file should be created by the Terraform apply command."
fi

ssh-add $PKI_PRIVATE_PEM

HOST_NAME=$(cat $INVENTORY | grep "\[kube-master\]" -A 1 | tail -n 1)
IP=$(cat $INVENTORY | grep $HOST_NAME | grep ansible_host | cut -d'=' -f2)
ssh -F $CONF centos@$IP
