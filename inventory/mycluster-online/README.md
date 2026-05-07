Use this inventory for overseas or direct-internet multi-node deployment.

This profile:
- keeps the multi-control-plane topology
- keeps `kube-vip` HA settings
- does not use the offline/private-registry overrides
- keeps the non-required add-ons disabled

Run with:

```bash
ansible-playbook -i inventory/mycluster-online/inventory.ini cluster.yml
```
