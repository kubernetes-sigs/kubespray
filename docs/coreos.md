CoreOS bootstrap
===============

Example with Ansible:

Before running the cluster playbook you must satisfy the following requirements:

General CoreOS Pre-Installation Notes:

- Ensure that the bin_dir is set to `/opt/bin`
- ansible_python_interpreter should be `/opt/bin/python`. This will be laid down by the bootstrap task.
- The default resolvconf_mode setting of `docker_dns` **does not** work for CoreOS. This is because we do not edit the systemd service file for docker on CoreOS nodes. Instead, just use the `host_resolvconf` mode. It should work out of the box.

Then you can proceed to [cluster deployment](#run-deployment)
