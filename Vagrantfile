# -*- mode: ruby -*-
# # vi: set ft=ruby :

# For help on using kubespray with vagrant, check out docs/developers/vagrant.md

require 'fileutils'
require 'ipaddr'
require 'socket'

Vagrant.require_version ">= 2.0.0"

CONFIG = File.join(File.dirname(__FILE__), ENV['KUBESPRAY_VAGRANT_CONFIG'] || 'vagrant/config.rb')

FLATCAR_URL_TEMPLATE = "https://%s.release.flatcar-linux.net/amd64-usr/current/flatcar_production_vagrant.json"

# Uniq disk UUID for libvirt
DISK_UUID = Time.now.utc.to_i

SUPPORTED_OS = {
  "flatcar-stable"      => {box: "flatcar-stable",             user: "core", box_url: FLATCAR_URL_TEMPLATE % ["stable"]},
  "flatcar-beta"        => {box: "flatcar-beta",               user: "core", box_url: FLATCAR_URL_TEMPLATE % ["beta"]},
  "flatcar-alpha"       => {box: "flatcar-alpha",              user: "core", box_url: FLATCAR_URL_TEMPLATE % ["alpha"]},
  "flatcar-edge"        => {box: "flatcar-edge",               user: "core", box_url: FLATCAR_URL_TEMPLATE % ["edge"]},
  "ubuntu2004"          => {box: "generic/ubuntu2004",         user: "vagrant"},
  "ubuntu2204"          => {box: "generic/ubuntu2204",         user: "vagrant"},
  "ubuntu2404"          => {box: "bento/ubuntu-24.04",         user: "vagrant"},
  "centos8"             => {box: "centos/8",                   user: "vagrant"},
  "centos8-bento"       => {box: "bento/centos-8",             user: "vagrant"},
  "almalinux8"          => {box: "almalinux/8",                user: "vagrant"},
  "almalinux8-bento"    => {box: "bento/almalinux-8",          user: "vagrant"},
  "almalinux9"          => {box: "almalinux/9",                user: "vagrant"},
  "rockylinux8"         => {box: "rockylinux/8",               user: "vagrant"},
  "rockylinux9"         => {box: "rockylinux/9",               user: "vagrant"},
  "fedora39"            => {box: "fedora/39-cloud-base",       user: "vagrant"},
  "fedora40"            => {box: "fedora/40-cloud-base",       user: "vagrant"},
  "fedora39-arm64"      => {box: "bento/fedora-39-arm64",      user: "vagrant"},
  "fedora40-arm64"      => {box: "bento/fedora-40",            user: "vagrant"},
  "fedora41"            => {box: "fedora/41-cloud-base",       user: "vagrant"},
  "fedora42"            => {box: "fedora/42-cloud-base",       user: "vagrant"},
  "fedora41-bento"      => {box: "bento/fedora-41",            user: "vagrant"},
  "opensuse"            => {box: "opensuse/Leap-15.6.x86_64",  user: "vagrant"},
  "opensuse-tumbleweed" => {box: "opensuse/Tumbleweed.x86_64", user: "vagrant"},
  "oraclelinux"         => {box: "generic/oracle7",            user: "vagrant"},
  "oraclelinux8"        => {box: "generic/oracle8",            user: "vagrant"},
  "rhel8"               => {box: "generic/rhel8",              user: "vagrant"},
  "debian11"            => {box: "debian/bullseye64",          user: "vagrant"},
  "debian12"            => {box: "debian/bookworm64",          user: "vagrant"},
}

if File.exist?(CONFIG)
  require CONFIG
end

