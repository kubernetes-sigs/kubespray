Getting started
===============

The easiest way to run the deployement is to use the **kargo-cli** tool. 
A complete documentation can be found in its [github repository](https://github.com/kubespray/kargo-cli).

Here is a simple example on AWS: 

* Create instances and generate the inventory

```
kargo aws --instances 3
```

* Run the deployment 

```
kargo deploy --aws -u centos -n calico
```

Building your own inventory
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Ansible inventory can be stored in 3 formats: YAML, JSON, or inifile. There is
an example inventory located
[here](https://github.com/kubernetes-incubator/kargo/blob/master/inventory/inventory.example).

You can use an
[inventory generator](https://github.com/kubernetes-incubator/kargo/blob/master/contrib/inventory_generator/inventory_generator.py)
to create or modify an Ansible inventory. Currently, it is limited in
functionality and is only use for making a basic Kargo cluster, but it does
support creating large clusters.
