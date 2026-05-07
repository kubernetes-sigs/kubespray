Use this inventory for a single-node cluster:

```bash
ansible-playbook -i inventory/mycluster-single/inventory.ini cluster.yml
```

Use the existing HA inventory for the multi-node cluster:

```bash
ansible-playbook -i inventory/mycluster/inventory.ini cluster.yml
```

Single-node profile changes:
- one host only: `master1`
- `kube-vip` disabled
- no external API VIP
- no HA ARP tuning
