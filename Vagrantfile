# -*- mode: ruby -*-
# # vi: set ft=ruby :

require 'fileutils'

Vagrant.require_version ">= 1.8.0"

CONFIG = File.join(File.dirname(__FILE__), "vagrant/config.rb")

# Defaults for config options defined in CONFIG
$num_instances = 3
$instance_name_prefix = "k8s"
$vm_gui = false
$vm_memory = 1536
$vm_cpus = 1
$shared_folders = {}
$forwarded_ports = {}
$subnet = "172.17.8"
$box = "bento/ubuntu-16.04"
# The first three nodes are etcd servers
$etcd_instances = $num_instances
# The first two nodes are masters
$kube_master_instances = $num_instances == 1 ? $num_instances : ($num_instances - 1)
# All nodes are kube nodes
$kube_node_instances = $num_instances
$local_release_dir = "/vagrant/temp"

host_vars = {}

if File.exist?(CONFIG)
  require CONFIG
end

# if $inventory is not set, try to use example
$inventory = File.join(File.dirname(__FILE__), "inventory") if ! $inventory

# if $inventory has a hosts file use it, otherwise copy over vars etc
# to where vagrant expects dynamic inventory to be.
if ! File.exist?(File.join(File.dirname($inventory), "hosts"))
  $vagrant_ansible = File.join(File.dirname(__FILE__), ".vagrant",
                       "provisioners", "ansible")
  FileUtils.mkdir_p($vagrant_ansible) if ! File.exist?($vagrant_ansible)
  if ! File.exist?(File.join($vagrant_ansible,"inventory"))
    FileUtils.ln_s($inventory, $vagrant_ansible)
  end
end

if Vagrant.has_plugin?("vagrant-proxyconf")
    $no_proxy = ENV['NO_PROXY'] || ENV['no_proxy'] || "127.0.0.1,localhost"
    (1..$num_instances).each do |i|
        $no_proxy += ",#{$subnet}.#{i+100}"
    end
end

Vagrant.configure("2") do |config|
  # always use Vagrants insecure key
  config.ssh.insert_key = false
  config.vm.box = $box

  # plugin conflict
  if Vagrant.has_plugin?("vagrant-vbguest") then
    config.vbguest.auto_update = false
  end

  (1..$num_instances).each do |i|
    config.vm.define vm_name = "%s-%02d" % [$instance_name_prefix, i] do |config|
      config.vm.hostname = vm_name

      if Vagrant.has_plugin?("vagrant-proxyconf")
        config.proxy.http     = ENV['HTTP_PROXY'] || ENV['http_proxy'] || ""
        config.proxy.https    = ENV['HTTPS_PROXY'] || ENV['https_proxy'] ||  ""
        config.proxy.no_proxy = $no_proxy
      end

      if $expose_docker_tcp
        config.vm.network "forwarded_port", guest: 2375, host: ($expose_docker_tcp + i - 1), auto_correct: true
      end

      $forwarded_ports.each do |guest, host|
        config.vm.network "forwarded_port", guest: guest, host: host, auto_correct: true
      end

      ["vmware_fusion", "vmware_workstation"].each do |vmware|
        config.vm.provider vmware do |v|
          v.vmx['memsize'] = $vm_memory
          v.vmx['numvcpus'] = $vm_cpus
        end
      end

      config.vm.provider :virtualbox do |vb|
        vb.gui = $vm_gui
        vb.memory = $vm_memory
        vb.cpus = $vm_cpus
      end

      ip = "#{$subnet}.#{i+100}"
      host_vars[vm_name] = {
        "ip": ip,
        "flannel_interface": ip,
        "flannel_backend_type": "host-gw",
        "local_release_dir" => $local_release_dir,
        "download_run_once": "False",
        # Override the default 'calico' with flannel.
        # inventory/group_vars/k8s-cluster.yml
        "kube_network_plugin": "flannel",
      }
      config.vm.network :private_network, ip: ip

      # Only execute once the Ansible provisioner,
      # when all the machines are up and ready.
      if i == $num_instances
        config.vm.provision "ansible" do |ansible|
          ansible.playbook = "cluster.yml"
          if File.exist?(File.join(File.dirname($inventory), "hosts"))
            ansible.inventory_path = $inventory
          end
          ansible.sudo = true
          ansible.limit = "all"
          ansible.host_key_checking = false
          ansible.raw_arguments = ["--forks=#{$num_instances}"]
          ansible.host_vars = host_vars
          #ansible.tags = ['download']
          ansible.groups = {
            "etcd" => ["#{$instance_name_prefix}-0[1:#{$etcd_instances}]"],
            "kube-master" => ["#{$instance_name_prefix}-0[1:#{$kube_master_instances}]"],
            "kube-node" => ["#{$instance_name_prefix}-0[1:#{$kube_node_instances}]"],
            "k8s-cluster:children" => ["kube-master", "kube-node"],
          }
        end
      end

    end
  end
end
