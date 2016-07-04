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
