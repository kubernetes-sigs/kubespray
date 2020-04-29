# Getting started

## Building your own inventory

Ansible inventory can be stored in 3 formats: YAML, JSON, or INI-like. There is
an example inventory located
[here](https://github.com/kubernetes-sigs/kubespray/blob/master/inventory/sample/inventory.ini).

You can use an
[inventory generator](https://github.com/kubernetes-sigs/kubespray/blob/master/contrib/inventory_builder/inventory.py)
to create or modify an Ansible inventory. Currently, it is limited in
functionality and is only used for configuring a basic Kubespray cluster inventory, but it does
support creating inventory file for large clusters as well. It now supports
separated ETCD and Kubernetes master roles from node role if the size exceeds a
certain threshold. Run `python3 contrib/inventory_builder/inventory.py help` help for more information.

Example inventory generator usage:

```ShellSession
cp -r inventory/sample inventory/mycluster
declare -a IPS=(10.10.1.3 10.10.1.4 10.10.1.5)
CONFIG_FILE=inventory/mycluster/hosts.yml python3 contrib/inventory_builder/inventory.py ${IPS[@]}
```

Then use `inventory/mycluster/hosts.yml` as inventory file.

## Starting custom deployment

Once you have an inventory, you may want to customize deployment data vars
and start the deployment:

**IMPORTANT**: Edit my\_inventory/groups\_vars/\*.yaml to override data vars:

```ShellSession
ansible-playbook -i inventory/mycluster/hosts.yml cluster.yml -b -v \
  --private-key=~/.ssh/private_key
```

See more details in the [ansible guide](docs/ansible.md).

### Adding nodes

You may want to add worker, master or etcd nodes to your existing cluster. This can be done by re-running the `cluster.yml` playbook, or you can target the bare minimum needed to get kubelet installed on the worker and talking to your masters. This is especially helpful when doing something like autoscaling your clusters.

- Add the new worker node to your inventory in the appropriate group (or utilize a [dynamic inventory](https://docs.ansible.com/ansible/intro_dynamic_inventory.html)).
- Run the ansible-playbook command, substituting `cluster.yml` for `scale.yml`:

```ShellSession
ansible-playbook -i inventory/mycluster/hosts.yml scale.yml -b -v \
  --private-key=~/.ssh/private_key
```

### Remove nodes

You may want to remove **master**, **worker**, or **etcd** nodes from your
existing cluster. This can be done by re-running the `remove-node.yml`
playbook. First, all specified nodes will be drained, then stop some
kubernetes services and delete some certificates,
and finally execute the kubectl command to delete these nodes.
This can be combined with the add node function. This is generally helpful
when doing something like autoscaling your clusters. Of course, if a node
is not working, you can remove the node and install it again.

Use `--extra-vars "node=<nodename>,<nodename2>"` to select the node(s) you want to delete.

```ShellSession
ansible-playbook -i inventory/mycluster/hosts.yml remove-node.yml -b -v \
--private-key=~/.ssh/private_key \
--extra-vars "node=nodename,nodename2"
```

If a node is completely unreachable by ssh, add `--extra-vars reset_nodes=no`
to skip the node reset step. If one node is unavailable, but others you wish
to remove are able to connect via SSH, you could set reset_nodes=no as a host
var in inventory.

## Connecting to Kubernetes

By default, Kubespray configures kube-master hosts with insecure access to
kube-apiserver via port 8080. A kubeconfig file is not necessary in this case,
because kubectl will use <http://localhost:8080> to connect. The kubeconfig files
generated will point to localhost (on kube-masters) and kube-node hosts will
connect either to a localhost nginx proxy or to a loadbalancer if configured.
More details on this process are in the [HA guide](docs/ha-mode.md).

Kubespray permits connecting to the cluster remotely on any IP of any
kube-master host on port 6443 by default. However, this requires
authentication. One can get a kubeconfig from kube-master hosts
(see [below](#accessing-kubernetes-api)) or connect with a [username and password](vars.md#user-accounts).

For more information on kubeconfig and accessing a Kubernetes cluster, refer to
the Kubernetes [documentation](https://kubernetes.io/docs/tasks/access-application-cluster/configure-access-multiple-clusters/).

## Accessing Kubernetes Dashboard

Supported version is kubernetes-dashboard v2.0.x :

- Login options are : token/kubeconfig by default, basic can be enabled with `kube_basic_auth: true` inventory variable - not recommended because this requires ABAC api-server which is not tested by kubespray team
- Deployed by default in "kube-system" namespace, can be overriden with `dashboard_namespace: kubernetes-dashboard` in inventory,
- Only serves over https

Access is described in [dashboard docs](https://github.com/kubernetes/dashboard/blob/master/docs/user/accessing-dashboard/1.7.x-and-above.md). With kubespray's default deployment in kube-system namespace, instead of kuberntes-dashboard :

- Proxy URL is <http://localhost:8001/api/v1/namespaces/kube-system/services/https:kubernetes-dashboard:/proxy/#/login>
- kubectl commands must be run with "-n kube-system"

Accessing through Ingress is highly recommended. For proxy access, please note that proxy must listen to [localhost](https://github.com/kubernetes/dashboard/issues/692#issuecomment-220492484) (`proxy  --address="x.x.x.x"` will not work)

For token authentication, guide to create Service Account is provided in [dashboard sample user](https://github.com/kubernetes/dashboard/blob/master/docs/user/access-control/creating-sample-user.md) doc. Still take care of default namespace.

Access can also by achieved via ssh tunnel on a master :

```bash
# localhost:8081 will be sent to master-1's own localhost:8081
ssh -L8001:localhost:8001 user@master-1
sudo -i
kubectl proxy
```

## Accessing Kubernetes API

The main client of Kubernetes is `kubectl`. It is installed on each kube-master
host and can optionally be configured on your ansible host by setting
`kubectl_localhost: true` and `kubeconfig_localhost: true` in the configuration:

- If `kubectl_localhost` enabled, `kubectl` will download onto `/usr/local/bin/` and setup with bash completion. A helper script `inventory/mycluster/artifacts/kubectl.sh` also created for setup with below `admin.conf`.
- If `kubeconfig_localhost` enabled `admin.conf` will appear in the `inventory/mycluster/artifacts/` directory after deployment.
- The location where these files are downloaded to can be configured via the `artifacts_dir` variable.

You can see a list of nodes by running the following commands:

```ShellSession
cd inventory/mycluster/artifacts
./kubectl.sh get nodes
```

If desired, copy admin.conf to ~/.kube/config.
