Role Name
=========

This role is intended to be used to fetch and deploy Helm Charts as part of
cluster installation or upgrading with kubespray.

Requirements
------------

The role needs to be executed on a host with access to the Kubernetes API, and
with the helm binary in place.

Role Variables
--------------

See meta/argument_specs.yml

Playbook example:

```yaml
---
- hosts: kube_control_plane[0]
  gather_facts: no
  vars:
    helm_apps:
      - release_name: app
        release_namespace: app
        chart_ref: simple-app/simple-app
    repos:
      - repo_name: simple-app
        repo_url: "https://blog.leiwang.info/simple-app"
    helm_params:
      wait_timeout: "5m"
  roles:
    - name: helm-apps
      charts: "{{ helm_apps }}"
      repositories: "{{ repos }}"
      charts_common_opts: "{{ helm_params }}"
```
