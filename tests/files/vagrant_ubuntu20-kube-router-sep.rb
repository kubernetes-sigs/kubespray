$num_instances = 2
$vm_memory ||= 2048
$os = "ubuntu2004"

$kube_master_instances = 1
$etcd_instances = 1

# For CI we are not worried about data persistence across reboot
$libvirt_volume_cache = "unsafe"

# Checking for box update can trigger API rate limiting
# https://www.vagrantup.com/docs/vagrant-cloud/request-limits.html
$box_check_update = false

$network_plugin = "kube-router"
