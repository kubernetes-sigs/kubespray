$network_pluign = 'calico'
$os = 'ubuntu2004'
$kube_master_instances = 1
$vm_cpus = 1

# Map guest ports to a port on the host
$forwarded_ports = {6443 => 6443, 80 => 10080}
