# Deploy a Production Ready Kubernetes Cluster

![Kubernetes Logo](https://raw.githubusercontent.com/kubernetes-sigs/kubespray/master/docs/img/kubernetes-logo.png)

If you have questions, check the documentation at [kubespray.io](https://kubespray.io) and join us on the [kubernetes slack](https://kubernetes.slack.com), channel **\#kubespray**.
You can get your invite [here](http://slack.k8s.io/)

- Can be deployed on **[AWS](docs/cloud_providers/aws.md), GCE, [Azure](docs/cloud_providers/azure.md), [OpenStack](docs/cloud_controllers/openstack.md), [vSphere](docs/cloud_controllers/vsphere.md), [Equinix Metal](docs/cloud_providers/equinix-metal.md) (bare metal), Oracle Cloud Infrastructure (Experimental), or Baremetal**
- **Highly available** cluster
- **Composable** (Choice of the network plugin for instance)
- Supports most popular **Linux distributions**
- **Continuous integration tests**

---

## Quick Start

> **Note:** This is a simplified guide tailored to a specific setup. For full details, check the [official repository](https://github.com/kubernetes-sigs/kubespray).

### Prepare the Inventory

Before proceeding with the installation, make sure to update your inventory file (`inventory.ini`) with the IP addresses and SSH credentials of all your control plane and worker nodes.

### Cluster Installation

Provision a highly available Kubernetes cluster:

```bash
ansible-playbook -i inventory/ha-calico-kube-vip/inventory.ini \
  -u goat --become --ask-become-pass cluster.yml
```

If your `kube-vip` configuration needs to be updated, rerun the playbook with the relevant tag:

```bash
ansible-playbook -i inventory/ha-calico-kube-vip/inventory.ini \
  -u goat --become --ask-become-pass --tags kube-vip cluster.yml
```

---

### Validate the Cluster

1. **SSH into a control plane node:**

```bash
ssh goat@<CONTROL_PLANE_NODE_1_IP>
```

2. **Configure kubectl on your local environment:**

```bash
mkdir -p ~/.kube
sudo cp /root/.kube/config ~/.kube/config
sudo chown $(id -u):$(id -g) ~/.kube/config
```

3. **Verify the cluster is up:**

```bash
kubectl get nodes
kubectl get pods -A
```

4. **Check the Virtual IP (VIP):**

```bash
ping <VIP>
```

---

### Configure External Access

1. **Backup your current kubeconfig:**

```bash
cp ~/.kube/config ~/.kube/config-external
```

2. **Replace `127.0.0.1` with the VIP address:**

```bash
export VIP=192.168.200.147
sed -i "s|https://127.0.0.1:6443|https://$VIP:6443|" ~/.kube/config-external
```

3. **Test using the external kubeconfig:**

```bash
kubectl --kubeconfig ~/.kube/config-external get nodes
```

### Manual steps that soon will be automated:

1. **Kube-vip cloud provide installation**
```bash
kubectl create configmap -n kube-system kubevip --from-literal range-global=192.168.200.161-192.168.200.165
kubectl apply -f https://raw.githubusercontent.com/kube-vip/kube-vip-cloud-provider/main/manifest/kube-vip-cloud-controller.yaml
```

2. **Clabernetes installation**
TODO

3. **Installation of custom monitoring stack**
TODO

Congratulations! You can now share the external kubeconfig with authorised users.

---

## Clean Up (Uninstallation)

To remove the Kubernetes cluster:

```bash
ansible-playbook -i inventory/ha-calico-kube-vip/inventory.ini \
  -u goat --become --ask-become-pass reset.yml
```

---
