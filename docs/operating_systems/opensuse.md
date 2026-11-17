# openSUSE Leap 16.0, Tumbleweed, and MicroOS

The `ansible` package in the openSUSE Leap 16.0 repositories is older than the
version Kubespray requires. Install Ansible in a Python virtual environment as
described in [Installing Ansible](/docs/ansible/ansible.md#installing-ansible),
then continue with [Getting started](/docs/getting_started/getting-started.md).

## openSUSE MicroOS

Kubespray supports openSUSE MicroOS nodes with `containerd`. Docker and CRI-O
are not supported.

MicroOS uses a read-only root filesystem and transactional package updates.
Packages installed into a new snapshot become available only after a reboot.
When the bootstrap package transaction changes the system, Kubespray reboots
one node at a time and waits for it to become reachable before continuing.

Kubespray does not cordon or drain nodes for this bootstrap reboot. For an
existing cluster, schedule an appropriate maintenance window if new bootstrap
packages might be required. Transactional root filesystem snapshots do not
replace etcd snapshots or persistent volume backups.

Kubespray does not disable or coordinate the MicroOS
`transactional-update.timer` and `rebootmgr` services. Configure automatic
reboots according to your cluster maintenance and node-draining policy.
