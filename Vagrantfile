# -*- mode: ruby -*-
# # vi: set ft=ruby :

# For help on using kubespray with vagrant, check out docs/vagrant.md

#
# Settings
#
OS = "debian" # Which operating system to use
OS_VERSION = "10" # Which operating system version to use
PLAYBOOK = "cluster.yml" # Which playbook to run

NODE_CPU_COUNT = 2 # How many cpus each node has
NODE_MEMORY_AMOUNT = 2048 # How much memory each node has
NODE_ROOTFS_SIZE = 50 # Default root partition size
NODE_EXTRA_DISK_COUNT = 2 # Attach to each node extra disks
NODE_EXTRA_DISK_SIZE = 50 # Size in GB of each extra disk

SUBNET = "192.168.100" # Allocate nodes from this subnet

NODE_MASTER_COUNT = 3 # How many masters to create
NODE_WORKER_COUNT = 2 # How many workers to create
NODE_ETCD_COUNT = 0 # How many etcd nodes to create, if 0 the nodes will be colocated with the masters

EXTRA_VARS = {
  "download_run_once" => true, # Increase provisioning speed
  "kube_network_plugin" => "calico"
}

FORWARD_PORTS = [
  # { guest: 2375, host: 2375, host_ip: "127.0.0.1", protocol: "tcp" }
]

SYNCED_FOLDERS = [
  # { from: "/tmp/cache", to: "/var/cache" }
]

#
# Kubespray data
#
COREOS_URL_TEMPLATE = "https://storage.googleapis.com/%s.release.core-os.net/amd64-usr/current/coreos_production_vagrant.json"
SUPPORTED_OS = {
  "coreos" => {
    "alpha" =>  { box: "coreos-alpha", user: "core", box_url: COREOS_URL_TEMPLATE % ["alpha"] },
    "beta" =>   { box: "coreos-beta", user: "core", box_url: COREOS_URL_TEMPLATE % ["beta"] },
    "stable" => { box: "coreos-stable", user: "core", box_url: COREOS_URL_TEMPLATE % ["stable"] }
  },
  "centos" => {
    "7" => { box: "centos/7" }
  },
  "debian" => {
    "9" =>  { box: "debian/stretch64" },
    "10" => { box: "debian/buster64" }
  },
  "fedora" => {
    "30" => { box: "fedora/30-cloud-base" },
    "31" => { box: "fedora/31-beta-cloud-base" }
  },
  "opensuse" => {
    "tumbleweed" => { box: "opensuse/openSUSE-Tumbleweed-Vagrant.x86_64" }
  },
  "oracle" => {
    "7" => { box: "generic/oracle7" }
  },
  "ubuntu" => {
    "16.04" => { box: "generic/ubuntu1604" },
    "18.04" => { box: "generic/ubuntu1804" }
  }
}

#
# Calculated data
#
host_vars = {}
COLOCATED_ETCD = NODE_ETCD_COUNT == 0
TOTAL_NODE_COUNT = NODE_MASTER_COUNT + NODE_WORKER_COUNT + NODE_ETCD_COUNT

#
# Functions
#
def node_role_from_index(index)
  # Return the node role for a given index
  # Example 3 masters, 2 worker, 3 etcd
  # 1,2,3 => master, 4,5 => worker, 6,7,8 => etcd
  if index <= NODE_MASTER_COUNT
    return "master"
  elsif index > NODE_MASTER_COUNT and index <= (NODE_MASTER_COUNT + NODE_WORKER_COUNT)
    return "worker"
  else
    return "etcd"
  end
end
def node_index_in_role(global_index)
  # Return the sub-index associated with that node
  case node_role_from_index(global_index)
  when "master"
    # Masters inherit the global index as-is
    return global_index
  when "worker"
    # Worker nodes' indexes are after the master ones
    return global_index - NODE_MASTER_COUNT
  when "etcd"
    # etcd nodes' indexes are after the masters and the workers
    return global_index - NODE_MASTER_COUNT - NODE_WORKER_COUNT
  end
end
def node_hostname_for_role(role, index)
  # Return the hostname of the node with the given role and index
  return "k8s-%s-%d" % [ role, index ]
end
def node_hostname(index)
  # Return the hostname of the node with a given index
  return node_hostname_for_role(node_role_from_index(index), node_index_in_role(index))
