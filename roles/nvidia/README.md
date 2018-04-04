# Ansible Nvidia Role

Installs nvidia drivers on a linux CLI system. It installs drivers without installing any X components

### Usage

```
---
- hosts: nvidia-gpu
  roles:
    - { role: nvidia , nvidia_driver_version: "384.111" }
```

### Compatiblity
Tested: Ubuntu 16.04

Should work with:
* ubuntu
* debian
* redhat/centos
* fedora
