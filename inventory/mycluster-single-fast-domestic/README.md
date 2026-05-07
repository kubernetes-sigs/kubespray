Domestic-accelerated single-node inventory for the "ultra-fast lane" deployment profile.

Use this inventory when you deploy a single-node cluster in mainland China using a local registry and DaoCloud file mirror for faster installs:

```bash
ansible-playbook -i inventory/mycluster-single-fast-domestic/inventory.ini cluster.yml
```

Characteristics:
- single-node topology
- keeps kube-vip disabled
- uses `192.168.194.226:5000` as the image registry
- uses `https://files.m.daocloud.io` for binary downloads
- reduces reliance on overseas/downstream mirrors at deploy time
- keeps optional components you already disabled turned off
