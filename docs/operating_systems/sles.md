# SUSE Linux Enterprise Server (SLES)

Support for SLES 15 SP7 is experimental. There is no CI coverage, because SLES
images and repositories need a SUSE subscription. It was tested manually with
`containerd` and Calico. Other container managers were not tested.

## Subscription and repositories

Register each node with `SUSEConnect` before you run Kubespray. Kubespray
installs packages with `zypper`, but it does not manage subscriptions or
repositories.

## Python

SLES 15 SP7 ships Python 3.6 as `/usr/bin/python3`. That version is too old for
Ansible. Install Python 3.11 on each node:

```ShellSession
zypper install python311
```

The `python311` package comes from the Python 3 module. Enable that module with
`SUSEConnect` if the package is not found.

Then set the interpreter in your inventory:

```yaml
ansible_python_interpreter: /usr/bin/python3.11
```

## NTP

SLE 15 does not ship the `ntp` package, which is the Kubespray default for the
SUSE family. If you set `ntp_enabled: true`, also set:

```yaml
ntp_package: chrony
```