# Defaults for config options defined in CONFIG
$num_instances ||= 3
$instance_name_prefix ||= "k8s"
$vm_gui ||= false
$vm_memory ||= 2048
$vm_cpus ||= 2
$shared_folders ||= {}
$forwarded_ports ||= {}
$subnet ||= "172.18.8"
$subnet_ipv6 ||= "fd3c:b398:0698:0756"
$os ||= "ubuntu2004"
$network_plugin ||= "flannel"
$inventories ||= []
# Setting multi_networking to true will install Multus: https://github.com/k8snetworkplumbingwg/multus-cni
$multi_networking ||= "False"
$download_run_once ||= "True"
$download_force_cache ||= "False"
# Set $etcd_count > 0 to instead provision dedicated etcd VMs (external etcd);
# in that case the 'etcd' group uses those nodes instead of the control plane.
$etcd_count          ||= 0
$control_plane_count ||= 1
$worker_count        ||= 2

# Hostname prefixes per role.
$etcd_prefix          ||= "#{$instance_name_prefix}-etcd"
$control_plane_prefix ||= "#{$instance_name_prefix}-api"
$worker_prefix        ||= "#{$instance_name_prefix}-worker"

# Build the full node list up front. Each entry is a hash describing one VM:
#   :name  -> zero-padded hostname (e.g. "etcd-01")
#   :role  -> :etcd | :control_plane | :worker
#   :ip4   -> last octet on $subnet (non-overlapping ranges per role)
# IP layout on $subnet: etcd .101+, control plane .121+, workers .141+.
$nodes = []
[[$etcd_prefix, $etcd_count, :etcd, 100],
 [$control_plane_prefix, $control_plane_count, :control_plane, 120],
 [$worker_prefix, $worker_count, :worker, 140]].each do |prefix, count, role, ip_base|
  (1..count).each do |n|
    $nodes << {
      :name => "%s-%02d" % [prefix, n],
      :role => role,
      :ip4  => ip_base + n,
    }
  end
end

# Total VM count (used for --forks and the "last node" provisioner trigger).
$num_instances = $nodes.length
# The following only works when using the libvirt provider
$kube_node_instances_with_disks ||= false
$kube_node_instances_with_disks_size ||= "20G"
$kube_node_instances_with_disks_number ||= 2
$override_disk_size ||= false
$disk_size ||= "20GB"
$local_path_provisioner_enabled ||= "False"
$local_path_provisioner_claim_root ||= "/opt/local-path-provisioner/"
$libvirt_nested ||= false
# Prefix vagrant-libvirt prepends to the machine name to form the libvirt domain
# name (shown by 'virsh list'). '' = no prefix, so domains match the VM names.
# Must be a string: if left unset (nil) the plugin silently falls back to
# "<project dir name>_", i.e. "kubespray_".
$libvirt_domain_prefix ||= ''
# Disable DNSSEC validation in the guests' systemd-resolved before Ansible runs.
# Needed when the upstream resolver can't validate DNSSEC (e.g. libvirt/WSL2 NAT).
$disable_dnssec = false if $disable_dnssec.nil?
# boolean or string (e.g. "-vvv")
$ansible_verbosity ||= false
$ansible_tags ||= ENV['VAGRANT_ANSIBLE_TAGS'] || ""

$vagrant_dir ||= File.join(File.dirname(__FILE__), ".vagrant")

$playbook ||= "cluster.yml"
$extra_vars ||= {}

host_vars = {}

def collect_networks(subnet, subnet_ipv6)
  Socket.getifaddrs.filter_map do |iface|
    next unless iface&.netmask&.ip_address && iface.addr

    is_ipv6 = iface.addr.ipv6?
    ip      = IPAddr.new(iface.addr.ip_address.split('%').first)
    ip_test = is_ipv6 ? IPAddr.new("#{subnet_ipv6}::0") : IPAddr.new("#{subnet}.0")

    prefix  = IPAddr.new(iface.netmask.ip_address).to_i.to_s(2).count('1')
    network = ip.mask(prefix)

    [IPAddr.new("#{network}/#{prefix}"), ip_test]
  end
end

def subnet_in_use?(network_ips)
  network_ips.any? { |net, test_ip| net.include?(test_ip) && test_ip != net }
end

network_ips = collect_networks($subnet, $subnet_ipv6)

