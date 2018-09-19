Kubelet standalone
==================

Kubelet may be installed headless, which is without the remaining kubernetes
cluster components. In that "dummy" mode, kubelet only manages static pods
locally and cannot schedule a pod onto other nodes.

Example installation
--------------------

Given a Fedora 28 node already prepared and having a static inventory file for
it, like:
```
$ cat ../hosts
node ansible_host=<IP for ssh access> ansible_user=fedora
[k8s-cluster]
node
```

The following steps may be done to install headless kubelet with CRI-O and runc
runtime. No networking plugins will be used, so pods only may be started in the
host networking mode. Execute these example commands from the clonned kubespray
repo directory:

* Optional step to configure custom repos
  (the required packages may be found in the stock updates repository as well):
```
$ cat > repos.yml << EOF
- hosts: node
  become: yes
  gather_facts: yes
  tasks:
    - yum_repository:
        name: paas7-openshift-origin311-candidate
        description: 'OpenShift Origin Repo'
        baseurl: https://cbs.centos.org/repos/paas7-openshift-origin311-candidate/x86_64/os/
        enabled: yes
        gpgcheck: no
    - yum_repository:
        name: virt7-container-common-candidate
        description: 'virt7-container-common-candidate'
        baseurl: https://cbs.centos.org/repos/virt7-container-common-candidate/x86_64/os/
        enabled: yes
        gpgcheck: no
EOF

$ ansible-playbook --flush-cache -i ../hosts repos.yml
```

* Deploy crio:
```
cat > crio.yml << EOF
- hosts: node
  become: yes
  gather_facts: yes
  vars:
    container_manager: crio
    is_atomic: false
    preinstall_selinux_state: enforcing
    # only defines insecure_registries for crio.conf
    kube_service_addresses: '{{ ansible_default_ipv4.address }}'
  roles:
    - roles/cri-o
EOF
ansible-playbook --flush-cache -i ../hosts crio.yml
```

* Deploy kubelet standalone (headless):
```
$ cat > kubelet-standalone.yml << EOF
- hosts: node
  become: yes
  gather_facts: yes
  vars:
    kube_version: v1.10.1           # see as it comes from installed rpm
    kubelet_headless: true
    kube_network_plugin: noop       # WIP (no network for pods yet!)
    kube_feature_gates:
      - "MountPropagation=true"     # mandatory for shared container mounts
      - "CRIContainerLogRotation=true" # let's see how/if it works
      - "DebugContainers=true"      # debug purposes
      - "MountContainers=true"      # debug purposes
    # https://github.com/kubernetes-sigs/cri-o/issues/842#issuecomment-327428272
    kubelet_cgroup_driver: cgroupfs # must match cri-o's cgroup_manager

    # debug-level (0-4) or trace-level (5-10)
    # informational is 1, verbose is 2 (defaults)
    kube_log_level: 4               # or 6 for displaying requested resources

    # default is 110, may be too much for the hosts-bound static pods
    kubelet_max_pods: 60
    kubelet_fail_swap_on: false     # not sure if we want it ON as default says
    is_kube_master: false           # a hack to ignore k8s-master specific things
    kube_cpu_reserved: 50m          # defaults to 100M for nodes, 200M for masters
    kube_memory_reserved: 128M      # defaults to 256M for nodes, 512M for masters
    pod_infra_image_repo: k8s.gcr.io/pause
    pod_infra_image_tag: 3.1

    dns_mode: manual
    manual_dns_server: 8.8.8.8      # pick the better one perhaps
    dns_domain: localdomain
    bin_dir: /usr/bin
    container_manager: crio
    preinstall_selinux_state: enforcing
  pre_tasks:
    - package: name=kubernetes-node state=present
  roles:
    - role: roles/kubespray-defaults
    - role: roles/kubernetes/preinstall
      tags: kubelet
    - role: roles/kubernetes/node
      tags: kubelet
EOF

$ ansible-playbook --flush-cache \
  --skip-tags=hyperkube,asserts,etchosts \
  -i ../hosts kubelet-standalone.yml
```

* Once deployed, perform some basic verifications, at the target node:
```
$ curl -skfL \
  https://raw.githubusercontent.com/kelseyhightower/standalone-kubelet-tutorial/master/pods/app-v0.1.0.yaml |\
  sudo tee /etc/kubernetes/manifests/app.yaml
$ curl http://127.0.0.1
version: 0.1.0
hostname: localhost.localdomain
key: 1537370096
$ crictl pods
$ crictl ps
$ crictl stats
$ crictl info # note: the networking is not ready yet for this guide :-(
```
Note, there is no kubectl CLI available for the standalone kubelet.

* Reset the deployment to try it from the scratch:
```
$ ansible-playbook -b --flush-cache -i ../hosts --skip-tags=iptables reset.yml
```
