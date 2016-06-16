# -*- mode: ruby -*-
# vi: set ft=ruby :

ENV["VAGRANT_DEFAULT_PROVIDER"] = "libvirt"
pool = ENV["VAGRANT_POOL"] || "10.210.0.0/16"
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
$box = "nrclark/xenial64-minimal-libvirt"

nodes=""
(1..$num_instances).each do |i|
  ip = "#{$private_subnet}.#{i+10}"
  nodes = "#{nodes}#{ip}\n"
end
File.open("nodes", 'w') { |file| file.write(nodes) }

Vagrant.configure("2") do |config|
  (1..$num_instances).each do |i|
    # First node would be master node
    if i == 1
      bootstrap_script = "bootstrap-master.sh"
      master = true
    else
      bootstrap_script = "bootstrap-node.sh"
      master = false
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
        domain.nested = true
        domain.cpu_mode = "host-passthrough"
        domain.volume_cache = "unsafe"
        domain.disk_bus = "virtio"
      end

      ip = "#{$private_subnet}.#{i+10}"
      test_vm.vm.network :private_network, :ip => "#{ip}"

      # Provisioning
      if master
        config.vm.provision "file", source: "deploy-k8s.kargo.sh", destination: "~/deploy-k8s.kargo.sh"
        config.vm.provision "file", source: "custom.yaml", destination: "~/custom.yaml"
        config.vm.provision "file", source: "nodes", destination: "~/nodes"
      end
      config.vm.provision "file", source: "ssh", destination: "~/ssh"
      config.vm.provision :shell, :path => bootstrap_script

    end
  end
end
