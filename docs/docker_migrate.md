# Migrate container runtime from docker to containerd

You can change container runtime from docker to containerd on your existing cluster:

## Known limitations:

- support change only from docker to containerd
- etcd should run in mode: `etcd_deployment_type=host` or `etcd_kubeadm_enabled=true`
- download mode "pull once, push many" not supported, so set `download_run_once=false`
- you shoul launch playbook `upgrade-cluster.yml` to change container runtime
- pre-download container images not support during upgrade

## Change etcd deployment type

If your cluster run with `etcd_deployment_type=docker`, you can change it to mode host.

1. Set `etcd_deployment_type=host` in inventory
2. Start playbook cluster.yml
3. Shell to control plane nodes and do on it:
  - `docker stop $(docker ps --format '{{.Names}}' | grep etcd)`
  - `systemctl stop etcd`
  - `systemctl start etcd`
  - `/usr/local/bin/etcdctl.sh endpoint status --cluster`

## Change container runtime

1. Set `container_runtime=containerd` in inventory
2. Start playbook upgrade-cluster.yml