end
def get_ansible_groups()
  # Return the Ansible host-group mappings

  masterList = (1..NODE_MASTER_COUNT).map{|i| node_hostname_for_role("master", i) }
  workerList = (1..NODE_WORKER_COUNT).map{|i| node_hostname_for_role("worker", i) }

  if COLOCATED_ETCD
    # Every master is also an etcd node
    etcdList = masterList
  else
    # Generate a separate etcd node list
    etcdList = (1..NODE_ETCD_COUNT).map{|i| node_hostname_for_role("etcd", i) }
  end

  return {
    "kube-master" => masterList,
    "kube-node" => masterList | workerList,
    "etcd" => etcdList,
    "k8s-cluster:children" => [ "kube-master", "kube-node" ]
  }
end
def is_etcd_node(index)
  # Check if the node with the given index will host an etcd instance

  if node_role_from_index(index) == "etcd"
    # The node is an etcd node
    return true
  end

  if COLOCATED_ETCD and node_role_from_index(index) == "master"
    # The node is a master node in colocated configuration
    return true
  end

  return false
end

#
# Vagrant script
#
Vagrant.require_version ">= 2.0.0"
Vagrant.configure("2") do |config|

  # Set box name
  config.vm.box = SUPPORTED_OS[OS][OS_VERSION][:box]
  if SUPPORTED_OS[OS][OS_VERSION].has_key?("box_url")
    config.vm.box_url = SUPPORTED_OS[OS][OS_VERSION][:box_url]
  end
  # Set box user
  if SUPPORTED_OS[OS][OS_VERSION].has_key?("user")
    config.ssh.username = SUPPORTED_OS[OS][OS_VERSION][:user]
  end

  # Disable default synced folder
  config.vm.synced_folder ".", "/vagrant", disabled: true

  # Provider settings
  config.vm.provider :libvirt do |libvirt|
    libvirt.cpus = NODE_CPU_COUNT
    libvirt.memory = NODE_MEMORY_AMOUNT
    libvirt.machine_virtual_size = NODE_ROOTFS_SIZE
  end

  # Define the VMs
  (1..TOTAL_NODE_COUNT).each do |i|
    config.vm.define node_name = node_hostname(i) do |node|

      # Ensure that the hostname is correct
      node.vm.hostname = node_name

      # Extra disks
      node.vm.provider :libvirt do |libvirt|
        (1..NODE_EXTRA_DISK_COUNT).each() do |extra_disk_index|
          libvirt.storage :file,
            :path => "#{node_name}disk#{extra_disk_index}.qcow2",
            :size => "#{NODE_EXTRA_DISK_SIZE}G",
            :type => "qcow2"
        end
      end

      # Forward ports
      FORWARD_PORTS.each() do |forwarded_port|
        node.vm.network :forwarded_port,
          guest: forwarded_port[:guest],
          host: forwarded_port[:host] + i - 1,
          host_ip: forwarded_port[:host_ip] || "127.0.0.1",
          protocol: forwarded_port[:protocol] || "tcp"
        puts "Forwarding %d => %d on %s" % [ (forwarded_port[:host] + i - 1), forwarded_port[:guest], node_name ]
      end

      # Synced folders
      SYNCED_FOLDERS.each() do |synced_folder|
        if i == 1
          puts "Syncing folder %s => %s" % [ synced_folder[:from], synced_folder[:to] ]
        end
        node.vm.synced_folder synced_folder[:from], synced_folder[:to]
      end

      # Expose the node on a local ip
      nodeIp = "#{SUBNET}.#{10 + i}"
      node.vm.network :private_network, ip: nodeIp

      # Set ansible variables
      host_vars[node_name] = {
        "ip" => nodeIp
      }

      # Set etcd member name
      if is_etcd_node(i)
        host_vars[node_name].merge!({ "etcd_member_name" => node_name })
      end

      # Provision the nodes
      if i == TOTAL_NODE_COUNT
        node.vm.provision "ansible" do |ansible|
          # Set the playbook
          ansible.playbook = PLAYBOOK
          ansible.become = true
          ansible.limit = "all,localhost"
          ansible.raw_arguments = ["--flush-cache", "--forks=#{TOTAL_NODE_COUNT}"]
          ansible.groups = get_ansible_groups()
          ansible.extra_vars = EXTRA_VARS
          ansible.host_vars = host_vars
        end
      end

    end
  end

end
