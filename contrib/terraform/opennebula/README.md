# Kubernetes on OpenNebula with Terraform

Provision a Kubespray-ready cluster on OpenNebula 7.2+: Terraform creates the
VMs from an existing contextualized template and generates the Ansible
inventory, then the standard Kubespray playbook deploys Kubernetes.

## Requirements

- OpenNebula >= 7.2 with the XML-RPC endpoint reachable from this machine
- An existing VM template with the [one-context](https://github.com/OpenNebula/one-apps)
  package installed (all OpenNebula marketplace OS appliances qualify) (for
  the contextualization requirement — see the disk-options note below for a
  separate template constraint). The template's network context must be
  enabled (`NETWORK = "YES"` is set by this module).
- An existing Virtual Network whose addresses are reachable from the machine
  running Terraform and Ansible
- Terraform >= 1.3 or OpenTofu (provider `OpenNebula/opennebula ~> 1.5` — the
  release line adapted to the OpenNebula 7.x API)
- The VM template should NOT define its own NIC — the module attaches the
  network explicitly, and a template NIC would leave nodes dual-homed with
  the default route on the wrong interface.
- To use any disk option (`master_disk_size`/`worker_disk_size`/`additional_disk_size`)
  the template's first disk must reference its image by numeric `IMAGE_ID` —
  templates created via Sunstone wizards or the CLI often reference the image
  by name (`IMAGE=`), which the provider cannot read; the module fails at
  plan time with a clear error in that case.

## Quickstart

```ShellSession
$ cd kubespray
$ cp -LRp contrib/terraform/opennebula/sample-inventory inventory/mycluster
$ cd inventory/mycluster
$ $EDITOR cluster.tfvars                  # template_name, network_name, master/worker_count, ssh_public_keys
$ export OPENNEBULA_ENDPOINT="https://one.example.com:2634/RPC2"
$ export OPENNEBULA_USERNAME="oneadmin"
$ export OPENNEBULA_PASSWORD="opennebula"
$ terraform -chdir=../../contrib/terraform/opennebula init
$ terraform -chdir=../../contrib/terraform/opennebula apply \
    -var-file=$PWD/cluster.tfvars \
    -var inventory_file=$PWD/inventory.ini
```

**Pass `-var inventory_file=$PWD/inventory.ini` on every subsequent `apply`
as well** — without it the variable falls back to a path relative to the
module directory and the previously rendered inventory file is removed.

After `apply`, the VMs are RUNNING in OpenNebula and `inventory.ini` contains
all Kubespray groups. Kubespray pins its Ansible version — install it in a
virtualenv from the repo root before deploying:

```ShellSession
$ python3 -m venv ~/.venvs/kubespray && source ~/.venvs/kubespray/bin/activate && \
    pip install -r requirements.txt
```

Deploy Kubernetes:

```ShellSession
$ cd ../.. && \
    ansible-playbook -i inventory/mycluster/inventory.ini cluster.yml -b
```

Smoke-test checklist: VMs visible and RUNNING in Sunstone; `inventory.ini`
written next to your `cluster.tfvars`; `ansible -i inventory/mycluster/inventory.ini -m ping all`
succeeds (one-context may need a few seconds after RUNNING before SSH is up).

To tear the cluster down: `terraform -chdir=contrib/terraform/opennebula destroy
-var-file=$PWD/inventory/mycluster/cluster.tfvars` (run from the repo root;
this also deletes the rendered `inventory.ini`).

The Terraform state lives in `contrib/terraform/opennebula/` — manage one
cluster per checkout, or use `terraform workspace` for more.

## Variables

### Required

- `template_name`: name of the existing contextualized OpenNebula VM template
- `network_name`: name of the existing Virtual Network for the nodes
- `master_count` / `worker_count`: how many control-plane and worker nodes to
  create (named `master-0..`, `worker-0..`; at least one master required) —
  the simple way to define the cluster
- `machines`: advanced alternative to the counts (takes precedence when set);
  map of machines, key = machine name (VM/hostname becomes `<prefix>-<key>`)
  - `node_type`: `master` or `worker` (at least one master required)
  - `ip`: optional static IP inside an address range of the network; empty
    string lets OpenNebula assign a lease. When `network_reservation_size > 0`
    the static IP must fall inside the **reservation's** address range, not
    just the parent network's
- `ssh_public_keys`: list of SSH public keys injected into the VMs via
  contextualization

### Connection

Set `OPENNEBULA_ENDPOINT`, `OPENNEBULA_USERNAME`, `OPENNEBULA_PASSWORD`
(and optionally `OPENNEBULA_INSECURE=true`) in the environment, or the
`one_endpoint` / `one_username` / `one_password` / `one_insecure` variables
(e.g. `one_endpoint = "https://one.example.com:2634/RPC2"`).
OpenNebula XML-RPC sends the username:password with every request — use a
TLS endpoint in production (`http://…:2633` is the plaintext out-of-the-box
default).

### Optional

- `prefix` (default `k8s`): VM name prefix — must be unique per OpenNebula
  user when the extras are enabled (the extra-disk image, VM group and
  reservation are named `<prefix>-...` and OpenNebula rejects duplicate
  names)
- `ansible_user` (default `root`): SSH user written into the inventory
- `inventory_file` (default `inventory.ini`): where the inventory is
  rendered — relative paths resolve against `contrib/terraform/opennebula/`
  because of `-chdir`; prefer an absolute path (e.g. set it in your
  `cluster.tfvars`)
- `master_cpu`/`master_vcpu`/`master_memory` (1 / 2 / 4096 MB)
- `worker_cpu`/`worker_vcpu`/`worker_memory` (1 / 4 / 8192 MB)
- `master_disk_size`/`worker_disk_size` (MB, default 0 = keep the template's
  disk; grow-only and create-time — raising it later does NOT grow an
  existing cluster's root disks). Any disk option drops the template's
  secondary disks (only the first disk is re-declared).
- `vm_create_timeout` (default `20m`)
- `additional_disk_size` (MB, default 0): extra non-persistent DATABLOCK disk
  cloned per node (requires `image_datastore_name`) — strictly create-time in
  BOTH directions: enabling it on an existing cluster silently hot-attaches
  the re-declared OS disk as a duplicate OS-image clone on every node (apply
  succeeds, wrong result), resizing it later fails against the in-use image,
  and disabling it can attempt to detach the boot disk. Decide disk options
  at cluster creation; changing them means recreating the VMs. The module
  automatically re-declares the template's first disk alongside the extra
  disk (preserving the template's `SIZE=` override; `TARGET`/`DRIVER` fall
  back to image defaults); templates with more than one disk lose their
  secondary disks whenever any disk option is used.
- `masters_anti_affinity` (default `false`): spread masters across hosts with
  an `ANTI_AFFINED` VM group; requires at least as many hosts as masters — on
  fewer hosts the VM stays pending until `vm_create_timeout` — changing this
  on an existing cluster replaces every master VM.
- `network_reservation_size` (default 0): carve an address reservation of
  this size out of `network_name` and attach the nodes to it — create-time
  only (the provider cannot grow a reservation in place); use
  `network_reservation_first_ip`/`network_reservation_ar_id` to pin the
  reserved range so static `machines` IPs can target it. Toggling the
  reservation on/off (0↔N) on an existing cluster re-attaches every node's
  NIC on the other network and re-leases all IPs — it will break a deployed
  cluster; treat it as a create-time choice. The reservation must be at
  least as large as the number of nodes (enforced at plan time). Leaving
  `network_reservation_first_ip`/`network_reservation_ar_id` unpinned causes
  a harmless perpetual in-place diff on `plan` (the provider reads back the
  allocated values) — pin both to avoid it.
- `network_reservation_first_ip` (default `""`): first IP of the reservation
  carved from the parent network (empty = let OpenNebula choose)
- `network_reservation_ar_id` (default `null`): address-range ID of the
  parent network to reserve from (null = provider default)

## Troubleshooting

- **CoreDNS / nodelocaldns in CrashLoopBackOff after deploy** (validated on
  Ubuntu 24.04 marketplace images): the nodes' `/etc/resolv.conf` points at
  the systemd-resolved stub (`127.0.0.53`), which CoreDNS detects as a
  forwarding loop — or the OpenNebula VNet defines no `DNS` attribute at all.
  Fix: set `upstream_dns_servers` (e.g. `[8.8.8.8, 1.1.1.1]` or your internal
  resolver) in `inventory/$CLUSTER/group_vars/all/all.yml` and re-run
  `cluster.yml`. Infrastructure-level alternative: set the `DNS` attribute on
  the OpenNebula Virtual Network so contextualized guests get a real resolver.
- **A failed first run can leave the cluster half-installed**: if
  `cluster.yml` dies before the network plugin is deployed, a re-run may wait
  forever on "control plane nodes to be Ready" (the nodes stay NotReady
  without a CNI). Recreate the VMs (`terraform destroy` + `apply`) and deploy
  again on clean machines.
- **Transient `Service is in unknown state` handler failures** during heavy
  image-pull phases are usually a one-off systemd/dbus hiccup — re-running
  `cluster.yml` is safe and idempotent.

## Known issues

- Deleting VMs/images/networks manually in OpenNebula breaks `terraform
  refresh`/`plan` with `NO_EXISTS` ([provider #623](https://github.com/OpenNebula/terraform-provider-opennebula/issues/623));
  workaround: `terraform state rm <resource>`.
- Overriding the template disk (any disk option: `*_disk_size > 0` or
  `additional_disk_size > 0`) can produce perpetual
  in-place updates in `plan` with some template layouts
  ([provider #598](https://github.com/OpenNebula/terraform-provider-opennebula/issues/598)).
- A network reservation supports a single address range
  ([provider #625](https://github.com/OpenNebula/terraform-provider-opennebula/issues/625)).
- IPv4 only: IPv6 read-back from templates is broken in provider 1.5.0
  ([provider #615](https://github.com/OpenNebula/terraform-provider-opennebula/issues/615)).
- Provider CI upstream covers OpenNebula 6.10/7.0; 7.2 keeps XML-RPC
  compatibility and has no known provider issues.
