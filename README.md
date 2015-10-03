This playbook deploys a whole kubernetes cluster, configures network overlay and some addons.

# Download necessary binaries
Note: a variable 'local_release_dir' defines where the binaries will be downloaded.
Ensure you've enough disk space

# Kubernetes
Kubernetes services are configured with the nodePort type.
eg: each node opoens the same tcp port and forwards the traffic to the target pod wherever it is located.

master :
  - apiserver :
  Currently the apiserver listen on both secure and unsecure ports
  todo, secure everything. Calico especially
  - scheduler :
  - controller :
  - proxy
node :
  - kubelet :
  kubelet is configured to call calico whenever a pod is created/destroyed
  - proxy
  configures all the forwarding rules

# Overlay network
You can choose between 2 network overlays. Only one must be chosen.
flannel: gre/vxlan (layer 2) networking
calico: bgp (layer 3) networking.

# Loadbalancer
The machine where ansible is ran must be allowed to access to the master ip on port 8080 (kubernetes api).
Indeed it gathered the services definition in order to know which NodePort is configured.