if subnet_in_use?(network_ips)
  puts "Invalid subnet provided, subnet is already in use: #{$subnet}.0"
  puts "Subnets in use: #{network_ips.inspect}"
  exit 1
end

# throw error if os is not supported
if ! SUPPORTED_OS.key?($os)
  puts "Unsupported OS: #{$os}"
  puts "Supported OS are: #{SUPPORTED_OS.keys.join(', ')}"
  exit 1
end

$box = SUPPORTED_OS[$os][:box]

if Vagrant.has_plugin?("vagrant-proxyconf")
  $no_proxy = ENV['NO_PROXY'] || ENV['no_proxy'] || "127.0.0.1,localhost"
  $nodes.each do |n|
  $no_proxy += ",#{$subnet}.#{n[:ip4]}"
  end
end

Vagrant.configure("2") do |config|

  config.vm.box = $box
  if SUPPORTED_OS[$os].has_key? :box_url
    config.vm.box_url = SUPPORTED_OS[$os][:box_url]
  end
  config.ssh.username = SUPPORTED_OS[$os][:user]

  # plugin conflict
  if Vagrant.has_plugin?("vagrant-vbguest") then
    config.vbguest.auto_update = false
  end

  # always use Vagrants insecure key
  config.ssh.insert_key = false

  if ($override_disk_size)
    unless Vagrant.has_plugin?("vagrant-disksize")
      system "vagrant plugin install vagrant-disksize"
    end
    config.disksize.size = $disk_size
  end

