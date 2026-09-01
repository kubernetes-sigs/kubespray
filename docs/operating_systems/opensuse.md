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
During bootstrap, Kubespray installs required system packages into a new
snapshot and reboots the node when the package transaction changes the system.
Ensure nodes can reboot and become reachable through SSH before starting the
deployment.

Kubespray does not disable or coordinate the MicroOS
`transactional-update.timer` and `rebootmgr` services. Configure automatic
reboots according to your cluster maintenance and node-draining policy.
