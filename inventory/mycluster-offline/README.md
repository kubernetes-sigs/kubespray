Offline 3-node inventory for the "ultra-fast lane" deployment profile.

Use this inventory when you deploy a 3-node offline/internal cluster with a local registry and DaoCloud files mirror:

```bash
ansible-playbook -i inventory/mycluster-offline/inventory.ini cluster.yml
```

Characteristics:
- 3-node topology
- keeps kube-vip enabled
- uses `192.168.194.226:5000` as the image registry
- uses `https://files.m.daocloud.io` for binary downloads
- does not rely on `swr.cn-north-4.myhuaweicloud.com/ddn-k8s` at deploy time
- keeps optional components you already disabled turned off
