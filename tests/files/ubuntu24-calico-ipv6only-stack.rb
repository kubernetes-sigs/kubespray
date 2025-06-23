$os = "ubuntu2404"

$vm_cpus = 2
$libvirt_volume_cache = "unsafe"

# Checking for box update can trigger API rate limiting
# https://www.vagrantup.com/docs/vagrant-cloud/request-limits.html
$box_check_update = false
$network_plugin = "calico"
