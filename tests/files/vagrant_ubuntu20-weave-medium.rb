$num_instances = 16
$vm_memory ||= 2048
$os = "ubuntu2004"
$network_plugin = "weave"
$kube_master_instances = 1
$etcd_instances = 1
$playbook = "tests/cloud_playbooks/wait-for-ssh.yml"
