Flatcar Container Linux bootstrap
===============

Example with Ansible:

Before running the cluster playbook you must satisfy the following requirements:

General Flatcar Pre-Installation Notes:

- Ensure that the bin_dir is set to `/opt/bin`
- ansible_python_interpreter should be `/opt/bin/python`. This will be laid down by the bootstrap task.
- The resolvconf_mode setting of `docker_dns` **does not** work for Flatcar. This is because we do not edit the systemd service file for docker on Flatcar nodes. Instead, just use the default `host_resolvconf` mode. It should work out of the box.

Then you can proceed to [cluster deployment](#run-deployment)
