# Kubespray on KVM Virtual Machines hypervisor preparation

A simple playbook to ensure your system has the right settings to enable Kubespray
deployment on VMs.

This playbook does not create Virtual Machines, nor does it run Kubespray itself.

### User creation

If you want to create a user for running Kubespray deployment, you should specify
both `k8s_deployment_user` and `k8s_deployment_user_pkey_path`.
