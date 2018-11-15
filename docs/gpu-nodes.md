Nvidia GPU Nodes
===============

*Status: Experimental*

Requirements
---------------------------

Currently Ubuntu 16.04, Ubuntu 18.04 and Centos 7 are supported.

Before you can succesfully install gpu scheduling in Kubernetes you need to make sure
that the nouveau driver is disabled. There is a playbook `extra_playbooks/disable_nouveau.yml`
which will disable nouveau and reboot (when requested) your servers to make it permanent.
Do to this run `ansible-playbook -i <inventory> disable_nouveau.yaml (-e reboot_hosts=false/true)` if you don't
specify the var `reboot_hosts`, you will be asked.

Ofcourse you also need a set of Nvidia GPU cards. If you have multiple GPU models you should group.
them by node. For more information on GPU scheduling in kubernetes follow this [link](https://kubernetes.io/docs/tasks/manage-gpus/scheduling-gpus/)

Deployment
--------------------------

The driver installer requires the `overlay` storage system. In Centos this is default, in Ubuntu you should set in `all.yml`
```YAML
docker_storage_options: -s overlay2
```

In `k8s-cluster.yml` you should set the following:
```YAML
nvidia_accelerator_enabled: true
nvidia_gpu_nodes:
  - kube-gpu-001
  - kube-gpu-002
nvidia_gpu_flavor: gtx
```
After this you can configure other kubespray settings and run the `cluster.yml` playbook.

Test deployment
------------

Run the following pod to check your deployment

```YAML
apiVersion: v1
kind: Pod
metadata:
  name: gpu-pod
spec:
  tolerations:
      - key: "nvidia.com/gpu"
        effect: "NoSchedule"
        operator: "Exists"
  containers:
    - name: cuda-container
      image: nvidia/cuda
      command: ["/bin/sh"]
      args:
        - "-c"
        - for i in $(seq 1 1000); do sleep 20000 ; done
      resources:
        limits:
          nvidia.com/gpu: 1 # requesting 1 GPUs
```
then run `kubectl exec gpu-pod -- nvidia-smi`. This should show your GPU info. If you requests 2 or more cards you should also see
more gpu's with `nvidia-smi`.

Notes
------------
There is a `NoSchedule` setting on the nodes which contain GPU's. This will prevent non gpu pods to not be scheduled on a GPU node.
