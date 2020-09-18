
# For CI we are not worries about data persistence across reboot
# $libvirt_volume_cache = "unsafe"

# Checking for box update can trigger API rate limiting
# https://www.vagrantup.com/docs/vagrant-cloud/request-limits.html
# $box_check_update = false
$vm_cpus = 2

$os = "ubuntu1604"
#$playbook = "tests/cloud_playbooks/wait-for-ssh.yml"


$kube_master_instances = 1
$etcd_instances = 1
$num_instances = 3