# Vagrant

Assuming you have Vagrant 2.0+ installed with virtualbox, libvirt/qemu or vmware, but is untested) you should be able to launch a 3 node Kubernetes cluster by simply running `vagrant up`. This will spin up 3 VMs and install kubernetes on them.  Once they are completed you can connect to any of them by running `vagrant ssh k8s-[1..3]`.

To give an estimate of the expected duration of a provisioning run: On a dual core i5-6300u laptop with an SSD, provisioning takes around 13 to 15 minutes, once the container images and other files are cached. Note that libvirt/qemu is recommended over virtualbox as it is quite a bit faster, especially during boot-up time.

For proper performance a minimum of 12GB RAM is recommended. It is possible to run a 3 node cluster on a laptop with 8GB of RAM using the default Vagrantfile, provided you have 8GB zram swap configured and not much more than a browser and a mail client running. If you decide to run on such a machine, then also make sure that any tmpfs devices, that are mounted, are mostly empty and disable any swapfiles mounted on HDD/SSD or you will be in for some serious swap-madness. Things can get a bit sluggish during provisioning, but when that's done, the system will actually be able to perform quite well.

## Customize Vagrant

You can override the default settings in the `Vagrantfile` either by directly modifying the `Vagrantfile` or through an override file. In the same directory as the `Vagrantfile`, create a folder called `vagrant` and create `config.rb` file in it. An example of how to configure this file is given below.

## Use alternative OS for Vagrant

By default, Vagrant uses Ubuntu 18.04 box to provision a local cluster. You may use an alternative supported operating system for your local cluster.

Customize `$os` variable in `Vagrantfile` or as override, e.g.,:

```ShellSession
echo '$os = "coreos-stable"' >> vagrant/config.rb
```

The supported operating systems for vagrant are defined in the `SUPPORTED_OS` constant in the `Vagrantfile`.

## File and image caching

Kubespray can take quite a while to start on a laptop. To improve provisioning speed, the variable 'download_run_once' is set. This will make kubespray download all files and containers just once and then redistributes them to the other nodes and as a bonus, also cache all downloads locally and re-use them on the next provisioning run. For more information on download settings see [download documentation](/docs/downloads.md).

## Example use of Vagrant

The following is an example of setting up and running kubespray using `vagrant`. For repeated runs, you could save the script to a file in the root of the kubespray and run it by executing 'source <name_of_the_file>.

```ShellSession
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
ln -s $INV/artifacts/admin.conf $HOME/.kube/config
# make the kubectl binary available
sudo ln -s $INV/artifacts/kubectl /usr/local/bin/kubectl
#or
export PATH=$PATH:$INV/artifacts
```

If a vagrant run failed and you've made some changes to fix the issue causing the fail, here is how you would re-run ansible:

```ShellSession
ansible-playbook -vvv -i .vagrant/provisioners/ansible/inventory/vagrant_ansible_inventory cluster.yml
```

If all went well, you check if it's all working as expected:

```ShellSession
kubectl get nodes
```

The output should look like this:

```ShellSession
$ kubectl get nodes
NAME    STATUS   ROLES    AGE   VERSION
kub-1   Ready    master   32m   v1.14.1
kub-2   Ready    master   31m   v1.14.1
kub-3   Ready    <none>   31m   v1.14.1
```

Another nice test is the following:

```ShellSession
kubectl get po --all-namespaces -o wide
```

Which should yield something like the following:

```ShellSession
NAMESPACE     NAME                                    READY   STATUS    RESTARTS   AGE   IP            NODE     NOMINATED NODE   READINESS GATES
kube-system   coredns-97c4b444f-9wm86                 1/1     Running   0          31m   10.233.66.2   kub-3    <none>           <none>
kube-system   coredns-97c4b444f-g7hqx                 0/1     Pending   0          30m   <none>        <none>   <none>           <none>
kube-system   dns-autoscaler-5fc5fdbf6-5c48k          1/1     Running   0          31m   10.233.66.3   kub-3    <none>           <none>
kube-system   kube-apiserver-kub-1                    1/1     Running   0          32m   10.0.20.101   kub-1    <none>           <none>
kube-system   kube-apiserver-kub-2                    1/1     Running   0          32m   10.0.20.102   kub-2    <none>           <none>
kube-system   kube-controller-manager-kub-1           1/1     Running   0          32m   10.0.20.101   kub-1    <none>           <none>
kube-system   kube-controller-manager-kub-2           1/1     Running   0          32m   10.0.20.102   kub-2    <none>           <none>
kube-system   kube-flannel-8tgcn                      2/2     Running   0          31m   10.0.20.103   kub-3    <none>           <none>
kube-system   kube-flannel-b2hgt                      2/2     Running   0          31m   10.0.20.101   kub-1    <none>           <none>
kube-system   kube-flannel-zx4bc                      2/2     Running   0          31m   10.0.20.102   kub-2    <none>           <none>
kube-system   kube-proxy-4bjdn                        1/1     Running   0          31m   10.0.20.102   kub-2    <none>           <none>
kube-system   kube-proxy-l5tt5                        1/1     Running   0          31m   10.0.20.103   kub-3    <none>           <none>
kube-system   kube-proxy-x59q8                        1/1     Running   0          31m   10.0.20.101   kub-1    <none>           <none>
kube-system   kube-scheduler-kub-1                    1/1     Running   0          32m   10.0.20.101   kub-1    <none>           <none>
kube-system   kube-scheduler-kub-2                    1/1     Running   0          32m   10.0.20.102   kub-2    <none>           <none>
kube-system   kubernetes-dashboard-6c7466966c-jqz42   1/1     Running   0          31m   10.233.66.4   kub-3    <none>           <none>
kube-system   nginx-proxy-kub-3                       1/1     Running   0          32m   10.0.20.103   kub-3    <none>           <none>
kube-system   nodelocaldns-2x7vh                      1/1     Running   0          31m   10.0.20.102   kub-2    <none>           <none>
kube-system   nodelocaldns-fpvnz                      1/1     Running   0          31m   10.0.20.103   kub-3    <none>           <none>
kube-system   nodelocaldns-h2f42                      1/1     Running   0          31m   10.0.20.101   kub-1    <none>           <none>
```

Create clusteradmin rbac and get the login token for the dashboard:

```ShellSession
kubectl create -f contrib/misc/clusteradmin-rbac.yml
kubectl -n kube-system describe secret kubernetes-dashboard-token | grep 'token:' | grep -o '[^ ]\+$'
```

Copy it to the clipboard and now log in to the [dashboard](https://10.0.20.101:6443/api/v1/namespaces/kube-system/services/https:kubernetes-dashboard:/proxy/#!/login).
