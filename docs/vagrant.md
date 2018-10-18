Vagrant Install
=================

Assuming you have Vagrant (2.0+) installed with virtualbox (it may work with vmware, but is untested) you should be able to launch a 3 node Kubernetes cluster by simply running `$ vagrant up`.

This will spin up 3 VMs and install kubernetes on them.  Once they are completed you can connect to any of them by running `$ vagrant ssh node-[1..3]`.

Customize Vagrant
=================

You can override the default settings in the `Vagrantfile` either by directly modifying the `Vagrantfile` or through an override file. In the same directory as the `Vagrantfile`, create a folder called `vagrant` and create `config.rb` file in it. You're able to override the variables defined in `Vagrantfile` by providing the value in the `vagrant/config.rb` file.


Use alternative OS for Vagrant
==============================

By default, Vagrant uses Ubuntu 16.04 box to provision a local cluster. You may use an alternative supported operating system for your local cluster.

Customize `$os` variable in `Vagrantfile` or as override, e.g.,:

    echo '$os = "coreos-stable"' >> vagrant/config.rb

The supported operating systems for vagrant are defined in the `SUPPORTED_OS` constant in the `Vagrantfile`.

How kubespray Vagrant and caching
===================
Kubespray can take quit a while to start on a laptop. To improve provisioning speed, the variable 'download_run_once' is set. This will make kubespray download all files and containers just once and then distribute them to nodes. The variable 'download_localhost' determines if the initial download is done on the local (ansible host) machine, or on the first master node in the kubernetes cluster. When download_localhost is set, ansible requires root rights to access docker for image downloading. For this reason, the Vagrantfile is configured to always ask for the root password on startup.

Additionally, all downloaded files will be cached locally in $local_release_dir, which defaults to /tmp/releases. On subsequent provisioning runs, this local cache will be used to provision the nodes, possibly improving provisining time. To give an estimate of the expected duration of a provisioning run: On a dual core i5-6300u laptop with an SSD, provisioning takes around 13 to 15 minutes, once the container images and other files are cached.

Example use of Vagrant
======================

The following is an example of setting up and running kubespray using `vagrant`. For repeated runs, you could save the script to a file in the root of the kubespray and run it by executing 'source <name_of_the_file>.

```
# use virtualenv to install all python requirements
VENVDIR=venv
virtualenv --python=/usr/bin/python3.7 $VENVDIR
source $VENVDIR/bin/activate
pip install -r requirements.txt

# prepare an inventory to test with
INV=inventory/my_lab
rm -rf ${INV}.bak &> /dev/null
mv ${INV} ${INV}.bak &> /dev/null
cp -a inventory/sample ${INV}
rm -f ${INV}/hosts.ini

# NOTE: When using the supplied Vagrant file, the next 2 commands would do nothing useful as vagrant generates its own inventory file. It is shown here simply to document and demonstrate that fact.
#declare -a IPS=(10.0.20.101 10.0.20.102 10.0.20.103)
#CONFIG_FILE=$INV/hosts python3 contrib/inventory_builder/inventory.py ${IPS[@]}

# set a few ansible vars, as an example
# NOTE1: open the the groupvars files in an editor to learn what variables can be set
# NOTE2: the vagrantfile can also vars, notably 'download_run_once', which may override the groupvar files
cat << EOF >> $INV/group_vars/all/all.yml
download_run_once: True
download_localhost: False
download_container: True
EOF

# this will create $INV/artifactes/admin.conf, which can the be used with kubectl
cat << EOF >> $INV/group_vars/k8s-cluster/k8s-cluster.yml
kubeconfig_localhost: True
EOF

# customize the vagrant environment
mkdir vagrant
cat << EOF > vagrant/config.rb
\$instance_name_prefix = "kub"
\$vm_cpus = 1
\$num_instances = 3
\$os = "centos-bento"
\$subnet = "10.0.20"
\$network_plugin = "flannel"
\$inventory = "$INV"
\$shared_folders = { 'temp/docker_rpms' => "/var/cache/yum/x86_64/7/docker-ce/packages" }
EOF

# make the rpm cache
mkdir -p temp/docker_rpms

vagrant up

# make a copy of the downloaded docker rpm, to speed up the next provisioning run
scp kub-1:/var/cache/yum/x86_64/7/docker-ce/packages/* temp/docker_rpms/

# copy kubectl access configuration in place
mkdir $HOME/.kube/ &> /dev/null
cp -f $INV/artifacts/admin.conf $HOME/.kube/config

# does it work?
kubectl get nodes
kubectl get ns
kubectl get po --all-namespaces -o wide
```
To play around a bit more the following commandlines may come in handy:

```
# generate a dashboard rbac token
kubectl create -f contrib/misc/dashboard-rbac.yml
kubectl -n kube-system describe secret kubernetes-dashboard-token | grep 'token:' | grep -o '[^ ]\+$'

# browse to the dashboard and use the rbac token that was generated a few lines back to log in
# https://10.0.20.101:6443/api/v1/namespaces/kube-system/services/https:kubernetes-dashboard:/proxy/#!/login

# Here is how you would re-run ansible, with extra verbose logging
ansible-playbook -vvv --become --ask-become-pass -i .vagrant/provisioners/ansible/inventory/vagrant_ansible_inventory cluster.yml
```

