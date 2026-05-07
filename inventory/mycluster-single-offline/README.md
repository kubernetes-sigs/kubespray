Offline single-node inventory for the "ultra-fast lane" deployment profile.

Use this inventory when you deploy a single-node offline/internal cluster with a local registry and DaoCloud files mirror:

```bash
ansible-playbook -i inventory/mycluster-single-offline/inventory.ini cluster.yml
```

Characteristics:
- single-node topology
- keeps kube-vip disabled
- uses `192.168.194.226:5000` as the image registry
- uses `https://files.m.daocloud.io` for binary downloads
- does not rely on `swr.cn-north-4.myhuaweicloud.com/ddn-k8s` at deploy time
- keeps optional components you already disabled turned off
