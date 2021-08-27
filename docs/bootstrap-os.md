# bootstrap-os

Bootstrap an Ansible host to be able to run Ansible modules.

This role will:

* configure the package manager (if applicable) to be able to fetch packages
* install Python
* install the necessary packages to use Ansible's package manager modules
* set the hostname of the host to `{{ inventory_hostname }}` when requested

## Requirements

A host running an operating system that is supported by Kubespray.
See [Supported Linux Distributions](https://github.com/kubernetes-sigs/kubespray#supported-linux-distributions) for a current list.

SSH access to the host.

## Role Variables

Variables are listed with their default values, if applicable.

### General variables

* `http_proxy`/`https_proxy`
  The role will configure the package manager (if applicable) to download packages via a proxy.

* `override_system_hostname: true`
  The role will set the hostname of the machine to the name it has according to Ansible's inventory (the variable `{{ inventory_hostname }}`).

### Per distribution variables

#### Flatcar Container Linux

* `coreos_locksmithd_disable: false`
  Whether `locksmithd` (responsible for rolling restarts) should be disabled or be left alone.

#### CentOS/RHEL/AlmaLinux

* `centos_fastestmirror_enabled: false`
  Whether the [fastestmirror](https://wiki.centos.org/PackageManagement/Yum/FastestMirror) yum plugin should be enabled.

## Dependencies

The `kubespray-defaults` role is expected to be run before this role.

## Example Playbook

Remember to disable fact gathering since Python might not be present on hosts.

    - hosts: all
      gather_facts: false  # not all hosts might be able to run modules yet
      roles:
         - kubespray-defaults
         - bootstrap-os

## License

Apache 2.0
