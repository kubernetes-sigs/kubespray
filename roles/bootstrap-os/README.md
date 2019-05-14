# bootstrap-os

Bootstrap an Ansible host to be able to run Ansible modules.

This role will:
  * configure the package manager (if applicable) to be able to fetch packages
  * install Python
  * install the necessary packages to use Ansible's package manager modules
  * set the hostname of the host to `{{ inventory_hostname }}` when requested

## Requirements

A host running an operating system that is supported by Kubespray.
See https://github.com/kubernetes-sigs/kubespray#supported-linux-distributions for a current list.

SSH access to the host.

## Role Variables

Variables are listed with their default values, if applicable.

### General variables

  * `http_proxy`/`https_proxy`
    The role will configure the package manager (if applicable) to download packages via a proxy.

  * `override_system_hostname: true`
    The role will set the hostname of the machine to the name it has according to Ansible's inventory (the variable `{{ inventory_hostname }}`).

### Per distribution variables

#### CoreOS

* `coreos_locksmithd_disable: false`
  Whether `locksmithd` (responsible for rolling restarts) should be disabled or be left alone.

* `coreos_pypy_folder: "pypy3.5-{{ coreos_pypy_version }}-linux_x86_64-portable"`
  Name of the folder inside the tar.bz2 downloaded.

* `coreos_pypy_download_url: "https://bitbucket.org/squeaky/portable-pypy/downloads/{{ coreos_pypy_folder }}.tar.bz2"`
  URL for the portable pypy tar.bz2 archive, specially useful for offline installations.

* `coreos_pypy_version: "7.0.0"`
  Version of the portable pypy3.5 package to download if using the default settings for the `coreos_pypy_*` variables.

#### CentOS/RHEL

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
