# Uprade MachShip Kubernetes Clusters


![MachShip](https://machship.com/wp-content/uploads/2021/05/machship-logo@2x.png)

![Kubernetes Logo](https://raw.githubusercontent.com/kubernetes-sigs/kubespray/master/docs/img/kubernetes-logo.png)

## Upgrade instruction
#### 1. Login to the upgrade runner host
Upgrading the cluster nodes requires direct SSH access to the Kubernetes nodes, therefore the process needs to run from a VM that is on the same network


```bash
ssh <your_user_name>@10.0.1.47
```

#### 2. Create a new Python environment
Create an isolated Python virtual environment for Kubespray to run
```bash
python3.10 -m venv ./kubespray-venv
cd kubespray-venv
```

#### 3. Clone the kubespray repository
Ask your manager for the access to the kubespray-fork repository
```bash
git clone https://github.com/machship/kubespray-fork.git kubespray
cd kubespray
```

#### 4. Installpython dependencies
```bash
pip install wheel
pip install -r requirements.txt
 ```

#### 5. Update the inventory files for the cluster to be upgraded
```bash
cd inventory/<cluster-name>
```

##### Update the hosts.yaml twith your username and id_rsa key
If you need to generate an ssh key on this host run the following command(do not use a passphrase)
```bash
ssh-keygen -t rsa
```

Example hosts.yaml to update
```
all:
  hosts:
    mel-dev-node1:
      ansible_host: 10.0.12.50
      ip: 10.0.12.50
      access_ip: 10.0.12.50
      ansible_user: <your_user_name>
      ansible_ssh_private_key_file: '~/.ssh/<your_rsa_key>'
    mel-dev-node2:
      ansible_host: 10.0.12.51
      ip: 10.0.12.51
      access_ip: 10.0.12.51
      ansible_user: <your_user_name>
      ansible_ssh_private_key_file: '~/.ssh/<your_rsa_key>'
    mel-dev-node3:
      ansible_host: 10.0.12.52
      ip: 10.0.12.52
      access_ip: 10.0.12.52
      ansible_user: <your_user_name>
      ansible_ssh_private_key_file: '~/.ssh/<your_rsa_key>'
  children:
    kube_control_plane:
      hosts:
        mel-dev-node1:
        mel-dev-node2:
        mel-dev-node3:
    kube_node:
      hosts:
        mel-dev-node1:
        mel-dev-node2:
        mel-dev-node3:
    etcd:
      hosts:
        mel-dev-node1:
        mel-dev-node2:
        mel-dev-node3:
    k8s_cluster:
      children:
        kube_control_plane:
        kube_node:
```

#### 6. Update the cluster version in the k8s_cluster.yaml file
Look for the kube_version: v1.xx.x and update as necessary
```bash
cd cd group_vars/k8s_cluster
vi k8s_cluster.yaml file
```

#### 7. Run the update from the root directory of teh repository
Use tghe --check flag to run the command in a dry run mode to test out the upgrade first
```bash
cd ../../../..
ansible-playbook -i inventory/<cluster-name>/hosts.yaml --diff -b -K upgrade-cluster.yml --check
```
You can also use the --limit flag to run the upgrade for a particular node, e.g.:
```bash
ansible-playbook -i inventory/<cluster-name>/hosts.yaml --diff -b -K upgrade-cluster.yml --limit <node-1>,<node-2>
```
