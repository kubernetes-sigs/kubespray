CoreOS bootstrap
===============

Example with **kargo-cli**:

```
kargo deploy --gce --coreos
```

Or with Ansible:

Before running the cluster playbook you must satisfy the following requirements:

* On each CoreOS nodes a writable directory **/opt/bin** (~400M disk space)

Then you can proceed to [cluster deployment](#run-deployment)
