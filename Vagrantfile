# -*- mode: ruby -*-
# vi: set ft=ruby :

pool = ENV["VAGRANT_POOL"] || "10.250.0.0/16"

ENV["VAGRANT_DEFAULT_PROVIDER"] = "libvirt"
prefix = pool.gsub(/\.\d+\.\d+\/16$/, "")

$num_instances = 7
$vm_memory = 2048
$vm_cpus = 2

$user = ENV["USER"]
$public_subnet = prefix.to_s + ".0"
$private_subnet = prefix.to_s + ".1"
$mgmt_cidr = prefix.to_s + ".2.0/24"

$instance_name_prefix = "#{$user}-k8s"

# Boxes with libvirt provider support:
#$box = "yk0/ubuntu-xenial" #900M
#$box = "centos/7"
#$box = "nrclark/xenial64-minimal-libvirt"
$box = "peru/ubuntu-16.04-server-amd64"

# Create SSH keys for future lab
system 'bash vagrant-scripts/ssh-keygen.sh'

# Create nodes list for future kargo deployment
nodes=""
(2..$num_instances).each do |i|
  ip = "#{$private_subnet}.#{i+10}"
  nodes = "#{nodes}#{ip}\n"
end
File.open("nodes", 'w') { |file| file.write(nodes) }

# Create the lab
Vagrant.configure("2") do |config|
  (1..$num_instances).each do |i|
    # First node would be master node
    if i == 1
      master = true
    else
      master = false
    end

    config.ssh.insert_key = false
    vm_name = "%s-%02d" % [$instance_name_prefix, i]

    config.vm.define vm_name do |test_vm|
      test_vm.vm.box = $box
      test_vm.vm.hostname = vm_name

      # Libvirt provider settings
      test_vm.vm.provider :libvirt do |domain|
        domain.uri = "qemu+unix:///system"
        domain.memory = $vm_memory
        domain.cpus = $vm_cpus
        domain.driver = "kvm"
        domain.host = "localhost"
        domain.connect_via_ssh = false
        domain.username = $user
        domain.storage_pool_name = "default"
        domain.nic_model_type = "e1000"
        domain.management_network_name = "#{$instance_name_prefix}-mgmt-net"
        domain.management_network_address = $mgmt_cidr
        domain.nested = true
        domain.cpu_mode = "host-passthrough"
        domain.volume_cache = "unsafe"
        domain.disk_bus = "virtio"
        # DISABLED: switched to new box which has 100G / partition
        #domain.storage :file, :type => 'qcow2', :bus => 'virtio', :size => '20G', :device => 'vdb'
      end

      # Networks and interfaces
      ip = "#{$private_subnet}.#{i+10}"
      pub_ip = "#{$public_subnet}.#{i+10}"
      # "public" network with nat forwarding
      test_vm.vm.network :private_network,
        :ip => pub_ip,
        :model_type => "e1000",
        :libvirt__network_name => "#{$instance_name_prefix}-public",
        :libvirt__dhcp_enabled => false,
        :libvirt__forward_mode => "nat"
      # "private" isolated network
      test_vm.vm.network :private_network,
        :ip => ip,
        :model_type => "e1000",
        :libvirt__network_name => "#{$instance_name_prefix}-private",
        :libvirt__dhcp_enabled => false,
        :libvirt__forward_mode => "none"

      # Provisioning
      config.vm.provision "file", source: "ssh", destination: "~/ssh"
      if master
        config.vm.provision "deploy-k8s", type: "file", source: "deploy-k8s.kargo.sh", destination: "~/deploy-k8s.kargo.sh"
        config.vm.provision "deploy-ccp", type: "file", source: "deploy-ccp.sh", destination: "~/deploy-ccp.sh"
        config.vm.provision "custom.yaml", type: "file", source: "custom.yaml", destination: "~/custom.yaml"
        config.vm.provision "playbooks", type: "file", source: "playbooks", destination: "~/playbooks"
        config.vm.provision "nodes", type: "file", source: "nodes", destination: "~/nodes"
        config.vm.provision "ccp", type: "file", source: "ccp", destination: "~/ccp"
        config.vm.provision "bootstrap", type: "shell", path: "vagrant-scripts/bootstrap-master.sh"
      else
        config.vm.provision "bootstrap", type: "shell", path: "vagrant-scripts/bootstrap-node.sh"
      end

    end
  end
end
