![Kubernetes Logo](https://s28.postimg.org/lf3q4ocpp/k8s.png)

Deploy a Production Ready Kubernetes Cluster
============================================

If you have questions, join us on the [kubernetes slack](https://kubernetes.slack.com), channel **\#kubespray**.

-   Can be deployed on **AWS, GCE, Azure, OpenStack, vSphere or Baremetal**
-   **High available** cluster
-   **Composable** (Choice of the network plugin for instance)
-   Support most popular **Linux distributions**
-   **Continuous integration tests**

Quick Start
-----------

To deploy the cluster you can use :

### Ansible

    # Copy ``inventory/sample`` as ``inventory/mycluster``
    cp -rfp inventory/sample inventory/mycluster

    # Update Ansible inventory file with inventory builder
    declare -a IPS=(10.10.1.3 10.10.1.4 10.10.1.5)
    CONFIG_FILE=inventory/mycluster/hosts.ini python3 contrib/inventory_builder/inventory.py ${IPS[@]}

    # Review and change parameters under ``inventory/mycluster/group_vars``
    cat inventory/mycluster/group_vars/all.yml
    cat inventory/mycluster/group_vars/k8s-cluster.yml

    # Deploy Kubespray with Ansible Playbook
    ansible-playbook -i inventory/mycluster/hosts.ini cluster.yml

### Vagrant

    # Simply running `vagrant up` (for tests purposes)
    vagrant up

Documents
---------

-   [Requirements](#requirements)
-   [Kubespray vs ...](docs/comparisons.md)
-   [Getting started](docs/getting-started.md)
-   [Ansible inventory and tags](docs/ansible.md)
-   [Integration with existing ansible repo](docs/integration.md)
-   [Deployment data variables](docs/vars.md)
-   [DNS stack](docs/dns-stack.md)
-   [HA mode](docs/ha-mode.md)
-   [Network plugins](#network-plugins)
-   [Vagrant install](docs/vagrant.md)
-   [CoreOS bootstrap](docs/coreos.md)
-   [Debian Jessie setup](docs/debian.md)
-   [openSUSE setup](docs/opensuse.md)
-   [Downloaded artifacts](docs/downloads.md)
-   [Cloud providers](docs/cloud.md)
-   [OpenStack](docs/openstack.md)
-   [AWS](docs/aws.md)
-   [Azure](docs/azure.md)
-   [vSphere](docs/vsphere.md)
-   [Large deployments](docs/large-deployments.md)
-   [Upgrades basics](docs/upgrades.md)
-   [Roadmap](docs/roadmap.md)

Supported Linux Distributions
-----------------------------

-   **Container Linux by CoreOS**
-   **Debian** Jessie, Stretch, Wheezy
-   **Ubuntu** 16.04
-   **CentOS/RHEL** 7
-   **Fedora/CentOS** Atomic
-   **openSUSE** Leap 42.3/Tumbleweed

Note: Upstart/SysV init based OS types are not supported.

Versions of supported components
--------------------------------

-   [kubernetes](https://github.com/kubernetes/kubernetes/releases) v1.9.5
-   [etcd](https://github.com/coreos/etcd/releases) v3.2.4
-   [flanneld](https://github.com/coreos/flannel/releases) v0.10.0
-   [calico](https://docs.projectcalico.org/v2.6/releases/) v2.6.8
-   [canal](https://github.com/projectcalico/canal) (given calico/flannel versions)
-   [cilium](https://github.com/cilium/cilium) v1.0.0-rc8
-   [contiv](https://github.com/contiv/install/releases) v1.1.7
-   [weave](http://weave.works/) v2.2.1
-   [docker](https://www.docker.com/) v17.03 (see note)
-   [rkt](https://coreos.com/rkt/docs/latest/) v1.21.0 (see Note 2)

Note: kubernetes doesn't support newer docker versions. Among other things kubelet currently breaks on docker's non-standard version numbering (it no longer uses semantic versioning). To ensure auto-updates don't break your cluster look into e.g. yum versionlock plugin or apt pin).

Note 2: rkt support as docker alternative is limited to control plane (etcd and
kubelet). Docker is still used for Kubernetes cluster workloads and network
plugins' related OS services. Also note, only one of the supported network
plugins can be deployed for a given single cluster.

Requirements
------------

-   **Ansible v2.4 (or newer) and python-netaddr is installed on the machine
    that will run Ansible commands**
-   **Jinja 2.9 (or newer) is required to run the Ansible Playbooks**
-   The target servers must have **access to the Internet** in order to pull docker images.
-   The target servers are configured to allow **IPv4 forwarding**.
-   **Your ssh key must be copied** to all the servers part of your inventory.
-   The **firewalls are not managed**, you'll need to implement your own rules the way you used to.
    in order to avoid any issue during deployment you should disable your firewall.
-   If kubespray is ran from non-root user account, correct privilege escalation method
    should be configured in the target servers. Then the `ansible_become` flag
    or command parameters `--become or -b` should be specified.

Network Plugins
---------------

You can choose between 6 network plugins. (default: `calico`, except Vagrant uses `flannel`)

-   [flannel](docs/flannel.md): gre/vxlan (layer 2) networking.

-   [calico](docs/calico.md): bgp (layer 3) networking.

-   [canal](https://github.com/projectcalico/canal): a composition of calico and flannel plugins.

-   [cilium](http://docs.cilium.io/en/latest/):  layer 3/4 networking (as well as layer 7 to protect and secure application protocols), supports dynamic insertion of BPF bytecode into the Linux kernel to implement security services, networking and visibility logic.

-   [contiv](docs/contiv.md): supports vlan, vxlan, bgp and Cisco SDN networking. This plugin is able to
    apply firewall policies, segregate containers in multiple network and bridging pods onto physical networks.

-   [weave](docs/weave.md): Weave is a lightweight container overlay network that doesn't require an external K/V database cluster.
    (Please refer to `weave` [troubleshooting documentation](http://docs.weave.works/weave/latest_release/troubleshooting.html)).

The choice is defined with the variable `kube_network_plugin`. There is also an
option to leverage built-in cloud provider networking instead.
See also [Network checker](docs/netcheck.md).

Community docs and resources
----------------------------

-   [kubernetes.io/docs/getting-started-guides/kubespray/](https://kubernetes.io/docs/getting-started-guides/kubespray/)
-   [kubespray, monitoring and logging](https://github.com/gregbkr/kubernetes-kargo-logging-monitoring) by @gregbkr
-   [Deploy Kubernetes w/ Ansible & Terraform](https://rsmitty.github.io/Terraform-Ansible-Kubernetes/) by @rsmitty
-   [Deploy a Kubernetes Cluster with Kubespray (video)](https://www.youtube.com/watch?v=N9q51JgbWu8)

Tools and projects on top of Kubespray
--------------------------------------

-   [Digital Rebar Provision](https://github.com/digitalrebar/provision/blob/master/doc/integrations/ansible.rst)
-   [Fuel-ccp-installer](https://github.com/openstack/fuel-ccp-installer)
-   [Terraform Contrib](https://github.com/kubernetes-incubator/kubespray/tree/master/contrib/terraform)

CI Tests
--------

![Gitlab Logo](https://s27.postimg.org/wmtaig1wz/gitlabci.png)

[![Build graphs](https://gitlab.com/kubespray-ci/kubernetes-incubator__kubespray/badges/master/build.svg)](https://gitlab.com/kubespray-ci/kubernetes-incubator__kubespray/pipelines)

CI/end-to-end tests sponsored by Google (GCE)
See the [test matrix](docs/test_cases.md) for details.
