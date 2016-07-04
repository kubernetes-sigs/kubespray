![Kubespray Logo](http://s9.postimg.org/md5dyjl67/kubespray_logoandkubespray_small.png)

##Deploy a production ready kubernetes cluster

If you have questions, you can [invite yourself](https://slack.kubespray.io/) to **chat** with us on Slack! [![SlackStatus](https://slack.kubespray.io/badge.svg)](https://kubespray.slack.com)

- Can be deployed on **AWS, GCE, OpenStack or Baremetal**
- **High available** cluster
- **Composable** (Choice of the network plugin for instance)
- Support most popular **Linux distributions**
- **Continuous integration tests**


To deploy the cluster you can use :

[**kargo-cli**](https://github.com/kubespray/kargo-cli) <br>
**Ansible** usual commands <br>
**vagrant** by simply running `vagrant up` (for tests purposes) <br>


*  [Requirements](#requirements)
*  [Getting started](docs/getting-started.md)
*  [Vagrant install](docs/vagrant.md)
*  [CoreOS bootstrap](docs/coreos.md)
*  [Ansible variables](docs/ansible.md)
*  [Cloud providers](docs/cloud.md)
*  [Openstack](docs/openstack.md)
*  [Network plugins](#network-plugins)

Supported Linux distributions
===============

* **CoreOS**
* **Debian** Wheezy, Jessie
* **Ubuntu** 14.10, 15.04, 15.10, 16.04
* **Fedora** 23
* **CentOS/RHEL** 7

Versions
--------------

[kubernetes](https://github.com/kubernetes/kubernetes/releases) v1.3.0 <br>
[etcd](https://github.com/coreos/etcd/releases) v3.0.1 <br>
[calicoctl](https://github.com/projectcalico/calico-docker/releases) v0.20.0 <br>
[flanneld](https://github.com/coreos/flannel/releases) v0.5.5 <br>
[weave](http://weave.works/) v1.5.0 <br>
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


[![Build Status](https://travis-ci.org/kubespray/kargo.svg)](https://travis-ci.org/kubespray/kargo) </br>
CI tests sponsored by Google (GCE), and [teuto.net](https://teuto.net/) for OpenStack.

