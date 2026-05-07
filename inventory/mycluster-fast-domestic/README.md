Domestic-accelerated 3-node inventory for the "ultra-fast lane" deployment profile.

Use this inventory when you deploy a 3-node cluster in mainland China using a local registry and DaoCloud file mirror for faster installs:

```bash
ansible-playbook -i inventory/mycluster-fast-domestic/inventory.ini cluster.yml
```

Characteristics:
- 3-node topology
- keeps kube-vip enabled
- uses `192.168.194.226:5000` as the image registry
- uses `https://files.m.daocloud.io` for binary downloads
- reduces reliance on overseas/downstream mirrors at deploy time
- keeps optional components you already disabled turned off
