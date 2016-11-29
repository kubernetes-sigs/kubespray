![Kubespray Logo](http://s9.postimg.org/md5dyjl67/kubespray_logoandkubespray_small.png)

##Deploy a production ready kubernetes cluster

If you have questions, you can [invite yourself](https://slack.kubespray.io/) to **chat** with us on Slack! [![SlackStatus](https://slack.kubespray.io/badge.svg)](https://kubespray.slack.com)

- Can be deployed on **AWS, GCE, Azure, OpenStack or Baremetal**
- **High available** cluster
- **Composable** (Choice of the network plugin for instance)
- Support most popular **Linux distributions**
- **Continuous integration tests**


To deploy the cluster you can use :

[**kargo-cli**](https://github.com/kubespray/kargo-cli) (deprecated, a newer [go](https://github.com/Smana/kargo-cli/tree/kargogo) version soon)<br>
**Ansible** usual commands <br>
**vagrant** by simply running `vagrant up` (for tests purposes) <br>


*  [Requirements](#requirements)
*  [Getting started](docs/getting-started.md)
*  [Vagrant install](docs/vagrant.md)
*  [CoreOS bootstrap](docs/coreos.md)
*  [Ansible variables](docs/ansible.md)
*  [Cloud providers](docs/cloud.md)
*  [OpenStack](docs/openstack.md)
*  [AWS](docs/aws.md)
*  [Azure](docs/azure.md)
*  [Network plugins](#network-plugins)
*  [Roadmap](docs/roadmap.md)

Supported Linux distributions
===============

* **CoreOS**
* **Debian** Wheezy, Jessie
* **Ubuntu** 14.10, 15.04, 15.10, 16.04
* **Fedora** 23
* **CentOS/RHEL** 7

Versions
--------------

[kubernetes](https://github.com/kubernetes/kubernetes/releases) v1.4.6 <br>
[etcd](https://github.com/coreos/etcd/releases) v3.0.6 <br>
[flanneld](https://github.com/coreos/flannel/releases) v0.6.2 <br>
[calicoctl](https://github.com/projectcalico/calico-docker/releases) v0.22.0 <br>
[weave](http://weave.works/) v1.6.1 <br>
[docker](https://www.docker.com/) v1.10.3 <br>


Requirements
--------------

* The target servers must have **access to the Internet** in order to pull docker images.
* The **firewalls are not managed**, you'll need to implement your own rules the way you used to.
in order to avoid any issue during deployment you should disable your firewall
* **Copy your ssh keys** to all the servers part of your inventory.
* **Ansible v2.x and python-netaddr**


## Network plugins
You can choose between 3 network plugins. (default: `flannel` with vxlan backend)

* [**flannel**](docs/flannel.md): gre/vxlan (layer 2) networking.

* [**calico**](docs/calico.md): bgp (layer 3) networking.

* **weave**: Weave is a lightweight container overlay network that doesn't require an external K/V database cluster. <br>
(Please refer to `weave` [troubleshooting documentation](http://docs.weave.works/weave/latest_release/troubleshooting.html))

The choice is defined with the variable `kube_network_plugin`


## CI Tests

[![Build Status](https://travis-ci.org/kubespray/kargo.svg)](https://travis-ci.org/kubespray/kargo) </br>

### Google Compute Engine

              | Calico        | Flannel       | Weave         |
------------- | ------------- | ------------- | ------------- |
Ubuntu Xenial |[![Build Status](https://ci.kubespray.io/job/kargo-gce-xenial-calico/badge/icon)](https://ci.kubespray.io/job/kargo-gce-xenial-calico/)|[![Build Status](https://ci.kubespray.io/job/kargo-gce-xenial-flannel/badge/icon)](https://ci.kubespray.io/job/kargo-gce-xenial-flannel/)|[![Build Status](https://ci.kubespray.io/job/kargo-gce-xenial-weave/badge/icon)](https://ci.kubespray.io/job/kargo-gce-xenial-weave)|
CentOS 7      |[![Build Status](https://ci.kubespray.io/job/kargo-gce-centos7-calico/badge/icon)](https://ci.kubespray.io/job/kargo-gce-centos7-calico/)|[![Build Status](https://ci.kubespray.io/job/kargo-gce-centos7-flannel/badge/icon)](https://ci.kubespray.io/job/kargo-gce-centos7-flannel/)|[![Build Status](https://ci.kubespray.io/job/kargo-gce-centos7-weave/badge/icon)](https://ci.kubespray.io/job/kargo-gce-centos7-weave/)|
CoreOS (stable) |[![Build Status](https://ci.kubespray.io/job/kargo-gce-coreos-calico/badge/icon)](https://ci.kubespray.io/job/kargo-gce-coreos-calico/)|[![Build Status](https://ci.kubespray.io/job/kargo-gce-coreos-flannel/badge/icon)](https://ci.kubespray.io/job/kargo-gce-coreos-flannel/)|[![Build Status](https://ci.kubespray.io/job/kargo-gce-coreos-weave/badge/icon)](https://ci.kubespray.io/job/kargo-gce-coreos-weave/)|

CI tests sponsored by Google (GCE), and [teuto.net](https://teuto.net/) for OpenStack.
