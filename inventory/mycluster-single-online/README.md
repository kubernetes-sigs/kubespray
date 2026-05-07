Use this inventory for overseas or direct-internet single-node deployment.

This profile:
- keeps the single-node topology
- disables `kube-vip`
- does not use the offline/private-registry overrides
- keeps the non-required add-ons disabled

Run with:

```bash
ansible-playbook -i inventory/mycluster-single-online/inventory.ini cluster.yml
```
