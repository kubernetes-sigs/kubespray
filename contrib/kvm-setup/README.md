# Kargo on KVM Virtual Machines hypervisor preparation

A simple playbook to ensure your system has the right settings to enable Kargo
deployment on VMs.

This playbook does not create Virtual Machines, nor does it run Kargo itself.

### User creation

If you want to create a user for running Kargo deployment, you should specify
both `k8s_deployment_user` and `k8s_deployment_user_pkey_path`.