$nodes.each_with_index do |node_spec, idx|
  i = idx + 1
  vm_name = node_spec[:name]
  config.vm.define vm_name do |node|


      node.vm.hostname = vm_name

      if Vagrant.has_plugin?("vagrant-proxyconf")
        node.proxy.http     = ENV['HTTP_PROXY'] || ENV['http_proxy'] || ""
        node.proxy.https    = ENV['HTTPS_PROXY'] || ENV['https_proxy'] ||  ""
        node.proxy.no_proxy = $no_proxy
      end

      ["vmware_fusion", "vmware_workstation"].each do |vmware|
        node.vm.provider vmware do |v|
          v.vmx['displayName'] = vm_name
          v.vmx['memsize'] = $vm_memory
          v.vmx['numvcpus'] = $vm_cpus
        end
      end

      node.vm.provider :virtualbox do |vb|
        vb.name = vm_name
        vb.memory = $vm_memory
        vb.cpus = $vm_cpus
        vb.gui = $vm_gui
        vb.linked_clone = true
        vb.customize ["modifyvm", :id, "--vram", "8"] # ubuntu defaults to 256 MB which is a waste of precious RAM
        vb.customize ["modifyvm", :id, "--audio", "none"]
      end

      node.vm.provider :libvirt do |lv|
        lv.nested = $libvirt_nested
        lv.cpu_mode = "host-model"
        lv.memory = $vm_memory
        lv.cpus = $vm_cpus
        lv.default_prefix = $libvirt_domain_prefix
        # Fix kernel panic on fedora 28
        if $os == "fedora"
          lv.cpu_mode = "host-passthrough"
        end
      end

      if $kube_node_instances_with_disks
        # Libvirt
        driverletters = ('a'..'z').to_a
        node.vm.provider :libvirt do |lv|
          # always make /dev/sd{a/b/c} so that CI can ensure that
          # virtualbox and libvirt will have the same devices to use for OSDs
          (1..$kube_node_instances_with_disks_number).each do |d|
            lv.storage :file, :device => "hd#{driverletters[d]}", :path => "disk-#{i}-#{d}-#{DISK_UUID}.disk", :size => $kube_node_instances_with_disks_size, :bus => "scsi"
          end
        end
        node.vm.provider :virtualbox do |vb|
          # always make /dev/sd{a/b/c} so that CI can ensure that
          # virtualbox and libvirt will have the same devices to use for OSDs
          (1..$kube_node_instances_with_disks_number).each do |d|
            vb.customize ['createhd', '--filename', "disk-#{i}-#{driverletters[d]}-#{DISK_UUID}.disk", '--size', $kube_node_instances_with_disks_size] # 10GB disk
            vb.customize ['storageattach', :id, '--storagectl', 'SATA Controller', '--port', d, '--device', 0, '--type', 'hdd', '--medium', "disk-#{i}-#{driverletters[d]}-#{DISK_UUID}.disk", '--nonrotational', 'on', '--mtype', 'normal']
          end
        end
      end

      if $expose_docker_tcp
        node.vm.network "forwarded_port", guest: 2375, host: ($expose_docker_tcp + i - 1), auto_correct: true
      end

      $forwarded_ports.each do |guest, host|
        node.vm.network "forwarded_port", guest: guest, host: host, auto_correct: true
      end

      if ["rhel8"].include? $os
        # Vagrant synced_folder rsync options cannot be used for RHEL boxes as Rsync package cannot
        # be installed until the host is registered with a valid Red Hat support subscription
        node.vm.synced_folder ".", "/vagrant", disabled: false
        $shared_folders.each do |src, dst|
          node.vm.synced_folder src, dst
        end
      else
        node.vm.synced_folder ".", "/vagrant", disabled: false, type: "rsync", rsync__args: ['--verbose', '--archive', '--delete', '-z'] , rsync__exclude: ['.git','venv']
        $shared_folders.each do |src, dst|
          node.vm.synced_folder src, dst, type: "rsync", rsync__args: ['--verbose', '--archive', '--delete', '-z']
        end
      end

      ip = "#{$subnet}.#{i+100}"
      ip6 = "#{$subnet_ipv6}::#{i+100}"
      node.vm.network :private_network,
        :ip => ip,
        :libvirt__guest_ipv6 => 'yes',
        :libvirt__ipv6_address => ip6,
        :libvirt__ipv6_prefix => "64",
        :libvirt__forward_mode => "none",
        :libvirt__dhcp_enabled => false

      # libvirt__ipv6_address does not work as intended, the address is obtained with the desired prefix, but auto-generated(like fd3c:b398:698:756:5054:ff:fe48:c61e/64)
      # add default route for detect ansible_default_ipv6
      # TODO: fix libvirt__ipv6 or use $subnet in shell
      config.vm.provision "shell", inline: "ip -6 r a fd3c:b398:698:756::/64 dev eth1;ip -6 r add default via fd3c:b398:0698:0756::1 dev eth1 || true"

      # Disable swap for each vm
      node.vm.provision "shell", inline: "swapoff -a"

      # ubuntu2004 and ubuntu2204 have IPv6 explicitly disabled. This undoes that.
      if ["ubuntu2004", "ubuntu2204"].include? $os
        node.vm.provision "shell", inline: "rm -f /etc/modprobe.d/local.conf"
        node.vm.provision "shell", inline: "sed -i '/net.ipv6.conf.all.disable_ipv6/d' /etc/sysctl.d/99-sysctl.conf /etc/sysctl.conf"
      end
      # Hack for fedora39/40 to get the IP address of the second interface
      if ["fedora39", "fedora40", "fedora39-arm64", "fedora40-arm64"].include? $os
        config.vm.provision "shell", inline: <<-SHELL
          nmcli conn modify 'Wired connection 2' ipv4.addresses $(cat /etc/sysconfig/network-scripts/ifcfg-eth1 | grep IPADDR | cut -d "=" -f2)/24
          nmcli conn modify 'Wired connection 2' ipv4.method manual
          service NetworkManager restart
        SHELL
      end

      # Disable DNSSEC in systemd-resolved before Ansible runs. The Ubuntu box
      # ships /etc/systemd/resolved.conf with DNSSEC=yes; on hosts whose upstream
      # resolver can't validate DNSSEC (libvirt/WSL2 NAT) this yields SERVFAIL and
      # the playbook's early apt step fails to resolve mirrors. Runs at boot, so
      # DNS works for the whole run.
      # Controlled by $disable_dnssec in vagrant/config.rb (default: true).
      if $disable_dnssec
        node.vm.provision "shell", inline: "if systemctl is-active --quiet systemd-resolved; then mkdir -p /etc/systemd/resolved.conf.d && printf '[Resolve]\\nDNSSEC=no\\n' > /etc/systemd/resolved.conf.d/00-disable-dnssec.conf && systemctl restart systemd-resolved; fi"
      end


      # Rockylinux boxes needs UEFI
      if ["rockylinux8", "rockylinux9"].include? $os
        config.vm.provider "libvirt" do |domain|
          domain.loader = "/usr/share/OVMF/x64/OVMF_CODE.fd"
        end
      end

      # Disable firewalld on oraclelinux/redhat vms
      if ["oraclelinux","oraclelinux8", "rhel8","rockylinux8"].include? $os
        node.vm.provision "shell", inline: "systemctl stop firewalld; systemctl disable firewalld"
      end

      host_vars[vm_name] = {
        "ip": ip,
        "flannel_interface": "eth1",
        "kube_network_plugin": $network_plugin,
        "kube_network_plugin_multus": $multi_networking,
        "download_run_once": $download_run_once,
        "download_localhost": "False",
        "download_cache_dir": ENV['HOME'] + "/kubespray_cache",
        # Make kubespray cache even when download_run_once is false
        "download_force_cache": $download_force_cache,
        # Keeping the cache on the nodes can improve provisioning speed while debugging kubespray
        "download_keep_remote_cache": "False",
        "docker_rpm_keepcache": "1",
        # These two settings will put kubectl and admin.config in $inventory/artifacts
        "kubeconfig_localhost": "True",
        "kubectl_localhost": "True",
        "local_path_provisioner_enabled": "#{$local_path_provisioner_enabled}",
        "local_path_provisioner_claim_root": "#{$local_path_provisioner_claim_root}",
        "ansible_ssh_user": SUPPORTED_OS[$os][:user],
        "ansible_ssh_private_key_file": File.join(Dir.home, ".vagrant.d", "insecure_private_key"),
        "unsafe_show_logs": "True"
      }

      # Only execute the Ansible provisioner once, when all the machines are up and ready.
      # And limit the action to gathering facts, the full playbook is going to be ran by testcases_run.sh
      if i == $num_instances
        node.vm.provision "ansible" do |ansible|
          ansible.playbook = $playbook
          ansible.compatibility_mode = "2.0"
          ansible.verbose = $ansible_verbosity
          ansible.become = true
          ansible.limit = "all,localhost"
          ansible.host_key_checking = false
          ansible.raw_arguments = ["--forks=#{$num_instances}",
                                   "--flush-cache",
                                   "-e ansible_become_pass=vagrant"] +
                                   $inventories.map {|inv| ["-i", inv]}.flatten
          ansible.host_vars = host_vars
          ansible.extra_vars = $extra_vars
          if $ansible_tags != ""
            ansible.tags = [$ansible_tags]
          end
          # Stacked topology: when no dedicated etcd VMs exist ($etcd_count == 0),
          # etcd runs on the control-plane nodes, so the 'etcd' group points at
          # them. With dedicated etcd VMs it points at those instead (external).
          etcd_nodes = $nodes.select { |n| n[:role] == :etcd }.map { |n| n[:name] }
          control_plane_nodes = $nodes.select { |n| n[:role] == :control_plane }.map { |n| n[:name] }
          etcd_nodes = control_plane_nodes if etcd_nodes.empty?
          ansible.groups = {
            "etcd" => etcd_nodes,
            "kube_control_plane" => control_plane_nodes,
            "kube_node" => $nodes.select { |n| n[:role] == :worker }.map { |n| n[:name] },
            "k8s_cluster:children" => ["kube_control_plane", "kube_node"],
          }
        end
      end

    end
  end
end
