# -*- mode: ruby -*-
# vi: set ft=ruby :

ENV["VAGRANT_DEFAULT_PROVIDER"] = "libvirt"

$num_instances = 7
$vm_memory = 2048
$vm_cpus = 2

$user = "adidenko"
$public_subnet = "10.210.0"
$private_subnet = "10.210.1"
$mgmt_cidr = "10.210.2.0/24"

$instance_name_prefix = "#{$user}-k8s"
# Boxes with libvirt provider support:
#$box = "yk0/ubuntu-xenial" #900M
#$box = "centos/7"
$box = "nrclark/xenial64-minimal-libvirt"

Vagrant.configure("2") do |config|
  (1..$num_instances).each do |i|
    if i == 1
      bootstrap_script = "bootstrap-master.sh"
    else
      bootstrap_script = "bootstrap-node.sh"
    end
    config.ssh.insert_key = false
    vm_name = "%s-%02d" % [$instance_name_prefix, i]
    config.vm.define vm_name do |test_vm|
      test_vm.vm.box = $box
      test_vm.vm.hostname = vm_name
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
      end

      test_vm.vm.network :private_network, :ip => "#{$private_subnet}.#{i+10}"

      # Provisioning
      config.vm.provision "file", source: "ssh", destination: "~/ssh"
      config.vm.provision :shell, :path => bootstrap_script

    end
  end
end
