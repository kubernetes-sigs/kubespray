'''
@author: Vinayaka V Ladwa
@email : vinayakladwa@gmail.com
@version : v1
'''
__author__ =""

## This script is used to generate the kubespray inventory file#
import logging
import sys
import itertools
import json
import traceback

logging.basicConfig(
    format='%(asctime)s:%(thread)d:%(levelname)s:%(message)s',
    level=logging.INFO, filename="GenerateInventoryFile.log"
)

def main():
    minion_node_details = []
    etcd_node_details = []
    master_node_details = []
    try:
        logging.info("Opening the terraform generated Inventory file for reading")
        with  open(sys.argv[1]+"/inventory_hosts.ini","r") as file_des:
            host_details = {}
            for i in file_des:
                input_line = i.rstrip('\n')
                env,component,instance_url = input_line.split(',')
                instance_details = instance_url.split('/')
                project = instance_details[6]
                instance_name = instance_details[-1]
                instance_fqdn = "%s.c.%s.internal" %(instance_name,project)
                if component == "minion":
                    minion_node_details.append(instance_name)
                    logging.info("Default/Minion Node is %s" %(instance_name))
                if component == "etcd":
                    etcd_node_details.append(instance_name)
                    logging.info("etcd name is: %s" %(instance_name))
                if component == "master":
                    master_node_details.append(instance_name)
                    logging.info("Master Node is %s" %(instance_name))
                host_details[instance_name] = instance_fqdn
    except Exception as e:
        print "Error while reading terraform generated inventory_hosts.ini file:%s" %(e)
        logging.error("Error while reading terraform generated inventory_hosts.ini file:%s" %(e))
        logging.error(traceback.format_exc())
        sys.exit()

    try:
        with open(sys.argv[1]+"/kubespray/inventory/cluster/inventory_hosts.ini", 'wb') as configfile:
            all_instance_details = list(itertools.chain(host_details))
            configfile.write("[all]\n")
            for i in  all_instance_details:
                configfile.write("%s ansible_host=%s  ansible_ssh_user=%s ansible_ssh_private_key_file=%s\n" % (i,host_details[i],sys.argv[2], sys.argv[1]+"/key"))
            configfile.write("\n[kube-master]\n")
            for master in master_node_details:
                configfile.write("%s\n"%(master))
            configfile.write("\n[etcd]\n")
            for etcd in etcd_node_details:
                configfile.write("%s\n"%(etcd))
            configfile.write("\n[kube-node]\n")
            for kube_nodes in minion_node_details:
                configfile.write("%s\n"%(kube_nodes))
            configfile.write("\n[k8s-cluster:children]\n")
            configfile.write("kube-master\n")
            configfile.write("kube-node\n")
            configfile.write("\n[all:vars]\n")
    except Exception as e:
        print "Error while generating kubespray inventory file:%s" %(e)
        logging.error("Error while generating kubespray inventory file:%s" %(e))
        logging.error(traceback.format_exc())
        sys.exit()

if __name__ == "__main__":
    main()