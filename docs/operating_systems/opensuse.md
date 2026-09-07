# openSUSE Leap 15.6, Tumbleweed, and MicroOS

openSUSE Leap installation Notes:

- Install Ansible

  ```ShellSession
  sudo zypper ref
  sudo zypper -n install ansible

  ```

- Install Jinja2 and Python-Netaddr

  ```sudo zypper -n install python-Jinja2 python-netaddr```

Now you can continue with [Preparing your deployment](getting-started.md#starting-custom-deployment)

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
